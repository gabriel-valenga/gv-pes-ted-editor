
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def create_option_file(
    connection: sqlite3.Connection,
    name: str,
) -> int:
    """Create an Option File record and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO option_files (
            name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?)
        """,
        (name, timestamp, timestamp),
    )

    return cursor.lastrowid


def get_option_file(
    connection: sqlite3.Connection,
    option_file_id: int,
) -> sqlite3.Row | None:
    """Retrieve an Option File by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM option_files
        WHERE id = ?
        """,
        (option_file_id,),
    ).fetchone()


def list_option_files(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Retrieve all registered Option Files."""
    return connection.execute(
        """
        SELECT *
        FROM option_files
        ORDER BY name
        """
    ).fetchall()


def update_option_file(
    connection: sqlite3.Connection,
    option_file_id: int,
    name: str,
) -> bool:
    """Update an Option File name."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        UPDATE option_files
        SET name = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (name, timestamp, option_file_id),
    )

    return cursor.rowcount > 0


def create_option_file_import(
    connection: sqlite3.Connection,
    option_file_id: int,
    source_path: str | Path | None = None,
) -> int:
    """Register a new Option File import and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO option_file_imports (
            option_file_id,
            source_path,
            imported_at,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            option_file_id,
            str(source_path) if source_path is not None else None,
            timestamp,
            timestamp,
        ),
    )

    return cursor.lastrowid


def list_option_file_imports(
    connection: sqlite3.Connection,
    option_file_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all imports associated with an Option File."""
    return connection.execute(
        """
        SELECT *
        FROM option_file_imports
        WHERE option_file_id = ?
        ORDER BY imported_at DESC, id DESC
        """,
        (option_file_id,),
    ).fetchall()
