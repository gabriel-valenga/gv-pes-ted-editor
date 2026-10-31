
import sqlite3

import pytest

from database.connection import get_connection
from database.migration_runner import migrate_database
from database.repositories.team_repository import (
    create_team,
    get_team,
    list_teams,
    update_team,
)


@pytest.fixture
def connection(tmp_path):
    """Create a migrated temporary database for repository tests."""
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    yield connection

    connection.close()


def test_create_team(connection):
    team_id = create_team(
        connection,
        name="Manchester City",
        team_type="club",
        short_name="Man City",
        external_id="MCI",
    )

    team = get_team(connection, team_id)

    assert team is not None
    assert team["name"] == "Manchester City"
    assert team["team_type"] == "club"
    assert team["short_name"] == "Man City"
    assert team["external_id"] == "MCI"
    assert team["created_at"] is not None
    assert team["updated_at"] is not None


def test_create_national_team(connection):
    team_id = create_team(
        connection,
        name="Brazil",
        team_type="national_team",
    )

    team = get_team(connection, team_id)

    assert team["name"] == "Brazil"
    assert team["team_type"] == "national_team"


def test_create_team_rejects_invalid_type(connection):
    with pytest.raises(sqlite3.IntegrityError):
        create_team(
            connection,
            name="Invalid Team",
            team_type="invalid",
        )


def test_get_team_returns_none_for_missing_id(connection):
    assert get_team(connection, 999) is None


def test_list_teams(connection):
    create_team(connection, "Real Madrid", "club")
    create_team(connection, "Brazil", "national_team")
    create_team(connection, "Barcelona", "club")

    teams = list_teams(connection)

    assert len(teams) == 3
    assert [team["name"] for team in teams] == [
        "Barcelona",
        "Brazil",
        "Real Madrid",
    ]


def test_list_teams_filters_by_type(connection):
    create_team(connection, "Real Madrid", "club")
    create_team(connection, "Brazil", "national_team")
    create_team(connection, "Barcelona", "club")

    teams = list_teams(connection, team_type="club")

    assert len(teams) == 2
    assert all(team["team_type"] == "club" for team in teams)


def test_update_team(connection):
    team_id = create_team(
        connection,
        name="Old Name",
        team_type="club",
        short_name="Old",
        external_id="OLD",
    )

    updated = update_team(
        connection,
        team_id,
        name="New Name",
        short_name="New",
        external_id="NEW",
    )

    team = get_team(connection, team_id)

    assert updated is True
    assert team["name"] == "New Name"
    assert team["short_name"] == "New"
    assert team["external_id"] == "NEW"
    assert team["team_type"] == "club"


def test_update_team_returns_false_for_missing_id(connection):
    updated = update_team(
        connection,
        999,
        name="New Name",
    )

    assert updated is False
