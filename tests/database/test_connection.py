
import sqlite3

from database.connection import get_connection


def test_get_connection_creates_database(tmp_path):
    database_path = tmp_path / "database" / "test.db"

    connection = get_connection(database_path)

    assert database_path.exists()
    assert isinstance(connection, sqlite3.Connection)

    connection.close()


def test_connection_uses_row_factory(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    assert connection.row_factory == sqlite3.Row

    connection.close()


def test_connection_enables_foreign_keys(tmp_path):
    connection = get_connection(tmp_path / "test.db")

    result = connection.execute("PRAGMA foreign_keys").fetchone()

    assert result[0] == 1

    connection.close()
