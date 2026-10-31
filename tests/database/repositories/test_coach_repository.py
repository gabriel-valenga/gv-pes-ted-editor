
from database.connection import get_connection
from database.migration_runner import migrate_database
from database.repositories.coach_repository import (
    create_coach,
    get_coach,
    list_coaches,
    update_coach,
)


import pytest


@pytest.fixture
def connection(tmp_path):
    """Create a migrated temporary database for repository tests."""
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    yield connection

    connection.close()


def test_create_coach(connection):
    coach_id = create_coach(connection, "Pep Guardiola")

    coach = get_coach(connection, coach_id)

    assert coach is not None
    assert coach["name"] == "Pep Guardiola"
    assert coach["created_at"] is not None
    assert coach["updated_at"] is not None


def test_get_coach_returns_none_for_missing_id(connection):
    assert get_coach(connection, 999) is None


def test_list_coaches(connection):
    create_coach(connection, "Carlo Ancelotti")
    create_coach(connection, "Pep Guardiola")

    coaches = list_coaches(connection)

    assert len(coaches) == 2
    assert [coach["name"] for coach in coaches] == [
        "Carlo Ancelotti",
        "Pep Guardiola",
    ]


def test_update_coach(connection):
    coach_id = create_coach(connection, "Old Name")

    updated = update_coach(
        connection,
        coach_id,
        "New Name",
    )

    coach = get_coach(connection, coach_id)

    assert updated is True
    assert coach["name"] == "New Name"


def test_update_coach_returns_false_for_missing_id(connection):
    updated = update_coach(
        connection,
        999,
        "New Name",
    )

    assert updated is False
