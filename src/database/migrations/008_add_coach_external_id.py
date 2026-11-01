def upgrade(connection):
    """Add an external identifier to coaches."""
    connection.execute("""
        ALTER TABLE coaches
        ADD COLUMN external_id TEXT
    """)

    connection.execute("""
        CREATE UNIQUE INDEX idx_coaches_external_id
        ON coaches(external_id)
        WHERE external_id IS NOT NULL
    """)
    