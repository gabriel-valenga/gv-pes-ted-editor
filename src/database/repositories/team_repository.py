
from datetime import datetime, timezone
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def create_team(
    connection: sqlite3.Connection,
    name: str,
    team_type: str,
    short_name: str | None = None,
    external_id: str | None = None,
) -> int:
    """Create a team and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO teams (
            name,
            short_name,
            team_type,
            external_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            short_name,
            team_type,
            external_id,
            timestamp,
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_team(
    connection: sqlite3.Connection,
    team_id: int,
) -> sqlite3.Row | None:
    """Retrieve a team by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM teams
        WHERE id = ?
        """,
        (team_id,),
    ).fetchone()


def list_teams(
    connection: sqlite3.Connection,
    team_type: str | None = None,
) -> list[sqlite3.Row]:
    """Retrieve all teams, optionally filtered by type."""
    if team_type is not None:
        return connection.execute(
            """
            SELECT *
            FROM teams
            WHERE team_type = ?
            ORDER BY name
            """,
            (team_type,),
        ).fetchall()

    return connection.execute(
        """
        SELECT *
        FROM teams
        ORDER BY name
        """
    ).fetchall()


def update_team(
    connection: sqlite3.Connection,
    team_id: int,
    name: str,
    short_name: str | None = None,
    team_type: str | None = None,
    external_id: str | None = None,
) -> bool:
    """Update a team's information."""
    current_team = get_team(connection, team_id)

    if current_team is None:
        return False

    timestamp = _get_current_timestamp()

    connection.execute(
        """
        UPDATE teams
        SET name = ?,
            short_name = ?,
            team_type = ?,
            external_id = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            name,
            short_name,
            team_type or current_team["team_type"],
            external_id,
            timestamp,
            team_id,
        ),
    )

    return True
