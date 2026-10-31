def upgrade(connection):
    """Create the rollback events table and enforce version ownership."""
    connection.execute("""
        CREATE TABLE rollback_events (
            id INTEGER PRIMARY KEY,
            ted_file_id INTEGER NOT NULL,
            source_version_id INTEGER NOT NULL,
            created_version_id INTEGER NOT NULL,
            edit_run_id INTEGER,
            created_at TEXT NOT NULL,

            FOREIGN KEY (ted_file_id)
                REFERENCES ted_files(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (source_version_id)
                REFERENCES ted_versions(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (created_version_id)
                REFERENCES ted_versions(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (edit_run_id)
                REFERENCES edit_runs(id)
                ON DELETE RESTRICT,

            UNIQUE (created_version_id),

            CHECK (source_version_id != created_version_id)
        )
    """)

    connection.execute("""
        CREATE INDEX idx_rollback_events_ted_file_id
        ON rollback_events(ted_file_id)
    """)

    connection.execute("""
        CREATE INDEX idx_rollback_events_source_version_id
        ON rollback_events(source_version_id)
    """)

    connection.execute("""
        CREATE TRIGGER trg_rollback_events_validate_versions_insert
        BEFORE INSERT ON rollback_events
        BEGIN
            SELECT CASE
                WHEN (
                    SELECT ted_file_id
                    FROM ted_versions
                    WHERE id = NEW.source_version_id
                ) != NEW.ted_file_id
                THEN RAISE(
                    ABORT,
                    'Source version does not belong to the specified TED file.'
                )
            END;

            SELECT CASE
                WHEN (
                    SELECT ted_file_id
                    FROM ted_versions
                    WHERE id = NEW.created_version_id
                ) != NEW.ted_file_id
                THEN RAISE(
                    ABORT,
                    'Created version does not belong to the specified TED file.'
                )
            END;
        END
    """)

    connection.execute("""
        CREATE TRIGGER trg_rollback_events_validate_versions_update
        BEFORE UPDATE OF ted_file_id, source_version_id, created_version_id
        ON rollback_events
        BEGIN
            SELECT CASE
                WHEN (
                    SELECT ted_file_id
                    FROM ted_versions
                    WHERE id = NEW.source_version_id
                ) != NEW.ted_file_id
                THEN RAISE(
                    ABORT,
                    'Source version does not belong to the specified TED file.'
                )
            END;

            SELECT CASE
                WHEN (
                    SELECT ted_file_id
                    FROM ted_versions
                    WHERE id = NEW.created_version_id
                ) != NEW.ted_file_id
                THEN RAISE(
                    ABORT,
                    'Created version does not belong to the specified TED file.'
                )
            END;
        END
    """)