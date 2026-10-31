
def upgrade(connection):
    """Create team, coach, and TED file tables."""
    connection.execute("""
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            short_name TEXT,
            team_type TEXT NOT NULL
                CHECK (team_type IN ('club', 'national_team')),
            external_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE coaches (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE ted_files (
            id INTEGER PRIMARY KEY,
            import_id INTEGER NOT NULL,
            team_id INTEGER,
            coach_id INTEGER,
            file_name TEXT NOT NULL,
            relative_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (import_id)
                REFERENCES option_file_imports(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (team_id)
                REFERENCES teams(id)
                ON DELETE RESTRICT,

            FOREIGN KEY (coach_id)
                REFERENCES coaches(id)
                ON DELETE RESTRICT
        )
    """)

    connection.execute("""
        CREATE INDEX idx_ted_files_import_id
        ON ted_files(import_id)
    """)

    connection.execute("""
        CREATE INDEX idx_ted_files_team_id
        ON ted_files(team_id)
    """)

    connection.execute("""
        CREATE INDEX idx_ted_files_coach_id
        ON ted_files(coach_id)
    """)
