
import sqlite3
import pytest
import importlib
from ted.fields import PLAYER_FIELDS
from database.connection import get_connection
from database.migration_runner import (
    LATEST_SCHEMA_VERSION,
    migrate_database,
)


TIMESTAMP = "2026-10-31T12:00:00.000Z"


def get_table_names(connection):
    """Return all table names in the database."""
    return {
        row["name"]
        for row in connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)
    }


def test_migrate_database_creates_initial_tables(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)

    assert "option_files" in tables
    assert "option_file_imports" in tables

    connection.close()


def test_migrate_database_sets_schema_version(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

    assert version == LATEST_SCHEMA_VERSION

    connection.close()


def test_migrate_database_rejects_newer_schema_version(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    connection.execute("PRAGMA user_version = 999")

    with pytest.raises(RuntimeError):
        migrate_database(connection)

    connection.close()


def test_migrate_database_creates_ted_related_tables(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)

    assert "ted_files" in tables
    assert "teams" in tables
    assert "coaches" in tables

    connection.close()


def test_migrate_database_preserves_existing_data(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    # Simulate a database already migrated to version 1.
    connection.execute("""
        CREATE TABLE option_files (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE option_file_imports (
            id INTEGER PRIMARY KEY,
            option_file_id INTEGER NOT NULL,
            source_path TEXT,
            imported_at TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (option_file_id)
                REFERENCES option_files(id)
                ON DELETE RESTRICT
        )
    """)

    connection.execute("PRAGMA user_version = 1")

    connection.execute("""
        INSERT INTO option_files (
            name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?)
    """, (
        "My Option File",
        TIMESTAMP,
        TIMESTAMP,
    ))

    migrate_database(connection)

    version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

    option_file = connection.execute(
        "SELECT name FROM option_files"
    ).fetchone()

    tables = get_table_names(connection)

    assert version == LATEST_SCHEMA_VERSION
    assert option_file["name"] == "My Option File"
    assert "ted_files" in tables
    assert "teams" in tables
    assert "coaches" in tables

    connection.close()


def test_team_type_only_accepts_valid_values(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO teams (
                name,
                team_type,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Invalid Team",
            "other",
            TIMESTAMP,
            TIMESTAMP,
        ))

    connection.close()


def test_migrations_are_not_applied_twice(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    migrate_database(connection)

    indexes = {
        row["name"]
        for row in connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
        """)
    }

    version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

    assert "idx_ted_files_import_id" in indexes
    assert "idx_ted_files_team_id" in indexes
    assert "idx_ted_files_coach_id" in indexes
    assert version == LATEST_SCHEMA_VERSION

    connection.close()



def test_migrate_database_creates_player_records_table(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)

    assert "player_records" in tables

    columns = {
        row["name"]: row["type"]
        for row in connection.execute(
            "PRAGMA table_info(player_records)"
        )
    }

    assert columns["playerId"] == "INTEGER"
    assert columns["playerName"] == "TEXT"
    assert columns["playingStyle"] == "TEXT"
    assert columns["playerAppearance"] == "BLOB"
    assert columns["ted_file_id"] == "INTEGER"
    assert columns["player_index"] == "INTEGER"

    connection.close()


def test_player_records_rejects_duplicate_player_index(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO player_records (
            ted_file_id, player_index, playerId
        )
        VALUES (?, ?, ?)
    """, (1, 0, 100))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO player_records (
                ted_file_id, player_index, playerId
            )
            VALUES (?, ?, ?)
        """, (1, 0, 200))

    connection.close()


def test_player_records_allows_same_player_id_in_different_ted_files(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.executemany("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, [
        (1, "first.ted", TIMESTAMP, TIMESTAMP),
        (1, "second.ted", TIMESTAMP, TIMESTAMP),
    ])

    connection.executemany("""
        INSERT INTO player_records (
            ted_file_id, player_index, playerId
        )
        VALUES (?, ?, ?)
    """, [
        (1, 0, 100),
        (2, 0, 100),
    ])

    count = connection.execute("""
        SELECT COUNT(*)
        FROM player_records
        WHERE playerId = 100
    """).fetchone()[0]

    assert count == 2

    connection.close()



def test_migrate_database_creates_media_files_table(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)
    assert "media_files" in tables

    columns = {
        row["name"]: row["type"]
        for row in connection.execute(
            "PRAGMA table_info(media_files)"
        )
    }

    assert columns["ted_file_id"] == "INTEGER"
    assert columns["file_name"] == "TEXT"
    assert columns["media_type"] == "TEXT"
    assert columns["purpose"] == "TEXT"
    assert columns["content"] == "BLOB"
    assert columns["sha256"] == "TEXT"
    assert columns["created_at"] == "TEXT"

    connection.close()


def test_media_files_accepts_binary_content(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    binary_content = b"\x89PNG\r\n\x1a\n\x00\x01\x02"
    sha256 = "a" * 64

    connection.execute("""
        INSERT INTO media_files (
            file_name,
            media_type,
            purpose,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "emblem.png",
        "image/png",
        "team_emblem",
        binary_content,
        sha256,
        TIMESTAMP,
    ))

    media = connection.execute("""
        SELECT content, purpose
        FROM media_files
        WHERE file_name = ?
    """, ("emblem.png",)).fetchone()

    assert media["content"] == binary_content
    assert media["purpose"] == "team_emblem"

    connection.close()


def test_media_files_rejects_invalid_sha256_length(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO media_files (
                file_name,
                media_type,
                content,
                sha256,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "emblem.png",
            "image/png",
            b"binary content",
            "invalid_hash",
            TIMESTAMP,
        ))

    connection.close()



def test_migrate_database_creates_ted_versions_table(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)
    assert "ted_versions" in tables

    columns = {
        row["name"]: row["type"]
        for row in connection.execute(
            "PRAGMA table_info(ted_versions)"
        )
    }

    assert columns["ted_file_id"] == "INTEGER"
    assert columns["version_number"] == "INTEGER"
    assert columns["version_type"] == "TEXT"
    assert columns["content"] == "BLOB"
    assert columns["sha256"] == "TEXT"
    assert columns["created_at"] == "TEXT"

    connection.close()


def test_ted_versions_preserves_binary_content(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    original_content = b"\x00\x01\x02TED\xff\xfe"

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1,
        1,
        "original",
        original_content,
        "a" * 64,
        TIMESTAMP,
    ))

    version = connection.execute("""
        SELECT content
        FROM ted_versions
        WHERE ted_file_id = ?
    """, (1,)).fetchone()

    assert version["content"] == original_content

    connection.close()


def test_ted_versions_rejects_duplicate_version_number(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id, version_number, version_type,
            content, sha256, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 1, "original", b"original", "a" * 64, TIMESTAMP))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO ted_versions (
                ted_file_id, version_number, version_type,
                content, sha256, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 1, "edited", b"edited", "b" * 64, TIMESTAMP))

    connection.close()


