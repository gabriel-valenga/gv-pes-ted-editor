
def upgrade(connection):
    """Create editing history tables and relationships."""
    connection.execute("""
        CREATE TABLE edit_runs (
            id INTEGER PRIMARY KEY,
            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'running',
                        'completed',
                        'failed'
                    )
                ),
            config_json TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE edit_run_ted_files (
            id INTEGER PRIMARY KEY,
            edit_run_id INTEGER NOT NULL,
            ted_file_id INTEGER NOT NULL,
            source_version_id INTEGER,
            output_version_id INTEGER,
            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'pending',
                        'completed',
                        'failed'
                    )
                ),
            started_at TEXT,
            completed_at TEXT,

            FOREIGN KEY (edit_run_id)
                REFERENCES edit_runs(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (ted_file_id)
                REFERENCES ted_files(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (source_version_id)
                REFERENCES ted_versions(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (output_version_id)
                REFERENCES ted_versions(id)
                ON DELETE RESTRICT,

            UNIQUE (edit_run_id, ted_file_id)
        )
    """)

    connection.execute("""
        CREATE TABLE edit_run_rules (
            id INTEGER PRIMARY KEY,
            edit_run_id INTEGER NOT NULL,
            rule_order INTEGER NOT NULL,
            rule_name TEXT,
            rule_json TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (edit_run_id)
                REFERENCES edit_runs(id)
                ON DELETE RESTRICT,

            UNIQUE (edit_run_id, rule_order)
        )
    """)

    connection.execute("""
        CREATE TABLE edit_changes (
            id INTEGER PRIMARY KEY,
            edit_run_ted_file_id INTEGER NOT NULL,
            edit_run_rule_id INTEGER,
            player_index INTEGER NOT NULL,
            player_id INTEGER,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY (edit_run_ted_file_id)
                REFERENCES edit_run_ted_files(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (edit_run_rule_id)
                REFERENCES edit_run_rules(id)
                ON DELETE RESTRICT
        )
    """)

    # Ensure source and output versions belong to the same TED file.
    connection.execute("""
        CREATE TRIGGER trg_edit_run_ted_files_validate_versions_insert
        BEFORE INSERT ON edit_run_ted_files
        BEGIN
            SELECT CASE
                WHEN NEW.source_version_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM ted_versions
                        WHERE id = NEW.source_version_id
                        AND ted_file_id = NEW.ted_file_id
                    )
                THEN RAISE(
                    ABORT,
                    'Source version belongs to a different TED file.'
                )
            END;

            SELECT CASE
                WHEN NEW.output_version_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM ted_versions
                        WHERE id = NEW.output_version_id
                        AND ted_file_id = NEW.ted_file_id
                    )
                THEN RAISE(
                    ABORT,
                    'Output version belongs to a different TED file.'
                )
            END;
        END
    """)

    connection.execute("""
        CREATE TRIGGER trg_edit_run_ted_files_validate_versions_update
        BEFORE UPDATE OF ted_file_id, source_version_id, output_version_id
        ON edit_run_ted_files
        BEGIN
            SELECT CASE
                WHEN NEW.source_version_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM ted_versions
                        WHERE id = NEW.source_version_id
                        AND ted_file_id = NEW.ted_file_id
                    )
                THEN RAISE(
                    ABORT,
                    'Source version belongs to a different TED file.'
                )
            END;

            SELECT CASE
                WHEN NEW.output_version_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM ted_versions
                        WHERE id = NEW.output_version_id
                        AND ted_file_id = NEW.ted_file_id
                    )
                THEN RAISE(
                    ABORT,
                    'Output version belongs to a different TED file.'
                )
            END;
        END
    """)

    # Ensure changes reference rules from the same editing run.
    connection.execute("""
        CREATE TRIGGER trg_edit_changes_validate_rule_insert
        BEFORE INSERT ON edit_changes
        WHEN NEW.edit_run_rule_id IS NOT NULL
        BEGIN
            SELECT CASE
                WHEN NOT EXISTS (
                    SELECT 1
                    FROM edit_run_ted_files AS run_file
                    JOIN edit_run_rules AS run_rule
                        ON run_rule.id = NEW.edit_run_rule_id
                    WHERE run_file.id = NEW.edit_run_ted_file_id
                    AND run_file.edit_run_id = run_rule.edit_run_id
                )
                THEN RAISE(
                    ABORT,
                    'Rule belongs to a different editing run.'
                )
            END;
        END
    """)

    connection.execute("""
        CREATE TRIGGER trg_edit_changes_validate_rule_update
        BEFORE UPDATE OF edit_run_ted_file_id, edit_run_rule_id
        ON edit_changes
        WHEN NEW.edit_run_rule_id IS NOT NULL
        BEGIN
            SELECT CASE
                WHEN NOT EXISTS (
                    SELECT 1
                    FROM edit_run_ted_files AS run_file
                    JOIN edit_run_rules AS run_rule
                        ON run_rule.id = NEW.edit_run_rule_id
                    WHERE run_file.id = NEW.edit_run_ted_file_id
                    AND run_file.edit_run_id = run_rule.edit_run_id
                )
                THEN RAISE(
                    ABORT,
                    'Rule belongs to a different editing run.'
                )
            END;
        END
    """)

    # Create indexes.
    connection.execute("""
        CREATE INDEX idx_edit_run_ted_files_run_id
        ON edit_run_ted_files(edit_run_id)
    """)

    connection.execute("""
        CREATE INDEX idx_edit_run_ted_files_ted_file_id
        ON edit_run_ted_files(ted_file_id)
    """)

    connection.execute("""
        CREATE INDEX idx_edit_run_rules_run_id
        ON edit_run_rules(edit_run_id)
    """)

    connection.execute("""
        CREATE INDEX idx_edit_changes_run_ted_file_id
        ON edit_changes(edit_run_ted_file_id)
    """)

    connection.execute("""
        CREATE INDEX idx_edit_changes_player_id
        ON edit_changes(player_id)
    """)
