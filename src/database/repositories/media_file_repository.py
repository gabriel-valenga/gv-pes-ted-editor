
from datetime import datetime, timezone
import hashlib
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def create_media_file(
    connection: sqlite3.Connection,
    file_name: str,
    media_type: str,
    content: bytes,
    ted_file_id: int | None = None,
    purpose: str | None = None,
) -> int:
    """Create a media file record and return its ID."""
    if not isinstance(content, bytes):
        raise TypeError("Media content must be bytes.")

    sha256 = hashlib.sha256(content).hexdigest()
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO media_files (
            ted_file_id,
            file_name,
            media_type,
            purpose,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ted_file_id,
            file_name,
            media_type,
            purpose,
            content,
            sha256,
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_media_file(
    connection: sqlite3.Connection,
    media_file_id: int,
) -> sqlite3.Row | None:
    """Retrieve a media file, including its binary content."""
    return connection.execute(
        """
        SELECT *
        FROM media_files
        WHERE id = ?
        """,
        (media_file_id,),
    ).fetchone()


def list_media_files(
    connection: sqlite3.Connection,
    ted_file_id: int | None = None,
    purpose: str | None = None,
    sha256: str | None = None,
) -> list[sqlite3.Row]:
    """Retrieve media file metadata with optional filters."""
    query = """
        SELECT
            id,
            ted_file_id,
            file_name,
            media_type,
            purpose,
            sha256,
            created_at
        FROM media_files
        WHERE 1 = 1
    """
    parameters = []

    if ted_file_id is not None:
        query += " AND ted_file_id = ?"
        parameters.append(ted_file_id)

    if purpose is not None:
        query += " AND purpose = ?"
        parameters.append(purpose)

    if sha256 is not None:
        query += " AND sha256 = ?"
        parameters.append(sha256)

    query += " ORDER BY file_name"

    return connection.execute(
        query,
        parameters,
    ).fetchall()


def delete_media_file(
    connection: sqlite3.Connection,
    media_file_id: int,
) -> bool:
    """Delete a media file record."""
    cursor = connection.execute(
        """
        DELETE FROM media_files
        WHERE id = ?
        """,
        (media_file_id,),
    )

    return cursor.rowcount > 0