def test_ted_versions_allows_only_one_original_per_ted(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id, version_number, version_type,
            content, sha256, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 1, "original", b"original", "a" * 64, TIMESTAMP))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO ted_versions (
                ted_file_id, version_number, version_type,
                content, sha256, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 2, "original", b"another", "b" * 64, TIMESTAMP))

    connection.close()


def test_ted_versions_rejects_invalid_version_type(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO ted_versions (
                ted_file_id, version_number, version_type,
                content, sha256, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 1, "backup", b"content", "a" * 64, TIMESTAMP))

    connection.close()



def create_test_ted_file(connection):
    """Create the minimum records required for a TED file."""
    connection.execute("""
        INSERT INTO option_files (
            name, created_at, updated_at
        )
        VALUES (?, ?, ?)
    """, ("Test Option File", TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO option_file_imports (
            option_file_id, imported_at, created_at
        )
        VALUES (?, ?, ?)
    """, (1, TIMESTAMP, TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_files (
            import_id, file_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, "test.ted", TIMESTAMP, TIMESTAMP))

    return 1


def test_migrate_database_creates_editing_history_tables(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)

    assert "edit_runs" in tables
    assert "edit_run_ted_files" in tables
    assert "edit_run_rules" in tables
    assert "edit_changes" in tables

    connection.close()


def test_edit_run_rules_preserves_rule_json(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    rule_json = '{"name": "Increase Speed", "operation": "add", "value": 5}'

    connection.execute("""
        INSERT INTO edit_runs (
            status, config_json, started_at
        )
        VALUES (?, ?, ?)
    """, ("running", "{}", TIMESTAMP))

    connection.execute("""
        INSERT INTO edit_run_rules (
            edit_run_id, rule_order, rule_name,
            rule_json, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (1, 1, "Increase Speed", rule_json, TIMESTAMP))

    rule = connection.execute("""
        SELECT rule_json
        FROM edit_run_rules
        WHERE edit_run_id = ?
    """, (1,)).fetchone()

    assert rule["rule_json"] == rule_json

    connection.close()


def test_edit_changes_preserves_old_and_new_values(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)

    connection.execute("""
        INSERT INTO edit_runs (
            status, config_json,  started_at
        )
        VALUES (?, ?, ?)
    """, ("running", "{}", TIMESTAMP))

    connection.execute("""
        INSERT INTO edit_run_ted_files (
            edit_run_id, ted_file_id, status
        )
        VALUES (?, ?, ?)
    """, (1, 1, "pending"))

    connection.execute("""
        INSERT INTO edit_changes (
            edit_run_ted_file_id,
            player_index,
            player_id,
            field_name,
            old_value,
            new_value,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (1, 0, 47287, "speed", "78", "83", TIMESTAMP))

    change = connection.execute("""
        SELECT field_name, old_value, new_value
        FROM edit_changes
        WHERE edit_run_ted_file_id = ?
    """, (1,)).fetchone()

    assert change["field_name"] == "speed"
    assert change["old_value"] == "78"
    assert change["new_value"] == "83"

    connection.close()


def test_edit_run_ted_files_rejects_duplicate_ted_in_same_run(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)

    connection.execute("""
        INSERT INTO edit_runs (
            status, config_json, started_at
        )
        VALUES (?, ?, ?)
    """, ("running", "{}", TIMESTAMP))

    connection.execute("""
        INSERT INTO edit_run_ted_files (
            edit_run_id, ted_file_id, status
        )
        VALUES (?, ?, ?)
    """, (1, 1, "pending"))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO edit_run_ted_files (
                edit_run_id, ted_file_id, status
            )
            VALUES (?, ?, ?)
        """, (1, 1, "pending"))

    connection.close()


def test_edit_run_ted_files_links_source_and_output_versions(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id, version_number, version_type,
            content, sha256, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 1, "original", b"original", "a" * 64, TIMESTAMP))

    connection.execute("""
        INSERT INTO edit_runs (
            status, config_json, started_at
        )
        VALUES (?, ?, ?)
    """, ("running", "{}", TIMESTAMP))

    connection.execute("""
        INSERT INTO edit_run_ted_files (
            edit_run_id, ted_file_id, source_version_id,
            status, started_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (1, 1, 1, "pending", TIMESTAMP))

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id, version_number, version_type,
            content, sha256, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 2, "edited", b"edited", "b" * 64, TIMESTAMP))

    connection.execute("""
        UPDATE edit_run_ted_files
        SET output_version_id = ?, status = ?
        WHERE id = ?
    """, (2, "completed", 1))

    result = connection.execute("""
        SELECT
            source_version_id,
            output_version_id,
            status
        FROM edit_run_ted_files
        WHERE id = ?
    """, (1,)).fetchone()

    assert result["source_version_id"] == 1
    assert result["output_version_id"] == 2
    assert result["status"] == "completed"

    connection.close()



def create_test_ted_versions(connection):
    """Create two TED versions for rollback tests."""
    connection.executemany("""
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (1, 1, "original", b"original", "a" * 64, TIMESTAMP),
        (1, 2, "edited", b"edited", "b" * 64, TIMESTAMP),
    ])


