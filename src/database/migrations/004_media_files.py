
def upgrade(connection):
    """Create the media files table."""
    connection.execute("""
        CREATE TABLE media_files (
            id INTEGER PRIMARY KEY,
            ted_file_id INTEGER,
            file_name TEXT NOT NULL,
            media_type TEXT NOT NULL,
            purpose TEXT,
            content BLOB NOT NULL,
            sha256 TEXT NOT NULL
                CHECK (length(sha256) = 64),
            created_at TEXT NOT NULL,

            FOREIGN KEY (ted_file_id)
                REFERENCES ted_files(id)
                ON DELETE RESTRICT
        )
    """)

    connection.execute("""
        CREATE INDEX idx_media_files_ted_file_id
        ON media_files(ted_file_id)
    """)

    connection.execute("""
        CREATE INDEX idx_media_files_sha256
        ON media_files(sha256)
    """)
