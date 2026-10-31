
from datetime import datetime, timezone
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def create_coach(
    connection: sqlite3.Connection,
    name: str,
) -> int:
    """Create a coach and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO coaches (
            name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?)
        """,
        (name, timestamp, timestamp),
    )

    return cursor.lastrowid


def get_coach(
    connection: sqlite3.Connection,
    coach_id: int,
) -> sqlite3.Row | None:
    """Retrieve a coach by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM coaches
        WHERE id = ?
        """,
        (coach_id,),
    ).fetchone()


def list_coaches(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Retrieve all coaches."""
    return connection.execute(
        """
        SELECT *
        FROM coaches
        ORDER BY name
        """
    ).fetchall()


def update_coach(
    connection: sqlite3.Connection,
    coach_id: int,
    name: str,
) -> bool:
    """Update a coach's name."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        UPDATE coaches
        SET name = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (name, timestamp, coach_id),
    )

    return cursor.rowcount > 0
