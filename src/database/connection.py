
import sqlite3
from pathlib import Path


def get_connection(database_path: str | Path) -> sqlite3.Connection:
    """Create and configure a SQLite database connection."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection
