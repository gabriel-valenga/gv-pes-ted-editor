from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from database.connection import get_connection
from database.migration_runner import migrate_database
from database.repositories.coach_repository import (
    create_coach,
    get_coach_by_external_id,
)
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.player_record_repository import (
    create_player_record,
)
from database.repositories.team_repository import create_team
from database.repositories.ted_file_repository import create_ted_file
from database.repositories.ted_version_repository import create_ted_version
from ted.crypto import decrypt_ted
from ted.reader import (
    EXPECTED_TED_SIZE,
    extract_players,
    get_team_summary,
)
from ted.team_classifier import classify_team


def find_option_file_teds(option_file_dir: Path) -> list[Path]:
    """Find all TED files recursively inside an Option File directory."""
    return sorted(
        path
        for path in option_file_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".ted"
    )


def _normalize_short_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    value = value.strip()
    return value or None


def _find_existing_team(
    connection: sqlite3.Connection,
    name: str,
    short_name: str | None,
    team_type: str,
) -> sqlite3.Row | None:
    """Find a team using its name, short name, and type."""
    return connection.execute(
        """
        SELECT *
        FROM teams
        WHERE name = ?
          AND short_name IS ?
          AND team_type = ?
        ORDER BY id
        LIMIT 1
        """,
        (name, short_name, team_type),
    ).fetchone()


def _resolve_team(
    connection: sqlite3.Connection,
    team_summary: dict[str, Any],
) -> int | None:
    """Find or create a team without modifying existing records."""
    name = team_summary.get("teamName")

    if not isinstance(name, str) or not name.strip():
        return None

    name = name.strip()
    short_name = _normalize_short_name(
        team_summary.get("shortName")
    )

    team_type = classify_team(
        team_name=name,
        country_id=team_summary.get("countryId"),
    )

    existing_team = _find_existing_team(
        connection=connection,
        name=name,
        short_name=short_name,
        team_type=team_type,
    )

    if existing_team is not None:
        return existing_team["id"]

    return create_team(
        connection=connection,
        name=name,
        short_name=short_name,
        team_type=team_type,
    )


def _resolve_coach(
    connection: sqlite3.Connection,
    team_summary: dict[str, Any],
) -> int | None:
    """Find or create a coach using the manager ID."""
    manager_id = team_summary.get("managerId")

    if (
        not isinstance(manager_id, int)
        or isinstance(manager_id, bool)
        or manager_id <= 0
    ):
        return None

    external_id = str(manager_id)

    existing_coach = get_coach_by_external_id(
        connection,
        external_id,
    )

    if existing_coach is not None:
        return existing_coach["id"]

    name = team_summary.get("managerName")

    if not isinstance(name, str) or not name.strip():
        name = f"Unknown coach #{manager_id}"
    else:
        name = name.strip()

    return create_coach(
        connection=connection,
        name=name,
        external_id=external_id,
    )


def _prepare_player_data(player: dict[str, Any]) -> tuple[int, dict]:
    """Remove extraction metadata and prepare fields for database storage."""
    player_index = player.get("index")

    if not isinstance(player_index, int) or isinstance(player_index, bool):
        raise ValueError(
            f"Invalid player index: {player_index!r}"
        )

    data = {}

    for field_name, value in player.items():
        if field_name in {"index", "_recordOffset"}:
            continue

        if isinstance(value, dict) and "read_error" in value:
            continue

        if field_name == "playerAppearance":
            if value is None:
                data[field_name] = None
            elif isinstance(value, bytes):
                data[field_name] = value
            elif isinstance(value, bytearray):
                data[field_name] = bytes(value)
            elif isinstance(value, str):
                try:
                    data[field_name] = bytes.fromhex(value)
                except ValueError as exc:
                    raise ValueError(
                        "Invalid hexadecimal playerAppearance "
                        f"for player index {player_index}."
                    ) from exc
            else:
                raise TypeError(
                    "Unsupported playerAppearance type: "
                    f"{type(value).__name__}"
                )

            appearance = data[field_name]
            if appearance is not None and len(appearance) != 72:
                raise ValueError(
                    "Invalid playerAppearance length for player "
                    f"index {player_index}: {len(appearance)} bytes."
                )
        else:
            data[field_name] = value

    return player_index, data


def import_option_file(
    option_file_dir: str | Path,
    database_path: str | Path,
) -> dict[str, Any]:
    """
    Import all TED files from an Option File into the database.

    The complete import is executed in one transaction. If any TED fails,
    all database changes from this import are rolled back.
    """
    option_file_dir = Path(option_file_dir).resolve()
    database_path = Path(database_path).resolve()

    if not option_file_dir.is_dir():
        raise NotADirectoryError(
            f"Option File directory does not exist: {option_file_dir}"
        )

    ted_files = find_option_file_teds(option_file_dir)

    if not ted_files:
        raise FileNotFoundError(
            f"No TED files found inside: {option_file_dir}"
        )

    connection = get_connection(database_path)

    try:
        migrate_database(connection)

        imported_players = 0
        imported_teds = 0
        warnings = []

        # All import records and TED data belong to one transaction.
        with connection:
            option_file_id = create_option_file(
                connection,
                name=option_file_dir.name,
            )

            import_id = create_option_file_import(
                connection,
                option_file_id=option_file_id,
                source_path=option_file_dir,
            )

            for ted_path in ted_files:
                try:
                    original_raw = ted_path.read_bytes()

                    if len(original_raw) != EXPECTED_TED_SIZE:
                        warnings.append(
                            f"{ted_path.name}: file size is "
                            f"{len(original_raw)} bytes; expected "
                            f"{EXPECTED_TED_SIZE}."
                        )

                    decrypted_data = decrypt_ted(original_raw)
                    team_summary = get_team_summary(decrypted_data)
                    players = extract_players(decrypted_data)

                    team_id = _resolve_team(
                        connection,
                        team_summary,
                    )

                    coach_id = _resolve_coach(
                        connection,
                        team_summary,
                    )

                    relative_path = ted_path.relative_to(
                        option_file_dir
                    ).as_posix()

                    ted_file_id = create_ted_file(
                        connection=connection,
                        import_id=import_id,
                        file_name=ted_path.name,
                        team_id=team_id,
                        coach_id=coach_id,
                        relative_path=relative_path,
                    )

                    create_ted_version(
                        connection=connection,
                        ted_file_id=ted_file_id,
                        version_number=1,
                        version_type="original",
                        content=original_raw,
                    )

                    for player in players:
                        player_index, player_data = _prepare_player_data(
                            player
                        )

                        create_player_record(
                            connection=connection,
                            ted_file_id=ted_file_id,
                            player_index=player_index,
                            data=player_data,
                        )

                        imported_players += 1

                    imported_teds += 1

                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to import TED file "
                        f"{ted_path.relative_to(option_file_dir)}: {exc}"
                    ) from exc

        return {
            "optionFile": str(option_file_dir),
            "optionFileId": option_file_id,
            "importId": import_id,
            "database": str(database_path),
            "importedTedCount": imported_teds,
            "importedPlayerCount": imported_players,
            "warnings": warnings,
        }

    finally:
        connection.close()
