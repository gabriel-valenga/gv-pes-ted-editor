
def upgrade(connection):
    """Create the TED file versions table."""
    connection.execute("""
        CREATE TABLE ted_versions (
            id INTEGER PRIMARY KEY,
            ted_file_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            version_type TEXT NOT NULL
                CHECK (
                    version_type IN (
                        'original',
                        'edited',
                        'restored'
                    )
                ),
            content BLOB NOT NULL,
            sha256 TEXT NOT NULL
                CHECK (length(sha256) = 64),
            created_at TEXT NOT NULL,

            FOREIGN KEY (ted_file_id)
                REFERENCES ted_files(id)
                ON DELETE RESTRICT,

            UNIQUE (ted_file_id, version_number)
        )
    """)

    connection.execute("""
        CREATE INDEX idx_ted_versions_ted_file_id
        ON ted_versions(ted_file_id)
    """)

    connection.execute("""
        CREATE INDEX idx_ted_versions_sha256
        ON ted_versions(sha256)
    """)

    connection.execute("""
        CREATE UNIQUE INDEX idx_ted_versions_original
        ON ted_versions(ted_file_id)
        WHERE version_type = 'original'
    """)
