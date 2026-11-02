
import pytest

from database.connection import get_connection
from database.migration_runner import migrate_database


@pytest.fixture
def db_connection(tmp_path):
    """Provide an isolated SQLite database for each test."""

    database_path = tmp_path / "test_database.db"
    connection = get_connection(database_path)

    try:
        migrate_database(connection)
        yield connection
    finally:
        connection.close()


@pytest.fixture
def sample_player(db_connection):
    """Create a player with the required database relationships."""

    with db_connection:
        cursor = db_connection.execute(
            """
            INSERT INTO option_files (
                name,
                created_at,
                updated_at
            )
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            ("Test Option File",),
        )

        option_file_id = cursor.lastrowid

        cursor = db_connection.execute(
            """
            INSERT INTO option_file_imports (
                option_file_id,
                source_path,
                imported_at,
                created_at
            )
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (option_file_id, "test_option_file"),
        )

        import_id = cursor.lastrowid

        cursor = db_connection.execute(
            """
            INSERT INTO ted_files (
                import_id,
                file_name,
                relative_path,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (import_id, "test_team.ted", "test_team.ted"),
        )

        ted_file_id = cursor.lastrowid

        cursor = db_connection.execute(
            """
            INSERT INTO player_records (
                ted_file_id,
                player_index,
                playerId,
                playerName,
                registeredPosition
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (ted_file_id, 0, 12345, "Test Player", "CF"),
        )

        player_record_id = cursor.lastrowid

    return {
        "id": player_record_id,
        "ted_file_id": ted_file_id,
        "player_index": 0,
        "playerId": 12345,
        "playerName": "Test Player",
        "registeredPosition": "CF",
    }



@pytest.fixture
def complete_player(db_connection, sample_player):
    """Provide a player with all attributes required for Overall calculations."""

    attributes = {
        "attackingProwess": 75,
        "ballControl": 75,
        "dribbling": 75,
        "tightPossession": 75,
        "lowPass": 75,
        "loftedPass": 75,
        "finishing": 75,
        "headingAbility": 75,
        "placeKicking": 75,
        "curl": 75,
        "speed": 75,
        "acceleration": 75,
        "kickingPower": 75,
        "jump": 75,
        "physicalContact": 75,
        "balance": 75,
        "stamina": 75,
        "defensiveProwess": 75,
        "ballWinning": 75,
        "aggression": 75,
        "weakFootAccuracy": 3,
        "gkAwareness": 75,
        "gkReach": 75,
        "gkCatching": 75,
        "gkClearing": 75,
        "gkReflexes": 75,
    }

    assignments = ", ".join(
        f"{column} = ?" for column in attributes
    )

    db_connection.execute(
        f"""
        UPDATE player_records
        SET {assignments}
        WHERE id = ?
        """,
        (*attributes.values(), sample_player["id"]),
    )

    return sample_player
