
import importlib
import sqlite3


MIGRATIONS = [
    (1, "database.migrations.001_initial_schema"),
    (2, "database.migrations.002_teams_coaches_ted_files"),
    (3, "database.migrations.003_player_records"),
    (4, "database.migrations.004_media_files"),
    (5, "database.migrations.005_ted_versions"),
    (6, "database.migrations.006_editing_history"),
    (7, "database.migrations.007_rollback_events"),
    (8, "database.migrations.008_add_coach_external_id"),
    (9, "database.migrations.009_prevent_duplicate_player_rules")
]

LATEST_SCHEMA_VERSION = MIGRATIONS[-1][0]


def migrate_database(connection: sqlite3.Connection) -> None:
    """Apply all pending database migrations."""
    current_version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

    if current_version > LATEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {current_version} "
            f"is newer than supported version {LATEST_SCHEMA_VERSION}."
        )

    with connection:
        for version, module_name in MIGRATIONS:
            if version > current_version:
                migration = importlib.import_module(module_name)
                migration.upgrade(connection)

                connection.execute(
                    f"PRAGMA user_version = {version}"
                )
