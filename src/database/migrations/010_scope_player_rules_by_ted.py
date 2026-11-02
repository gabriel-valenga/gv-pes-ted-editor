
def upgrade(connection):
    """Scope player rule applications to individual TED files."""

    connection.execute("""
        CREATE TABLE player_rule_applications_new (
            id INTEGER PRIMARY KEY,
            player_id INTEGER NOT NULL,
            rule_hash TEXT NOT NULL,
            first_ted_file_id INTEGER NOT NULL,
            first_edit_run_id INTEGER NOT NULL,
            first_edit_run_rule_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,

            UNIQUE (
                player_id,
                rule_hash,
                first_ted_file_id
            ),

            FOREIGN KEY (first_ted_file_id)
                REFERENCES ted_files(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (first_edit_run_id)
                REFERENCES edit_runs(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (first_edit_run_rule_id)
                REFERENCES edit_run_rules(id)
                ON DELETE RESTRICT
        )
    """)

    historical_edits = connection.execute("""
        SELECT
            ec.player_id,
            err.rule_hash,
            ertf.ted_file_id,
            ertf.edit_run_id,
            ec.edit_run_rule_id,
            ec.created_at
        FROM edit_changes AS ec
        JOIN edit_run_ted_files AS ertf
            ON ertf.id = ec.edit_run_ted_file_id
        JOIN edit_run_rules AS err
            ON err.id = ec.edit_run_rule_id
        WHERE ec.player_id IS NOT NULL
          AND ec.edit_run_rule_id IS NOT NULL
          AND err.rule_hash IS NOT NULL
        ORDER BY ec.created_at, ec.id
    """).fetchall()

    for row in historical_edits:
        connection.execute("""
            INSERT OR IGNORE INTO player_rule_applications_new (
                player_id,
                rule_hash,
                first_ted_file_id,
                first_edit_run_id,
                first_edit_run_rule_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["player_id"],
            row["rule_hash"],
            row["ted_file_id"],
            row["edit_run_id"],
            row["edit_run_rule_id"],
            row["created_at"],
        ))

    connection.execute("""
        DROP TABLE player_rule_applications
    """)

    connection.execute("""
        ALTER TABLE player_rule_applications_new
        RENAME TO player_rule_applications
    """)

    connection.execute("""
        CREATE INDEX idx_player_rule_applications_player
        ON player_rule_applications(player_id)
    """)

    connection.execute("""
        CREATE INDEX idx_player_rule_applications_rule_hash
        ON player_rule_applications(rule_hash)
    """)

    connection.execute("""
        CREATE INDEX idx_player_rule_applications_ted_rule
        ON player_rule_applications(
            first_ted_file_id,
            rule_hash
        )
    """)
