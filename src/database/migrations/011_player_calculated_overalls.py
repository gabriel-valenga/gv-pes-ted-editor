
import sqlite3


def upgrade(connection: sqlite3.Connection) -> None:
    """Create tables for calculated player Overalls."""

    connection.execute("""
        CREATE TABLE player_position_overalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_record_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            overall INTEGER NOT NULL,
            calculation_version TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_record_id)
                REFERENCES player_records(id)
                ON DELETE CASCADE,

            UNIQUE (
                player_record_id,
                position,
                calculation_version
            ),

            CHECK (
                position IN (
                    'GK', 'CB', 'LB', 'RB',
                    'DMF', 'CMF', 'LMF', 'RMF',
                    'AMF', 'LWF', 'RWF', 'SS', 'CF'
                )
            )
        )
    """)

    connection.execute("""
        CREATE TABLE player_registered_overalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_record_id INTEGER NOT NULL,
            registered_position TEXT NOT NULL,
            overall INTEGER NOT NULL,
            calculation_version TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_record_id)
                REFERENCES player_records(id)
                ON DELETE CASCADE,

            UNIQUE (
                player_record_id,
                calculation_version
            )
        )
    """)

    connection.execute("""
        CREATE INDEX idx_player_position_overalls_record
        ON player_position_overalls(player_record_id)
    """)

    connection.execute("""
        CREATE INDEX idx_player_registered_overalls_record
        ON player_registered_overalls(player_record_id)
    """)
