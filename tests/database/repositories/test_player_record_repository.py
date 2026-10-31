
import sqlite3

import pytest

from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.team_repository import create_team
from database.repositories.coach_repository import create_coach
from database.repositories.ted_file_repository import create_ted_file
from database.repositories.player_record_repository import (
    create_player_record,
    get_player_record,
    list_player_records,
    update_player_record,
    delete_player_record,
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
    """Create the records required by a TED file."""
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

    return create_ted_file(
        connection,
        import_id=import_id,
        team_id=team_id,
        coach_id=coach_id,
        file_name="team.ted",
    )


@pytest.fixture
def player_data():
    """Return sample player data."""
    return {
        "playerId": 12345,
        "playerName": "Test Player",
        "age": 25,
        "height": 180,
        "speed": 85,
        "finishing": 90,
        "isFromLiveUpdate": 1,
        "scissorsFeint": 0,
        "strongerFoot": "Right",
        "playerAppearance": bytes(72),
    }


def test_create_player_record(
    connection,
    ted_file_id,
    player_data,
):
    player_record_id = create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data=player_data,
    )

    player = get_player_record(
        connection,
        ted_file_id,
        0,
    )

    assert player_record_id is not None
    assert player is not None
    assert player["ted_file_id"] == ted_file_id
    assert player["player_index"] == 0
    assert player["playerId"] == 12345
    assert player["playerName"] == "Test Player"
    assert player["age"] == 25
    assert player["speed"] == 85
    assert player["finishing"] == 90
    assert player["isFromLiveUpdate"] == 1
    assert player["scissorsFeint"] == 0
    assert player["strongerFoot"] == "Right"
    assert player["playerAppearance"] == bytes(72)


def test_create_player_record_with_empty_data(
    connection,
    ted_file_id,
):
    player_record_id = create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={},
    )

    player = get_player_record(
        connection,
        ted_file_id,
        0,
    )

    assert player_record_id is not None
    assert player is not None
    assert player["ted_file_id"] == ted_file_id
    assert player["player_index"] == 0
    assert player["playerId"] is None


def test_create_player_record_with_invalid_field(
    connection,
    ted_file_id,
):
    with pytest.raises(ValueError):
        create_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={
                "invalidField": 123,
            },
        )


def test_create_player_record_with_invalid_foreign_key(
    connection,
    player_data,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_player_record(
            connection,
            ted_file_id=999999,
            player_index=0,
            data=player_data,
        )


def test_create_player_record_with_invalid_boolean(
    connection,
    ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={
                "isFromLiveUpdate": 2,
            },
        )


def test_create_player_record_with_invalid_appearance_size(
    connection,
    ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={
                "playerAppearance": bytes(71),
            },
        )


def test_get_player_record_not_found(connection, ted_file_id):
    player = get_player_record(
        connection,
        ted_file_id,
        999,
    )

    assert player is None


def test_list_player_records(connection, ted_file_id):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=2,
        data={"playerName": "Player B"},
    )

    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={"playerName": "Player A"},
    )

    players = list_player_records(
        connection,
        ted_file_id,
    )

    assert len(players) == 2
    assert [player["player_index"] for player in players] == [0, 2]
    assert [player["playerName"] for player in players] == [
        "Player A",
        "Player B",
    ]


def test_list_player_records_empty(connection, ted_file_id):
    players = list_player_records(
        connection,
        ted_file_id,
    )

    assert players == []


def test_list_player_records_only_from_requested_ted(
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

    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={"playerName": "First Player"},
    )

    create_player_record(
        connection,
        ted_file_id=another_ted_file_id,
        player_index=0,
        data={"playerName": "Second Player"},
    )

    players = list_player_records(
        connection,
        ted_file_id,
    )

    assert len(players) == 1
    assert players[0]["playerName"] == "First Player"


def test_same_player_index_in_different_ted_files(
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

    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={"playerId": 12345},
    )

    create_player_record(
        connection,
        ted_file_id=another_ted_file_id,
        player_index=0,
        data={"playerId": 12345},
    )

    first_player = get_player_record(
        connection,
        ted_file_id,
        0,
    )

    second_player = get_player_record(
        connection,
        another_ted_file_id,
        0,
    )

    assert first_player is not None
    assert second_player is not None
    assert first_player["playerId"] == second_player["playerId"]


def test_create_duplicate_player_index(
    connection,
    ted_file_id,
):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={"playerName": "First Player"},
    )

    with pytest.raises(sqlite3.IntegrityError):
        create_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={"playerName": "Second Player"},
        )


def test_update_player_record(
    connection,
    ted_file_id,
    player_data,
):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data=player_data,
    )

    updated = update_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={
            "speed": 95,
            "finishing": 98,
        },
    )

    player = get_player_record(
        connection,
        ted_file_id,
        0,
    )

    assert updated is True
    assert player["speed"] == 95
    assert player["finishing"] == 98
    assert player["playerName"] == "Test Player"
    assert player["age"] == 25


def test_update_player_record_not_found(
    connection,
    ted_file_id,
):
    updated = update_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=999,
        data={"speed": 90},
    )

    assert updated is False


def test_update_player_record_with_empty_data(
    connection,
    ted_file_id,
    player_data,
):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data=player_data,
    )

    updated = update_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={},
    )

    assert updated is False


def test_update_player_record_with_invalid_field(
    connection,
    ted_file_id,
):
    with pytest.raises(ValueError):
        update_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={
                "invalidField": 123,
            },
        )


def test_update_player_record_with_invalid_boolean(
    connection,
    ted_file_id,
):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data={"isFromLiveUpdate": 1},
    )

    with pytest.raises(sqlite3.IntegrityError):
        update_player_record(
            connection,
            ted_file_id=ted_file_id,
            player_index=0,
            data={
                "isFromLiveUpdate": 5,
            },
        )


def test_delete_player_record(
    connection,
    ted_file_id,
    player_data,
):
    create_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
        data=player_data,
    )

    deleted = delete_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=0,
    )

    player = get_player_record(
        connection,
        ted_file_id,
        0,
    )

    assert deleted is True
    assert player is None


def test_delete_player_record_not_found(
    connection,
    ted_file_id,
):
    deleted = delete_player_record(
        connection,
        ted_file_id=ted_file_id,
        player_index=999,
    )

    assert deleted is False