def test_migrate_database_creates_rollback_events_table(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)

    tables = get_table_names(connection)
    assert "rollback_events" in tables

    columns = {
        row["name"]: row["type"]
        for row in connection.execute(
            "PRAGMA table_info(rollback_events)"
        )
    }

    assert columns["ted_file_id"] == "INTEGER"
    assert columns["source_version_id"] == "INTEGER"
    assert columns["created_version_id"] == "INTEGER"
    assert columns["edit_run_id"] == "INTEGER"
    assert columns["created_at"] == "TEXT"

    connection.close()


def test_rollback_events_records_restoration(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)
    create_test_ted_versions(connection)

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 3, "restored", b"original", "c" * 64, TIMESTAMP))

    connection.execute("""
        INSERT INTO rollback_events (
            ted_file_id,
            source_version_id,
            created_version_id,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, 1, 3, TIMESTAMP))

    event = connection.execute("""
        SELECT
            ted_file_id,
            source_version_id,
            created_version_id
        FROM rollback_events
        WHERE id = 1
    """).fetchone()

    assert event["ted_file_id"] == 1
    assert event["source_version_id"] == 1
    assert event["created_version_id"] == 3

    connection.close()


def test_rollback_events_rejects_duplicate_created_version(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)
    create_test_ted_versions(connection)

    connection.execute("""
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 3, "restored", b"original", "c" * 64, TIMESTAMP))

    connection.execute("""
        INSERT INTO rollback_events (
            ted_file_id,
            source_version_id,
            created_version_id,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (1, 1, 3, TIMESTAMP))

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO rollback_events (
                ted_file_id,
                source_version_id,
                created_version_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (1, 2, 3, TIMESTAMP))

    connection.close()


def test_rollback_events_rejects_same_source_and_created_version(
    tmp_path,
):
    connection = get_connection(tmp_path / "test.db")

    migrate_database(connection)
    create_test_ted_file(connection)
    create_test_ted_versions(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO rollback_events (
                ted_file_id,
                source_version_id,
                created_version_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (1, 1, 1, TIMESTAMP))

    connection.close()


def create_test_second_ted_file(connection):
    """Create a second TED file for rollback integrity tests."""
    cursor = connection.execute("""
        INSERT INTO ted_files (
            import_id,
            file_name,
            relative_path,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        1,
        "second_team.ted",
        "second_team.ted",
        TIMESTAMP,
        TIMESTAMP,
    ))

    return cursor.lastrowid


