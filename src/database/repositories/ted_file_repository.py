
from datetime import datetime, timezone
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def create_ted_file(
    connection: sqlite3.Connection,
    import_id: int,
    file_name: str,
    team_id: int | None = None,
    coach_id: int | None = None,
    relative_path: str | None = None,
) -> int:
    """Create a TED file record and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO ted_files (
            import_id,
            team_id,
            coach_id,
            file_name,
            relative_path,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            import_id,
            team_id,
            coach_id,
            file_name,
            relative_path,
            timestamp,
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_ted_file(
    connection: sqlite3.Connection,
    ted_file_id: int,
) -> sqlite3.Row | None:
    """Retrieve a TED file by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM ted_files
        WHERE id = ?
        """,
        (ted_file_id,),
    ).fetchone()


def list_ted_files(
    connection: sqlite3.Connection,
    import_id: int | None = None,
    team_id: int | None = None,
    coach_id: int | None = None,
) -> list[sqlite3.Row]:
    """Retrieve TED files with optional filters."""
    query = """
        SELECT *
        FROM ted_files
        WHERE 1 = 1
    """
    parameters = []

    if import_id is not None:
        query += " AND import_id = ?"
        parameters.append(import_id)

    if team_id is not None:
        query += " AND team_id = ?"
        parameters.append(team_id)

    if coach_id is not None:
        query += " AND coach_id = ?"
        parameters.append(coach_id)

    query += " ORDER BY file_name"

    return connection.execute(
        query,
        parameters,
    ).fetchall()


def update_ted_file(
    connection: sqlite3.Connection,
    ted_file_id: int,
    file_name: str,
    team_id: int | None = None,
    coach_id: int | None = None,
    relative_path: str | None = None,
) -> bool:
    """Update a TED file record."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        UPDATE ted_files
        SET file_name = ?,
            team_id = ?,
            coach_id = ?,
            relative_path = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            file_name,
            team_id,
            coach_id,
            relative_path,
            timestamp,
            ted_file_id,
        ),
    )

    return cursor.rowcount > 0
