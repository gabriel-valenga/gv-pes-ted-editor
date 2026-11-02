
import sqlite3

import cli

from database.connection import get_connection
from database.migration_runner import migrate_database
from database.repositories.editing_history_repository import (
    create_edit_run,
    create_edit_run_rule,
)
from editing.players.rules import build_rule_hash


TIMESTAMP = "2026-10-31T12:00:00.000Z"


def create_database(tmp_path):
    database_path = tmp_path / "test.db"

    connection = get_connection(database_path)
    migrate_database(connection)

    connection.execute(
        """
        INSERT INTO option_files (
            name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?)
        """,
        ("Test Option File", TIMESTAMP, TIMESTAMP),
    )

    option_file_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO option_file_imports (
            option_file_id,
            imported_at,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (option_file_id, TIMESTAMP, TIMESTAMP),
    )

    import_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO ted_files (
            import_id,
            file_name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (import_id, "team.ted", TIMESTAMP, TIMESTAMP),
    )

    ted_file_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    edit_run_id = create_edit_run(
        connection=connection,
        config={"command": "test"},
    )

    rule = {
        "name": "Increase speed",
        "enabled": True,
        "conditions": [],
        "operations": [
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    }

    rule_id = create_edit_run_rule(
        connection=connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule=rule,
        rule_name=rule["name"],
    )

    rule_hash = build_rule_hash(rule)

    connection.execute(
        """
        UPDATE edit_run_rules
        SET rule_hash = ?
        WHERE id = ?
        """,
        (rule_hash, rule_id),
    )

    connection.commit()

    return connection, ted_file_id, edit_run_id, rule_id, rule_hash


def test_register_history_persists_successful_rule_application(
    tmp_path,
):
    (
        connection,
        ted_file_id,
        edit_run_id,
        rule_id,
        rule_hash,
    ) = create_database(tmp_path)

    result = {
        "players": [
            {
                "index": 0,
                "playerId": 1001,
            }
        ],
        "edits": [
            {
                "index": 0,
                "playerId": 1001,
                "field": "speed",
                "before": 70,
                "after": 75,
                "source": "rule",
                "ruleHash": rule_hash,
            }
        ],
    }

    with connection:
        cli._register_ted_edit_history(
            connection=connection,
            edit_run_id=edit_run_id,
            ted_file_id=ted_file_id,
            source_version_id=None,
            result=result,
            output_path=None,
            source_content=b"original ted",
            rule_ids_by_hash={
                rule_hash: rule_id,
            },
        )

    application = connection.execute(
        """
        SELECT *
        FROM player_rule_applications
        WHERE player_id = ?
          AND rule_hash = ?
        """,
        (1001, rule_hash),
    ).fetchone()

    assert application is not None
    assert application["player_id"] == 1001
    assert application["rule_hash"] == rule_hash
    assert application["first_ted_file_id"] == ted_file_id
    assert application["first_edit_run_id"] == edit_run_id
    assert application["first_edit_run_rule_id"] == rule_id

    connection.close()


def test_register_history_does_not_persist_application_without_edits(
    tmp_path,
):
    (
        connection,
        ted_file_id,
        edit_run_id,
        rule_id,
        rule_hash,
    ) = create_database(tmp_path)

    result = {
        "players": [
            {
                "index": 0,
                "playerId": 1001,
            }
        ],
        "edits": [],
    }

    with connection:
        cli._register_ted_edit_history(
            connection=connection,
            edit_run_id=edit_run_id,
            ted_file_id=ted_file_id,
            source_version_id=None,
            result=result,
            output_path=None,
            source_content=b"original ted",
            rule_ids_by_hash={
                rule_hash: rule_id,
            },
        )

    application_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_rule_applications
        WHERE player_id = ?
          AND rule_hash = ?
        """,
        (1001, rule_hash),
    ).fetchone()[0]

    assert application_count == 0

    connection.close()



def test_first_rule_application_has_priority_across_teds_and_runs(
    tmp_path,
    monkeypatch,
):
    (
        connection,
        first_ted_id,
        first_run_id,
        first_rule_id,
        rule_hash,
    ) = create_database(tmp_path)

    import_id = connection.execute(
        """
        SELECT import_id
        FROM ted_files
        WHERE id = ?
        """,
        (first_ted_id,),
    ).fetchone()["import_id"]

    ted_ids = [first_ted_id]

    for filename in ("second_team.ted", "third_team.ted"):
        cursor = connection.execute(
            """
            INSERT INTO ted_files (
                import_id,
                file_name,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (import_id, filename, TIMESTAMP, TIMESTAMP),
        )
        ted_ids.append(cursor.lastrowid)

    rule = {
        "name": "Increase speed",
        "enabled": True,
        "conditions": [],
        "operations": [
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    }

    rules_list = [{"rules": [rule]}]

    # Register the first effective application in TED 1.
    first_result = {
        "players": [
            {"index": 0, "playerId": 1001},
        ],
        "edits": [
            {
                "index": 0,
                "playerId": 1001,
                "field": "speed",
                "before": 70,
                "after": 75,
                "source": "rule",
                "ruleHash": rule_hash,
            }
        ],
    }

    with connection:
        cli._register_ted_edit_history(
            connection=connection,
            edit_run_id=first_run_id,
            ted_file_id=ted_ids[0],
            source_version_id=None,
            result=first_result,
            output_path=None,
            source_content=b"TED 1",
            rule_ids_by_hash={
                rule_hash: first_rule_id,
            },
        )

    # The same player appears in TED 2.
    second_ted_path = tmp_path / "second_team.ted"
    second_ted_path.write_bytes(b"TED 2")

    monkeypatch.setattr(
        cli,
        "decrypt_ted",
        lambda content: b"decrypted",
    )

    monkeypatch.setattr(
        cli,
        "extract_players",
        lambda data: [
            {"index": 0, "playerId": 1001},
        ],
    )

    second_prepared = cli._prepare_rules_for_ted(
        connection=connection,
        ted_path=second_ted_path,
        ted_file_id=ted_ids[1],
        rules_list=rules_list,
    )

    # An application in TED 1 must not block the player in TED 2.
    assert second_prepared[0]["rules"][0]["playerIds"] == [1001]

    # Start a new execution and register the same functional rule again.
    with connection:
        second_run_id = create_edit_run(
            connection=connection,
            config={"command": "second execution"},
        )

        second_rule_ids = cli._build_rule_records(
            connection=connection,
            edit_run_id=second_run_id,
            rules_list=rules_list,
        )

    assert second_rule_ids[rule_hash] != first_rule_id

    # The same player appears in TED 3 during the new execution.
    third_ted_path = tmp_path / "third_team.ted"
    third_ted_path.write_bytes(b"TED 3")

    third_prepared = cli._prepare_rules_for_ted(
        connection=connection,
        ted_path=third_ted_path,
        ted_file_id=ted_ids[2],
        rules_list=rules_list,
    )

    # The application in TED 1 must not block the player in TED 3 either.
    assert third_prepared[0]["rules"][0]["playerIds"] == [1001]

    # The original application must remain the first one.
    application = connection.execute(
        """
        SELECT *
        FROM player_rule_applications
        WHERE player_id = ?
          AND rule_hash = ?
        """,
        (1001, rule_hash),
    ).fetchone()

    assert application is not None
    assert application["first_ted_file_id"] == ted_ids[0]
    assert application["first_edit_run_id"] == first_run_id
    assert application["first_edit_run_rule_id"] == first_rule_id

    application_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_rule_applications
        WHERE player_id = ?
          AND rule_hash = ?
        """,
        (1001, rule_hash),
    ).fetchone()[0]

    assert application_count == 1

    connection.close()
