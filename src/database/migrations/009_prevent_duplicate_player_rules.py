
import hashlib
import json


def _build_rule_hash(rule_json: str) -> str:
    """Build a stable hash from the functional content of a rule."""
    rule = json.loads(rule_json)

    if not isinstance(rule, dict):
        raise ValueError("Invalid rule JSON: expected an object.")

    normalized_rule = {
        key: value
        for key, value in rule.items()
        if key not in {"name", "enabled"}
    }

    canonical_json = json.dumps(
        normalized_rule,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def upgrade(connection):
    """Add persistent tracking for rules already applied to players."""
    connection.execute("""
        ALTER TABLE edit_run_rules
        ADD COLUMN rule_hash TEXT
    """)

    connection.execute("""
        CREATE TABLE player_rule_applications (
            id INTEGER PRIMARY KEY,
            player_id INTEGER NOT NULL,
            rule_hash TEXT NOT NULL,
            first_ted_file_id INTEGER NOT NULL,
            first_edit_run_id INTEGER NOT NULL,
            first_edit_run_rule_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,

            UNIQUE (player_id, rule_hash),

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

    connection.execute("""
        CREATE INDEX idx_player_rule_applications_player
        ON player_rule_applications(player_id)
    """)

    connection.execute("""
        CREATE INDEX idx_player_rule_applications_rule_hash
        ON player_rule_applications(rule_hash)
    """)

    rules = connection.execute("""
        SELECT id, rule_json
        FROM edit_run_rules
        ORDER BY id
    """).fetchall()

    rule_hashes = {}

    for rule_id, rule_json in rules:
        try:
            rule_hash = _build_rule_hash(rule_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

        rule_hashes[rule_id] = rule_hash

        connection.execute("""
            UPDATE edit_run_rules
            SET rule_hash = ?
            WHERE id = ?
        """, (rule_hash, rule_id))

    historical_edits = connection.execute("""
        SELECT
            ec.player_id,
            ec.edit_run_rule_id,
            ertf.ted_file_id,
            ertf.edit_run_id,
            ec.created_at
        FROM edit_changes AS ec
        JOIN edit_run_ted_files AS ertf
            ON ertf.id = ec.edit_run_ted_file_id
        WHERE ec.player_id IS NOT NULL
          AND ec.edit_run_rule_id IS NOT NULL
        ORDER BY ec.created_at, ec.id
    """).fetchall()

    for (
        player_id,
        rule_id,
        ted_file_id,
        edit_run_id,
        created_at,
    ) in historical_edits:
        rule_hash = rule_hashes.get(rule_id)

        if rule_hash is None:
            continue

        connection.execute("""
            INSERT OR IGNORE INTO player_rule_applications (
                player_id,
                rule_hash,
                first_ted_file_id,
                first_edit_run_id,
                first_edit_run_rule_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            rule_hash,
            ted_file_id,
            edit_run_id,
            rule_id,
            created_at,
        ))
