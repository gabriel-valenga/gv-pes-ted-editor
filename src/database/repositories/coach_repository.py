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
    external_id: str | None = None,
) -> int:
    """Create a coach and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO coaches (
            name,
            external_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (name, external_id, timestamp, timestamp),
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


def get_coach_by_external_id(
    connection: sqlite3.Connection,
    external_id: str,
) -> sqlite3.Row | None:
    """Retrieve a coach by its external identifier."""
    return connection.execute(
        """
        SELECT *
        FROM coaches
        WHERE external_id = ?
        """,
        (external_id,),
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
    external_id: str | None = None,
) -> bool:
    """Update a coach's name and external identifier."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        UPDATE coaches
        SET name = ?,
            external_id = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (name, external_id, timestamp, coach_id),
    )

    return cursor.rowcount > 0