def create_test_second_ted_versions(connection, ted_file_id):
    """Create two versions belonging to a second TED file."""
    connection.executemany("""
        INSERT INTO ted_versions (
            ted_file_id,
            version_number,
            version_type,
            content,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (ted_file_id, 1, "original", b"original2", "d" * 64, TIMESTAMP),
        (ted_file_id, 2, "edited", b"edited2", "e" * 64, TIMESTAMP),
    ])


def test_rollback_events_rejects_source_version_from_another_ted(tmp_path):
    """Reject rollback events referencing a source version from another TED."""
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    create_test_ted_file(connection)
    create_test_ted_versions(connection)

    second_ted_id = create_test_second_ted_file(connection)
    create_test_second_ted_versions(connection, second_ted_id)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO rollback_events (
                ted_file_id,
                source_version_id,
                created_version_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (1, 3, 2, TIMESTAMP))

    connection.close()


def test_rollback_events_rejects_created_version_from_another_ted(tmp_path):
    """Reject rollback events referencing a created version from another TED."""
    connection = get_connection(tmp_path / "test.db")
    migrate_database(connection)

    create_test_ted_file(connection)
    create_test_ted_versions(connection)

    second_ted_id = create_test_second_ted_file(connection)
    create_test_second_ted_versions(connection, second_ted_id)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("""
            INSERT INTO rollback_events (
                ted_file_id,
                source_version_id,
                created_version_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (1, 1, 4, TIMESTAMP))

    connection.close()


def test_player_fields_match_database_schema():
    """Ensure all TED player fields are correctly mapped to database columns."""
    migration = importlib.import_module(
        "database.migrations.003_player_records"
    )

    integer_fields = set(migration.INTEGER_FIELDS)
    boolean_fields = set(migration.BOOLEAN_FIELDS)
    text_fields = set(migration.TEXT_FIELDS)

    player_fields = {
        field["key"]: field
        for field in PLAYER_FIELDS
    }

    expected_integer_fields = set()
    expected_boolean_fields = set()
    expected_text_fields = set()
    expected_blob_fields = set()

    for field in PLAYER_FIELDS:
        key = field["key"]
        field_type = field["type"]
        transform = field.get("transform")

        if field_type == "raw_bytes":
            expected_blob_fields.add(key)

        elif transform == "j":
            expected_boolean_fields.add(key)

        elif transform in ("l4", "dt", "eB", "nB"):
            expected_text_fields.add(key)

        elif field_type == "string":
            expected_text_fields.add(key)

        else:
            expected_integer_fields.add(key)

    assert integer_fields == (
        expected_integer_fields | expected_boolean_fields
    ), (
        f"INTEGER_FIELDS mismatch. "
        f"Missing: {expected_integer_fields - integer_fields}. "
        f"Unexpected: {integer_fields - expected_integer_fields}"
    )

    assert boolean_fields == expected_boolean_fields, (
        f"BOOLEAN_FIELDS mismatch. "
        f"Missing: {expected_boolean_fields - boolean_fields}. "
        f"Unexpected: {boolean_fields - expected_boolean_fields}"
    )

    assert text_fields == expected_text_fields, (
        f"TEXT_FIELDS mismatch. "
        f"Missing: {expected_text_fields - text_fields}. "
        f"Unexpected: {text_fields - expected_text_fields}"
    )

    assert expected_blob_fields == {"playerAppearance"}

    assert len(player_fields) == len(PLAYER_FIELDS), (
        "Duplicate player field keys detected."
    )
