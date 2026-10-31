
import sqlite3

import pytest

from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.team_repository import create_team
from database.repositories.coach_repository import create_coach
from database.repositories.ted_file_repository import (
    create_ted_file,
    get_ted_file,
    list_ted_files,
    update_ted_file,
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
def related_records(connection):
    """Create the records required by TED files."""
    option_file_id = create_option_file(
        connection,
        "Test Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    team_id = create_team(
        connection,
        name="Test Team",
        team_type="club",
    )

    coach_id = create_coach(
        connection,
        name="Test Coach",
    )

    return {
        "import_id": import_id,
        "team_id": team_id,
        "coach_id": coach_id,
    }


def test_create_ted_file(connection, related_records):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team.ted",
        team_id=related_records["team_id"],
        coach_id=related_records["coach_id"],
        relative_path="Teams/team.ted",
    )

    ted_file = get_ted_file(connection, ted_file_id)

    assert ted_file is not None
    assert ted_file["import_id"] == related_records["import_id"]
    assert ted_file["team_id"] == related_records["team_id"]
    assert ted_file["coach_id"] == related_records["coach_id"]
    assert ted_file["file_name"] == "team.ted"
    assert ted_file["relative_path"] == "Teams/team.ted"
    assert ted_file["created_at"] is not None
    assert ted_file["updated_at"] is not None


def test_create_ted_file_without_team_and_coach(
    connection,
    related_records,
):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="unknown.ted",
    )

    ted_file = get_ted_file(connection, ted_file_id)

    assert ted_file is not None
    assert ted_file["team_id"] is None
    assert ted_file["coach_id"] is None
    assert ted_file["relative_path"] is None


def test_get_ted_file_not_found(connection):
    ted_file = get_ted_file(connection, 999)

    assert ted_file is None


def test_list_ted_files(connection, related_records):
    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team_b.ted",
    )

    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team_a.ted",
    )

    ted_files = list_ted_files(connection)

    assert len(ted_files) == 2
    assert [item["file_name"] for item in ted_files] == [
        "team_a.ted",
        "team_b.ted",
    ]


def test_list_ted_files_by_import_id(connection, related_records):
    first_import_id = related_records["import_id"]

    option_file_id = create_option_file(
        connection,
        "Another Option File",
    )
    second_import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    create_ted_file(
        connection,
        import_id=first_import_id,
        file_name="first.ted",
    )

    create_ted_file(
        connection,
        import_id=second_import_id,
        file_name="second.ted",
    )

    ted_files = list_ted_files(
        connection,
        import_id=first_import_id,
    )

    assert len(ted_files) == 1
    assert ted_files[0]["file_name"] == "first.ted"


def test_list_ted_files_by_team_id(connection, related_records):
    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="assigned.ted",
        team_id=related_records["team_id"],
    )

    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="unassigned.ted",
    )

    ted_files = list_ted_files(
        connection,
        team_id=related_records["team_id"],
    )

    assert len(ted_files) == 1
    assert ted_files[0]["file_name"] == "assigned.ted"


def test_list_ted_files_by_coach_id(connection, related_records):
    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="assigned.ted",
        coach_id=related_records["coach_id"],
    )

    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="unassigned.ted",
    )

    ted_files = list_ted_files(
        connection,
        coach_id=related_records["coach_id"],
    )

    assert len(ted_files) == 1
    assert ted_files[0]["file_name"] == "assigned.ted"


def test_list_ted_files_with_combined_filters(
    connection,
    related_records,
):
    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="matching.ted",
        team_id=related_records["team_id"],
        coach_id=related_records["coach_id"],
    )

    create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="different.ted",
        team_id=related_records["team_id"],
    )

    ted_files = list_ted_files(
        connection,
        import_id=related_records["import_id"],
        team_id=related_records["team_id"],
        coach_id=related_records["coach_id"],
    )

    assert len(ted_files) == 1
    assert ted_files[0]["file_name"] == "matching.ted"


def test_update_ted_file(connection, related_records):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="old.ted",
    )

    updated = update_ted_file(
        connection,
        ted_file_id=ted_file_id,
        file_name="new.ted",
        team_id=related_records["team_id"],
        coach_id=related_records["coach_id"],
        relative_path="Updated/new.ted",
    )

    ted_file = get_ted_file(connection, ted_file_id)

    assert updated is True
    assert ted_file["file_name"] == "new.ted"
    assert ted_file["team_id"] == related_records["team_id"]
    assert ted_file["coach_id"] == related_records["coach_id"]
    assert ted_file["relative_path"] == "Updated/new.ted"


def test_update_ted_file_not_found(connection):
    updated = update_ted_file(
        connection,
        ted_file_id=999,
        file_name="missing.ted",
    )

    assert updated is False


def test_update_ted_file_clears_team_and_coach(
    connection,
    related_records,
):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team.ted",
        team_id=related_records["team_id"],
        coach_id=related_records["coach_id"],
    )

    update_ted_file(
        connection,
        ted_file_id=ted_file_id,
        file_name="team.ted",
    )

    ted_file = get_ted_file(connection, ted_file_id)

    assert ted_file["team_id"] is None
    assert ted_file["coach_id"] is None


@pytest.mark.parametrize(
    "invalid_field",
    ["import_id", "team_id", "coach_id"],
)
def test_create_ted_file_with_invalid_foreign_key(
    connection,
    related_records,
    invalid_field,
):
    parameters = {
        "import_id": related_records["import_id"],
        "team_id": related_records["team_id"],
        "coach_id": related_records["coach_id"],
    }

    parameters[invalid_field] = 999999

    with pytest.raises(sqlite3.IntegrityError):
        create_ted_file(
            connection,
            file_name="invalid.ted",
            **parameters,
        )


def test_update_ted_file_with_invalid_team_id(
    connection,
    related_records,
):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team.ted",
    )

    with pytest.raises(sqlite3.IntegrityError):
        update_ted_file(
            connection,
            ted_file_id=ted_file_id,
            file_name="team.ted",
            team_id=999999,
        )


def test_update_ted_file_with_invalid_coach_id(
    connection,
    related_records,
):
    ted_file_id = create_ted_file(
        connection,
        import_id=related_records["import_id"],
        file_name="team.ted",
    )

    with pytest.raises(sqlite3.IntegrityError):
        update_ted_file(
            connection,
            ted_file_id=ted_file_id,
            file_name="team.ted",
            coach_id=999999,
        )
