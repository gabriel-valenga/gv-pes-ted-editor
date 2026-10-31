
from datetime import datetime, timezone
import json
import sqlite3


def _get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _serialize_json(data: dict | list) -> str:
    """Serialize Python data into JSON."""
    return json.dumps(data, ensure_ascii=False)


def _serialize_value(value) -> str | None:
    """Serialize a change value into TEXT."""
    if value is None:
        return None

    return json.dumps(value, ensure_ascii=False)


# Edit Runs


def create_edit_run(
    connection: sqlite3.Connection,
    config: dict,
    status: str = "running",
) -> int:
    """Create an editing run and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO edit_runs (
            status,
            config_json,
            started_at
        )
        VALUES (?, ?, ?)
        """,
        (
            status,
            _serialize_json(config),
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_edit_run(
    connection: sqlite3.Connection,
    edit_run_id: int,
) -> sqlite3.Row | None:
    """Retrieve an editing run by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM edit_runs
        WHERE id = ?
        """,
        (edit_run_id,),
    ).fetchone()


def update_edit_run_status(
    connection: sqlite3.Connection,
    edit_run_id: int,
    status: str,
) -> bool:
    """Update an editing run status."""
    completed_at = (
        _get_current_timestamp()
        if status in ("completed", "failed")
        else None
    )

    cursor = connection.execute(
        """
        UPDATE edit_runs
        SET status = ?,
            completed_at = ?
        WHERE id = ?
        """,
        (status, completed_at, edit_run_id),
    )

    return cursor.rowcount > 0


# Edit Run TED Files


def create_edit_run_ted_file(
    connection: sqlite3.Connection,
    edit_run_id: int,
    ted_file_id: int,
    status: str = "pending",
    source_version_id: int | None = None,
    output_version_id: int | None = None,
) -> int:
    """Register a TED file in an editing run."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO edit_run_ted_files (
            edit_run_id,
            ted_file_id,
            source_version_id,
            output_version_id,
            status,
            started_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            edit_run_id,
            ted_file_id,
            source_version_id,
            output_version_id,
            status,
            timestamp if status != "pending" else None,
        ),
    )

    return cursor.lastrowid


def get_edit_run_ted_file(
    connection: sqlite3.Connection,
    run_ted_file_id: int,
) -> sqlite3.Row | None:
    """Retrieve a TED file entry from an editing run."""
    return connection.execute(
        """
        SELECT *
        FROM edit_run_ted_files
        WHERE id = ?
        """,
        (run_ted_file_id,),
    ).fetchone()


def list_edit_run_ted_files(
    connection: sqlite3.Connection,
    edit_run_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all TED files associated with an editing run."""
    return connection.execute(
        """
        SELECT *
        FROM edit_run_ted_files
        WHERE edit_run_id = ?
        ORDER BY id
        """,
        (edit_run_id,),
    ).fetchall()


def update_edit_run_ted_file(
    connection: sqlite3.Connection,
    run_ted_file_id: int,
    status: str,
    source_version_id: int | None = None,
    output_version_id: int | None = None,
) -> bool:
    """Update a TED file entry in an editing run."""
    completed_at = (
        _get_current_timestamp()
        if status in ("completed", "failed")
        else None
    )

    cursor = connection.execute(
        """
        UPDATE edit_run_ted_files
        SET status = ?,
            source_version_id = ?,
            output_version_id = ?,
            completed_at = ?
        WHERE id = ?
        """,
        (
            status,
            source_version_id,
            output_version_id,
            completed_at,
            run_ted_file_id,
        ),
    )

    return cursor.rowcount > 0


# Edit Run Rules


def create_edit_run_rule(
    connection: sqlite3.Connection,
    edit_run_id: int,
    rule_order: int,
    rule: dict,
    rule_name: str | None = None,
) -> int:
    """Register a rule in an editing run."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO edit_run_rules (
            edit_run_id,
            rule_order,
            rule_name,
            rule_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            edit_run_id,
            rule_order,
            rule_name,
            _serialize_json(rule),
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_edit_run_rule(
    connection: sqlite3.Connection,
    rule_id: int,
) -> sqlite3.Row | None:
    """Retrieve an editing rule by its ID."""
    return connection.execute(
        """
        SELECT *
        FROM edit_run_rules
        WHERE id = ?
        """,
        (rule_id,),
    ).fetchone()


def list_edit_run_rules(
    connection: sqlite3.Connection,
    edit_run_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all rules from an editing run in execution order."""
    return connection.execute(
        """
        SELECT *
        FROM edit_run_rules
        WHERE edit_run_id = ?
        ORDER BY rule_order
        """,
        (edit_run_id,),
    ).fetchall()


# Edit Changes


def create_edit_change(
    connection: sqlite3.Connection,
    run_ted_file_id: int,
    player_index: int,
    field_name: str,
    old_value=None,
    new_value=None,
    player_id: int | None = None,
    rule_id: int | None = None,
) -> int:
    """Register a player field change and return its ID."""
    timestamp = _get_current_timestamp()

    cursor = connection.execute(
        """
        INSERT INTO edit_changes (
            edit_run_ted_file_id,
            edit_run_rule_id,
            player_index,
            player_id,
            field_name,
            old_value,
            new_value,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_ted_file_id,
            rule_id,
            player_index,
            player_id,
            field_name,
            _serialize_value(old_value),
            _serialize_value(new_value),
            timestamp,
        ),
    )

    return cursor.lastrowid


def get_edit_change(
    connection: sqlite3.Connection,
    change_id: int,
) -> sqlite3.Row | None:
    """Retrieve an individual editing change."""
    return connection.execute(
        """
        SELECT *
        FROM edit_changes
        WHERE id = ?
        """,
        (change_id,),
    ).fetchone()


def list_edit_changes(
    connection: sqlite3.Connection,
    run_ted_file_id: int,
) -> list[sqlite3.Row]:
    """Retrieve all changes associated with a TED file in a run."""
    return connection.execute(
        """
        SELECT *
        FROM edit_changes
        WHERE edit_run_ted_file_id = ?
        ORDER BY id
        """,
        (run_ted_file_id,),
    ).fetchall()
