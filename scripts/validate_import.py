import hashlib
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "database.db"

OPTION_FILE = Path(
    r"C:\Users\gabri\Downloads\retedsparateste129102026\teste teds estado original patch bmpes 25-26 - teste alteracao 01-11"
)

IMPORT_ID = 1

connection = sqlite3.connect(DATABASE_PATH)
connection.row_factory = sqlite3.Row

try:
    rows = connection.execute(
        """
        SELECT
            tf.file_name,
            tf.relative_path,
            tv.sha256,
            tv.content
        FROM ted_files tf
        JOIN ted_versions tv
            ON tv.ted_file_id = tf.id
        WHERE tf.import_id = ?
          AND tv.version_type = 'original'
        ORDER BY tf.relative_path
        """,
        (IMPORT_ID,),
    ).fetchall()

    for row in rows:
        original_path = OPTION_FILE / row["relative_path"]
        original_hash = hashlib.sha256(
            original_path.read_bytes()
        ).hexdigest()

        stored_hash = hashlib.sha256(
            row["content"]
        ).hexdigest()

        valid = (
            original_hash == stored_hash
            and stored_hash == row["sha256"]
        )

        print(
            f"{'OK' if valid else 'FAIL'} | "
            f"{row['relative_path']}"
        )

finally:
    connection.close()
    