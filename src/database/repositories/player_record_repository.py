
import importlib
import sqlite3


_player_migration = importlib.import_module(
    "database.migrations.003_player_records"
)

PLAYER_FIELDS = (
    _player_migration.INTEGER_FIELDS
    + _player_migration.TEXT_FIELDS
    + ["playerAppearance"]
)


def _validate_player_data(data: dict) -> None:
    """Validate player data field names."""
    invalid_fields = set(data) - set(PLAYER_FIELDS)

    if invalid_fields:
        raise ValueError(
            f"Invalid player fields: {sorted(invalid_fields)}"
        )


def create_player_record(
    connection: sqlite3.Connection,
    ted_file_id: int,
    player_index: int,
    data: dict,
) -> int:
    """Create a player record and return its ID."""
    _validate_player_data(data)

    fields = list(data.keys())
    columns = ["ted_file_id", "player_index"] + fields
    values = [ted_file_id, player_index] + list(data.values())

    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    cursor = connection.execute(
        f"""
        INSERT INTO player_records ({column_names})
        VALUES ({placeholders})
        """,
        values,
    )

    return cursor.lastrowid


def get_player_record(
    connection: sqlite3.Connection,
    ted_file_id: int,
    player_index: int,
) -> sqlite3.Row | None:
    """Retrieve a player record by its TED file and index."""
    return connection.execute(
        """
        SELECT *
        FROM player_records
        WHERE ted_file_id = ?
          AND player_index = ?
        """,
        (ted_file_id, player_index),
    ).fetchone()


def list_player_records(
    connection: sqlite3.Connection,
    ted_file_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all player records from a TED file."""
    return connection.execute(
        """
        SELECT *
        FROM player_records
        WHERE ted_file_id = ?
        ORDER BY player_index
        """,
        (ted_file_id,),
    ).fetchall()


def update_player_record(
    connection: sqlite3.Connection,
    ted_file_id: int,
    player_index: int,
    data: dict,
) -> bool:
    """Update specific fields of a player record."""
    _validate_player_data(data)

    if not data:
        return False

    assignments = ", ".join(
        f"{field} = ?"
        for field in data
    )

    values = list(data.values()) + [
        ted_file_id,
        player_index,
    ]

    cursor = connection.execute(
        f"""
        UPDATE player_records
        SET {assignments}
        WHERE ted_file_id = ?
          AND player_index = ?
        """,
        values,
    )

    return cursor.rowcount > 0


def delete_player_record(
    connection: sqlite3.Connection,
    ted_file_id: int,
    player_index: int,
) -> bool:
    """Delete a player record by its TED file and index."""
    cursor = connection.execute(
        """
        DELETE FROM player_records
        WHERE ted_file_id = ?
          AND player_index = ?
        """,
        (ted_file_id, player_index),
    )

    return cursor.rowcount > 0
