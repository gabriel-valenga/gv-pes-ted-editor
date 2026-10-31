
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


def create_ted_version(
    connection: sqlite3.Connection,
    ted_file_id: int,
    version_number: int,
    version_type: str,
    content: bytes,
) -> int:
    """Create a TED version and return its ID."""
    if not isinstance(content, bytes):
        raise TypeError("TED version content must be bytes.")

    sha256 = hashlib.sha256(content).hexdigest()
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_ted_version(
    connection: sqlite3.Connection,
    version_id: int,
) -> sqlite3.Row | None:
    """Retrieve a TED version, including its binary content."""
    return connection.execute(
        """
        SELECT *
        FROM ted_versions
        WHERE id = ?
        """,
        (version_id,),
    ).fetchone()


def list_ted_versions(
    connection: sqlite3.Connection,
    ted_file_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all versions of a TED file without loading their content."""
    return connection.execute(
        """
        SELECT
            id,
            ted_file_id,
            version_number,
            version_type,
            sha256,
            created_at
        FROM ted_versions
        WHERE ted_file_id = ?
        ORDER BY version_number
        """,
        (ted_file_id,),
    ).fetchall()


def get_latest_ted_version(
    connection: sqlite3.Connection,
    ted_file_id: int,
) -> sqlite3.Row | None:
    """Retrieve the latest version metadata of a TED file."""
    return connection.execute(
        """
        SELECT
            id,
            ted_file_id,
            version_number,
            version_type,
            sha256,
            created_at
        FROM ted_versions
        WHERE ted_file_id = ?
        ORDER BY version_number DESC
        LIMIT 1
        """,
        (ted_file_id,),
    ).fetchone()


def get_ted_version_content(
    connection: sqlite3.Connection,
    version_id: int,
) -> bytes | None:
    """Retrieve only the binary content of a TED version."""
    row = connection.execute(
        """
        SELECT content
        FROM ted_versions
        WHERE id = ?
        """,
        (version_id,),
    ).fetchone()

    return row["content"] if row is not None else None
