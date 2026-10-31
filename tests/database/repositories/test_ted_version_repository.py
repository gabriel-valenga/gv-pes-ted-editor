
import hashlib
import sqlite3

import pytest

from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.ted_file_repository import create_ted_file
from database.repositories.ted_version_repository import (
    create_ted_version,
    get_ted_version,
    list_ted_versions,
    get_latest_ted_version,
    get_ted_version_content,
)


@pytest.fixture
def connection(tmp_path):
    """Create a temporary database with the latest schema."""
    database_path = tmp_path / "test.db"

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    migrate_database(connection)

    yield connection

    connection.close()


@pytest.fixture
def ted_file_id(connection):
    """Create a TED file for version tests."""
    option_file_id = create_option_file(
        connection,
        "Test Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    return create_ted_file(
        connection,
        import_id=import_id,
        file_name="team.ted",
    )


@pytest.fixture
def original_content():
    """Return sample encrypted TED content."""
    return b"\x00\x01\x02\x03\x04\x05\xFF"


def test_create_ted_version(
    connection,
    ted_file_id,
    original_content,
):
    version_id = create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    version = get_ted_version(
        connection,
        version_id,
    )

    assert version is not None
    assert version["ted_file_id"] == ted_file_id
    assert version["version_number"] == 1
    assert version["version_type"] == "original"
    assert version["content"] == original_content
    assert version["sha256"] == hashlib.sha256(
        original_content
    ).hexdigest()
    assert version["created_at"] is not None


def test_create_ted_version_with_empty_content(
    connection,
    ted_file_id,
):
    version_id = create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=b"",
    )

    version = get_ted_version(
        connection,
        version_id,
    )

    assert version is not None
    assert version["content"] == b""
    assert version["sha256"] == hashlib.sha256(b"").hexdigest()


def test_create_ted_version_rejects_non_bytes_content(
    connection,
    ted_file_id,
):
    with pytest.raises(TypeError):
        create_ted_version(
            connection,
            ted_file_id=ted_file_id,
            version_number=1,
            version_type="original",
            content="not binary",
        )


def test_create_ted_version_with_invalid_type(
    connection,
    ted_file_id,
    original_content,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_ted_version(
            connection,
            ted_file_id=ted_file_id,
            version_number=1,
            version_type="invalid",
            content=original_content,
        )


def test_create_ted_version_with_invalid_ted_file_id(
    connection,
    original_content,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_ted_version(
            connection,
            ted_file_id=999999,
            version_number=1,
            version_type="original",
            content=original_content,
        )


def test_create_duplicate_version_number(
    connection,
    ted_file_id,
    original_content,
):
    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    with pytest.raises(sqlite3.IntegrityError):
        create_ted_version(
            connection,
            ted_file_id=ted_file_id,
            version_number=1,
            version_type="edited",
            content=b"edited content",
        )


def test_create_multiple_original_versions(
    connection,
    ted_file_id,
    original_content,
):
    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    with pytest.raises(sqlite3.IntegrityError):
        create_ted_version(
            connection,
            ted_file_id=ted_file_id,
            version_number=2,
            version_type="original",
            content=b"another original",
        )


def test_same_version_number_in_different_ted_files(
    connection,
    ted_file_id,
    original_content,
):
    option_file_id = create_option_file(
        connection,
        "Another Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    another_ted_file_id = create_ted_file(
        connection,
        import_id=import_id,
        file_name="another_team.ted",
    )

    first_version_id = create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    second_version_id = create_ted_version(
        connection,
        ted_file_id=another_ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    assert first_version_id != second_version_id


def test_get_ted_version_not_found(connection):
    version = get_ted_version(
        connection,
        999,
    )

    assert version is None


def test_list_ted_versions(connection, ted_file_id):
    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=3,
        version_type="restored",
        content=b"version 3",
    )

    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=b"version 1",
    )

    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=2,
        version_type="edited",
        content=b"version 2",
    )

    versions = list_ted_versions(
        connection,
        ted_file_id,
    )

    assert len(versions) == 3
    assert [
        version["version_number"]
        for version in versions
    ] == [1, 2, 3]

    assert "content" not in versions[0].keys()


def test_list_ted_versions_empty(connection, ted_file_id):
    versions = list_ted_versions(
        connection,
        ted_file_id,
    )

    assert versions == []


def test_list_ted_versions_only_from_requested_ted(
    connection,
    ted_file_id,
):
    option_file_id = create_option_file(
        connection,
        "Another Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    another_ted_file_id = create_ted_file(
        connection,
        import_id=import_id,
        file_name="another_team.ted",
    )

    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=b"first",
    )

    create_ted_version(
        connection,
        ted_file_id=another_ted_file_id,
        version_number=1,
        version_type="original",
        content=b"second",
    )

    versions = list_ted_versions(
        connection,
        ted_file_id,
    )

    assert len(versions) == 1
    assert versions[0]["ted_file_id"] == ted_file_id


def test_get_latest_ted_version(connection, ted_file_id):
    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=b"original",
    )

    create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=2,
        version_type="edited",
        content=b"edited",
    )

    latest_version = get_latest_ted_version(
        connection,
        ted_file_id,
    )

    assert latest_version is not None
    assert latest_version["version_number"] == 2
    assert latest_version["version_type"] == "edited"
    assert "content" not in latest_version.keys()


def test_get_latest_ted_version_empty(connection, ted_file_id):
    latest_version = get_latest_ted_version(
        connection,
        ted_file_id,
    )

    assert latest_version is None


def test_get_ted_version_content(
    connection,
    ted_file_id,
    original_content,
):
    version_id = create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=original_content,
    )

    content = get_ted_version_content(
        connection,
        version_id,
    )

    assert content == original_content


def test_get_ted_version_content_not_found(connection):
    content = get_ted_version_content(
        connection,
        999,
    )

    assert content is None
