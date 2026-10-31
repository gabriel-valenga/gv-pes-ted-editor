
def upgrade(connection):
    """Create the initial Option File tables."""
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
