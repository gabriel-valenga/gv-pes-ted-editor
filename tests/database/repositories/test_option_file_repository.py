
import sqlite3

import pytest

from database.connection import get_connection
from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    get_option_file,
    list_option_files,
    update_option_file,
    create_option_file_import,
    list_option_file_imports,
)


@pytest.fixture
def connection(tmp_path):
    """Create a migrated temporary database for repository tests."""
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    yield connection

    connection.close()


def test_create_option_file(connection):
    option_file_id = create_option_file(
        connection,
        "My Option File",
    )

    option_file = get_option_file(
        connection,
        option_file_id,
    )

    assert option_file is not None
    assert option_file["name"] == "My Option File"
    assert option_file["created_at"] is not None
    assert option_file["updated_at"] is not None


def test_get_option_file_returns_none_for_missing_id(connection):
    option_file = get_option_file(connection, 999)

    assert option_file is None


def test_list_option_files(connection):
    create_option_file(connection, "Option File B")
    create_option_file(connection, "Option File A")

    option_files = list_option_files(connection)

    assert len(option_files) == 2
    assert [item["name"] for item in option_files] == [
        "Option File A",
        "Option File B",
    ]


def test_update_option_file(connection):
    option_file_id = create_option_file(
        connection,
        "Original Name",
    )

    updated = update_option_file(
        connection,
        option_file_id,
        "Updated Name",
    )

    option_file = get_option_file(
        connection,
        option_file_id,
    )

    assert updated is True
    assert option_file["name"] == "Updated Name"


def test_update_option_file_returns_false_for_missing_id(connection):
    updated = update_option_file(
        connection,
        999,
        "Updated Name",
    )

    assert updated is False


def test_create_option_file_import(connection):
    option_file_id = create_option_file(
        connection,
        "My Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
        "C:/PES/OptionFile",
    )

    imports = list_option_file_imports(
        connection,
        option_file_id,
    )

    assert import_id is not None
    assert len(imports) == 1
    assert imports[0]["source_path"] == "C:/PES/OptionFile"
    assert imports[0]["imported_at"] is not None
    assert imports[0]["created_at"] is not None


def test_create_option_file_import_without_source_path(connection):
    option_file_id = create_option_file(
        connection,
        "My Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    imports = list_option_file_imports(
        connection,
        option_file_id,
    )

    assert import_id is not None
    assert len(imports) == 1
    assert imports[0]["source_path"] is None


def test_list_option_file_imports_preserves_history(connection):
    option_file_id = create_option_file(
        connection,
        "My Option File",
    )

    create_option_file_import(
        connection,
        option_file_id,
        "C:/PES/Import1",
    )

    create_option_file_import(
        connection,
        option_file_id,
        "C:/PES/Import2",
    )

    imports = list_option_file_imports(
        connection,
        option_file_id,
    )

    assert len(imports) == 2
    assert {item["source_path"] for item in imports} == {
        "C:/PES/Import1",
        "C:/PES/Import2",
    }


def test_create_option_file_import_rejects_invalid_option_file_id(
    connection,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_option_file_import(
            connection,
            999,
            "C:/PES/OptionFile",
        )


def test_list_option_file_imports_returns_empty_list(connection):
    option_file_id = create_option_file(
        connection,
        "My Option File",
    )

    imports = list_option_file_imports(
        connection,
        option_file_id,
    )

    assert imports == []
