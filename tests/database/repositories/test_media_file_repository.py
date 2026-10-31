
import hashlib
import sqlite3

import pytest

from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.ted_file_repository import create_ted_file
from database.repositories.media_file_repository import (
    create_media_file,
    get_media_file,
    list_media_files,
    delete_media_file,
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
    """Create a TED file for media tests."""
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
def media_content():
    """Return sample binary content."""
    return b"\x00\x01\x02\x03\x04\x05\xFF"


def test_create_media_file(
    connection,
    ted_file_id,
    media_content,
):
    media_file_id = create_media_file(
        connection,
        file_name="player_face.bin",
        media_type="image",
        content=media_content,
        ted_file_id=ted_file_id,
        purpose="player_face",
    )

    media_file = get_media_file(
        connection,
        media_file_id,
    )

    assert media_file is not None
    assert media_file["ted_file_id"] == ted_file_id
    assert media_file["file_name"] == "player_face.bin"
    assert media_file["media_type"] == "image"
    assert media_file["purpose"] == "player_face"
    assert media_file["content"] == media_content
    assert media_file["sha256"] == hashlib.sha256(
        media_content
    ).hexdigest()
    assert media_file["created_at"] is not None


def test_create_media_file_without_optional_fields(
    connection,
    media_content,
):
    media_file_id = create_media_file(
        connection,
        file_name="generic.bin",
        media_type="binary",
        content=media_content,
    )

    media_file = get_media_file(
        connection,
        media_file_id,
    )

    assert media_file is not None
    assert media_file["ted_file_id"] is None
    assert media_file["purpose"] is None


def test_create_media_file_with_empty_content(connection):
    media_file_id = create_media_file(
        connection,
        file_name="empty.bin",
        media_type="binary",
        content=b"",
    )

    media_file = get_media_file(
        connection,
        media_file_id,
    )

    assert media_file is not None
    assert media_file["content"] == b""
    assert media_file["sha256"] == hashlib.sha256(b"").hexdigest()


def test_create_media_file_rejects_non_bytes_content(connection):
    with pytest.raises(TypeError):
        create_media_file(
            connection,
            file_name="invalid.bin",
            media_type="binary",
            content="not binary",
        )


def test_create_media_file_with_invalid_ted_file_id(
    connection,
    media_content,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_media_file(
            connection,
            file_name="invalid.bin",
            media_type="binary",
            content=media_content,
            ted_file_id=999999,
        )


def test_get_media_file_not_found(connection):
    media_file = get_media_file(
        connection,
        999,
    )

    assert media_file is None


def test_list_media_files(connection, media_content):
    create_media_file(
        connection,
        file_name="second.bin",
        media_type="binary",
        content=media_content,
    )

    create_media_file(
        connection,
        file_name="first.bin",
        media_type="image",
        content=media_content,
    )

    media_files = list_media_files(connection)

    assert len(media_files) == 2
    assert [item["file_name"] for item in media_files] == [
        "first.bin",
        "second.bin",
    ]

    assert "content" not in media_files[0].keys()


def test_list_media_files_empty(connection):
    media_files = list_media_files(connection)

    assert media_files == []


def test_list_media_files_by_ted_file_id(
    connection,
    ted_file_id,
    media_content,
):
    another_ted_file_id = create_ted_file(
        connection,
        import_id=connection.execute(
            "SELECT import_id FROM ted_files WHERE id = ?",
            (ted_file_id,),
        ).fetchone()["import_id"],
        file_name="another_team.ted",
    )

    create_media_file(
        connection,
        file_name="first.bin",
        media_type="binary",
        content=media_content,
        ted_file_id=ted_file_id,
    )

    create_media_file(
        connection,
        file_name="second.bin",
        media_type="binary",
        content=media_content,
        ted_file_id=another_ted_file_id,
    )

    media_files = list_media_files(
        connection,
        ted_file_id=ted_file_id,
    )

    assert len(media_files) == 1
    assert media_files[0]["file_name"] == "first.bin"


def test_list_media_files_by_purpose(connection, media_content):
    create_media_file(
        connection,
        file_name="face.bin",
        media_type="image",
        content=media_content,
        purpose="player_face",
    )

    create_media_file(
        connection,
        file_name="badge.bin",
        media_type="image",
        content=media_content,
        purpose="team_badge",
    )

    media_files = list_media_files(
        connection,
        purpose="player_face",
    )

    assert len(media_files) == 1
    assert media_files[0]["file_name"] == "face.bin"


def test_list_media_files_by_sha256(connection):
    first_content = b"first media"
    second_content = b"second media"

    create_media_file(
        connection,
        file_name="first.bin",
        media_type="binary",
        content=first_content,
    )

    create_media_file(
        connection,
        file_name="second.bin",
        media_type="binary",
        content=second_content,
    )

    first_hash = hashlib.sha256(first_content).hexdigest()

    media_files = list_media_files(
        connection,
        sha256=first_hash,
    )

    assert len(media_files) == 1
    assert media_files[0]["file_name"] == "first.bin"


def test_list_media_files_with_combined_filters(
    connection,
    ted_file_id,
):
    content = b"shared media"

    create_media_file(
        connection,
        file_name="matching.bin",
        media_type="image",
        content=content,
        ted_file_id=ted_file_id,
        purpose="player_face",
    )

    create_media_file(
        connection,
        file_name="different_purpose.bin",
        media_type="image",
        content=content,
        ted_file_id=ted_file_id,
        purpose="team_badge",
    )

    media_files = list_media_files(
        connection,
        ted_file_id=ted_file_id,
        purpose="player_face",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    assert len(media_files) == 1
    assert media_files[0]["file_name"] == "matching.bin"


def test_delete_media_file(
    connection,
    media_content,
):
    media_file_id = create_media_file(
        connection,
        file_name="delete.bin",
        media_type="binary",
        content=media_content,
    )

    deleted = delete_media_file(
        connection,
        media_file_id,
    )

    media_file = get_media_file(
        connection,
        media_file_id,
    )

    assert deleted is True
    assert media_file is None


def test_delete_media_file_not_found(connection):
    deleted = delete_media_file(
        connection,
        999,
    )

    assert deleted is False
