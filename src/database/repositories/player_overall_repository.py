
import sqlite3


def get_player_position_overalls(
    connection: sqlite3.Connection,
    player_record_id: int,
    calculation_version: str,
) -> list[sqlite3.Row]:
    """Retrieve calculated Overalls for all positions of a player."""
    return connection.execute(
        """
        SELECT *
        FROM player_position_overalls
        WHERE player_record_id = ?
          AND calculation_version = ?
        ORDER BY position
        """,
        (player_record_id, calculation_version),
    ).fetchall()


def get_player_registered_overall(
    connection: sqlite3.Connection,
    player_record_id: int,
    calculation_version: str,
) -> sqlite3.Row | None:
    """Retrieve the calculated Overall for the registered position."""
    return connection.execute(
        """
        SELECT *
        FROM player_registered_overalls
        WHERE player_record_id = ?
          AND calculation_version = ?
        """,
        (player_record_id, calculation_version),
    ).fetchone()


def create_player_position_overall(
    connection: sqlite3.Connection,
    player_record_id: int,
    position: str,
    overall: int,
    calculation_version: str,
) -> bool:
    """Create a calculated Overall for a specific player position."""
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO player_position_overalls (
            player_record_id,
            position,
            overall,
            calculation_version
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            player_record_id,
            position,
            overall,
            calculation_version,
        ),
    )

    return cursor.rowcount > 0


def create_player_registered_overall(
    connection: sqlite3.Connection,
    player_record_id: int,
    registered_position: str,
    overall: int,
    calculation_version: str,
) -> bool:
    """Create a calculated Overall for the player's registered position."""
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO player_registered_overalls (
            player_record_id,
            registered_position,
            overall,
            calculation_version
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            player_record_id,
            registered_position,
            overall,
            calculation_version,
        ),
    )

    return cursor.rowcount > 0
