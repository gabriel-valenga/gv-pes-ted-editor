
#!/usr/bin/env python3
# PES GV - PES 2021 TED logical reader/editor
# Applies editing rules to one or more TED files.
# Only explicitly edited fields should be modified.

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path

from editing.players.operations import apply_edit
from editing.players.rules import (
    load_rules,
    apply_rules,
    build_rule_hash,
)
from ted.crypto import decrypt_ted, encrypt_ted
from ted.fields import PLAYER_FIELDS
from ted.reader import (
    EXPECTED_TED_SIZE,
    extract_player_field,
    extract_players,
    get_team_summary,
)
from ted.writer import save_ted, validate_ted_round_trip
from database.connection import get_connection
from database.importer import import_option_file
from database.migration_runner import migrate_database
from database.repositories.editing_history_repository import (
    create_edit_run,
    create_edit_run_rule,
    create_edit_run_ted_file,
    create_edit_change,
    update_edit_run_status,
    update_edit_run_ted_file,
)
from database.repositories.ted_version_repository import (
    create_ted_version,
    get_latest_ted_version,
)


def find_option_file_teds(option_file_dir: Path) -> list[Path]:
    """Find all TED files recursively inside an Option File directory."""
    return sorted(
        path
        for path in option_file_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".ted"
    )


def process_ted(
    ted_path: Path,
    rules_list: list[dict],
    output_path: Path | None = None,
    manual_edits: list[str] | None = None,
    decrypted_path: Path | None = None,
) -> dict:
    """Read a TED file, apply all rules, and optionally save the result."""

    original_raw = ted_path.read_bytes()

    if len(original_raw) != EXPECTED_TED_SIZE:
        print(
            f"NOTICE: {ted_path.name}: file size is {len(original_raw)} bytes; "
            f"expected {EXPECTED_TED_SIZE}."
        )

    data = decrypt_ted(original_raw)

    if decrypted_path:
        decrypted_path.parent.mkdir(parents=True, exist_ok=True)
        decrypted_path.write_bytes(data)
        print(f"Decrypted debug buffer saved: {decrypted_path}")

    edits = []

    # Apply every configuration to this TED in the specified order.
    for rule_index, rules in enumerate(rules_list, start=1):
        rule_edits = apply_rules(data, rules)
        edits.extend(rule_edits)

        print(
            f"{ted_path.name}: rule {rule_index}/{len(rules_list)} "
            f"applied ({len(rule_edits)} changes)."
        )

    # Apply manual edits after all configuration rules.
    for edit in manual_edits or []:
        try:
            left, value = edit.split("=", 1)
            index_text, field_name = left.split(":", 1)
            index = int(index_text)

            before = extract_player_field(data, index, field_name)
            apply_edit(data, index, field_name, value)
            after = extract_player_field(data, index, field_name)

            edits.append({
                "index": index,
                "field": field_name,
                "before": before,
                "after": after,
                "source": "manual",
            })

        except Exception as exc:
            raise ValueError(
                f"Failed to apply manual edit {edit!r} "
                f"to {ted_path.name}: {exc}"
            ) from exc

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        encrypted_ted_file = encrypt_ted(data, original_raw)

        # Validate the encrypted data before writing or replacing the file.
        validate_ted_round_trip(
            encrypted_ted_file=encrypted_ted_file,
            data=data,
        )

        # Create a unique temporary file in the destination directory.
        file_descriptor, temp_file = tempfile.mkstemp(
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
        )

        os.close(file_descriptor)
        temp_output_path = Path(temp_file)

        try:
            save_ted(
                path_to_save=str(temp_output_path),
                encrypted_ted_file=encrypted_ted_file,
            )

            # Replace the destination only after successful validation and writing.
            os.replace(temp_output_path, output_path)

        finally:
            if temp_output_path.exists():
                temp_output_path.unlink()

        print(f"TED saved: {output_path}")

    players = extract_players(data)

    return {
        "sourceFile": str(ted_path),
        "outputFile": str(output_path) if output_path else None,
        "fileSize": len(original_raw),
        "rulesApplied": len(rules_list),
        "team": get_team_summary(data),
        "playerCount": len(players),
        "players": players,
        "edits": edits,
        "notes": [
            "Only explicitly edited player fields are intended to change.",
            "playerAppearance is exposed as hexadecimal bytes; its internal structure has not yet been decoded.",
            "TEditor OVR, full tactics, and complete team fields are not yet implemented.",
        ],
    }


def _get_database_path() -> Path:
    """Return the project database path."""
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data" / "database.db"


def _find_registered_ted(
    connection: sqlite3.Connection,
    ted_path: Path,
    option_file_dir: Path | None,
) -> sqlite3.Row | None:
    """Find a TED file in the most recent matching Option File import."""

    if option_file_dir is None:
        return None

    option_file_dir = option_file_dir.resolve()
    ted_path = ted_path.resolve()

    try:
        relative_path = ted_path.relative_to(option_file_dir).as_posix()
    except ValueError:
        return None

    return connection.execute(
        """
        SELECT
            tf.id AS ted_file_id,
            tf.import_id,
            tf.relative_path,
            ofi.source_path,
            ofi.imported_at
        FROM ted_files AS tf
        JOIN option_file_imports AS ofi
            ON ofi.id = tf.import_id
        WHERE ofi.source_path = ?
          AND tf.relative_path = ?
        ORDER BY ofi.imported_at DESC, ofi.id DESC
        LIMIT 1
        """,
        (
            str(option_file_dir),
            relative_path,
        ),
    ).fetchone()


def _build_rule_records(
    connection: sqlite3.Connection,
    edit_run_id: int,
    rules_list: list[dict],
) -> dict[str, int]:
    """Register rules and map their hashes to database IDs."""

    rule_ids_by_hash = {}
    rule_order = 0

    for config in rules_list:
        for rule in config.get("rules", []):
            rule_order += 1

            rule_hash = build_rule_hash(rule)

            rule_id = create_edit_run_rule(
                connection=connection,
                edit_run_id=edit_run_id,
                rule_order=rule_order,
                rule=rule,
                rule_name=rule.get("name"),
            )

            connection.execute(
                """
                UPDATE edit_run_rules
                SET rule_hash = ?
                WHERE id = ?
                """,
                (rule_hash, rule_id),
            )

            rule_ids_by_hash.setdefault(rule_hash, rule_id)

    return rule_ids_by_hash


def _prepare_rules_for_ted(
    connection: sqlite3.Connection,
    ted_path: Path,
    rules_list: list[dict],
) -> list[dict]:
    """
    Exclude players that already received the same rule in a previous TED.
    """
    encrypted_content = ted_path.read_bytes()
    decrypted_data = decrypt_ted(encrypted_content)
    players = extract_players(decrypted_data)

    player_ids = {
        player.get("playerId")
        for player in players
        if isinstance(player.get("playerId"), int)
    }

    prepared_rules = []

    for config in rules_list:
        prepared_config = copy.deepcopy(config)
        prepared_config["rules"] = []

        for rule in config.get("rules", []):
            prepared_rule = copy.deepcopy(rule)

            if not rule.get("enabled", False):
                prepared_config["rules"].append(prepared_rule)
                continue

            rule_hash = build_rule_hash(rule)

            applied_rows = connection.execute(
                """
                SELECT player_id
                FROM player_rule_applications
                WHERE rule_hash = ?
                """,
                (rule_hash,),
            ).fetchall()

            blocked_player_ids = {
                row["player_id"]
                for row in applied_rows
            }

            allowed_player_ids = player_ids - blocked_player_ids

            # Preserve an existing player ID restriction.
            if "playerIds" in rule:
                allowed_player_ids &= set(rule["playerIds"])

            prepared_rule["playerIds"] = sorted(
                allowed_player_ids
            )

            # Preserve the original rule identity after filtering.
            prepared_rule["_originalRuleHash"] = rule_hash

            prepared_config["rules"].append(prepared_rule)

        prepared_rules.append(prepared_config)

    return prepared_rules


def _get_source_version_id(
    connection: sqlite3.Connection,
    ted_file_id: int,
    source_content: bytes,
) -> int | None:
    """Find the database version matching the current source file."""

    source_hash = hashlib.sha256(source_content).hexdigest()

    row = connection.execute(
        """
        SELECT id
        FROM ted_versions
        WHERE ted_file_id = ?
          AND sha256 = ?
        ORDER BY version_number DESC
        LIMIT 1
        """,
        (ted_file_id, source_hash),
    ).fetchone()

    return row["id"] if row else None


def _create_output_version(
    connection: sqlite3.Connection,
    ted_file_id: int,
    output_path: Path,
    source_content: bytes,
) -> int | None:
    """Create a new edited version when the output differs from the source."""

    if not output_path.is_file():
        return None

    output_content = output_path.read_bytes()

    output_hash = hashlib.sha256(output_content).hexdigest()
    source_hash = hashlib.sha256(source_content).hexdigest()

    if output_hash == source_hash:
        return None

    latest_version = get_latest_ted_version(
        connection,
        ted_file_id,
    )

    version_number = (
        latest_version["version_number"] + 1
        if latest_version
        else 1
    )

    return create_ted_version(
        connection=connection,
        ted_file_id=ted_file_id,
        version_number=version_number,
        version_type="edited",
        content=output_content,
    )


def _register_ted_edit_history(
    connection: sqlite3.Connection,
    edit_run_id: int,
    ted_file_id: int,
    source_version_id: int | None,
    result: dict,
    output_path: Path | None,
    source_content: bytes,
    rule_ids_by_hash: dict[str, int],
) -> None:
    """Persist one TED editing result inside the current transaction."""

    run_ted_file_id = create_edit_run_ted_file(
        connection=connection,
        edit_run_id=edit_run_id,
        ted_file_id=ted_file_id,
        status="pending",
        source_version_id=source_version_id,
    )

    output_version_id = None

    if output_path is not None:
        output_version_id = _create_output_version(
            connection=connection,
            ted_file_id=ted_file_id,
            output_path=output_path,
            source_content=source_content,
        )

    players_by_index = {
        player.get("index"): player
        for player in result.get("players", [])
        if isinstance(player.get("index"), int)
    }

    successful_applications = {}

    for edit in result.get("edits", []):
        player_index = edit.get(
            "playerIndex",
            edit.get("index"),
        )

        if not isinstance(player_index, int):
            continue

        field_name = edit.get("field")

        if not isinstance(field_name, str):
            continue

        player = players_by_index.get(player_index, {})
        player_id = edit.get("playerId", player.get("playerId"))

        rule_id = None
        rule_hash = None

        if edit.get("source") == "rule":
            rule_hash = edit.get("ruleHash")

            if isinstance(rule_hash, str):
                rule_id = rule_ids_by_hash.get(rule_hash)

        create_edit_change(
            connection=connection,
            run_ted_file_id=run_ted_file_id,
            player_index=player_index,
            field_name=field_name,
            old_value=edit.get("before"),
            new_value=edit.get("after"),
            player_id=player_id,
            rule_id=rule_id,
        )

        if (
            isinstance(player_id, int)
            and isinstance(rule_hash, str)
            and rule_id is not None
        ):
            successful_applications[
                (player_id, rule_hash)
            ] = rule_id

    # Persist only rules that effectively changed a player.
    for (player_id, rule_hash), rule_id in successful_applications.items():
        connection.execute(
            """
            INSERT OR IGNORE INTO player_rule_applications (
                player_id,
                rule_hash,
                first_ted_file_id,
                first_edit_run_id,
                first_edit_run_rule_id,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?,
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            )
            """,
            (
                player_id,
                rule_hash,
                ted_file_id,
                edit_run_id,
                rule_id,
            ),
        )

    update_edit_run_ted_file(
        connection=connection,
        run_ted_file_id=run_ted_file_id,
        status="completed",
        source_version_id=source_version_id,
        output_version_id=output_version_id,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Read, edit, and import PES 2021 TED files."
    )

    parser.add_argument(
        "ted",
        nargs="*",
        help="One or more encrypted TED file paths.",
    )
    parser.add_argument(
        "--input-dir",
        help="Process all .ted files in this directory (non-recursively).",
    )
    parser.add_argument(
        "--option-file",
        help="Process all .ted files inside an Option File directory.",
    )
    parser.add_argument(
        "--import-db",
        action="store_true",
        help="Import an Option File into the database without editing TED files.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Replace original TED files after successful processing and validation.",
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        metavar="JSON",
        help="JSON rules file. Can be specified multiple times, in order.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for processed TED files. Original filenames are preserved.",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        help="Save the JSON result. Only available when processing one TED file.",
    )
    parser.add_argument(
        "--decrypted",
        help="Save the decrypted buffer for debugging. Only available for one TED file.",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="INDEX:FIELD=VALUE",
        help='Manually edit a field. Example: --set "0:speed=90".',
    )
    parser.add_argument(
        "--out",
        help="Output path for a single TED file.",
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="List recognized player fields.",
    )

    args = parser.parse_args()

    # Database import mode is independent from the editing workflow.
    if args.import_db:
        if not args.option_file:
            parser.error("--import-db requires --option-file.")

        incompatible_options = []

        if args.ted:
            incompatible_options.append("positional TED paths")
        if args.input_dir:
            incompatible_options.append("--input-dir")
        if args.in_place:
            incompatible_options.append("--in-place")
        if args.config:
            incompatible_options.append("--config")
        if args.output_dir:
            incompatible_options.append("--output-dir")
        if args.json_out:
            incompatible_options.append("--json")
        if args.decrypted:
            incompatible_options.append("--decrypted")
        if args.set:
            incompatible_options.append("--set")
        if args.out:
            incompatible_options.append("--out")
        if args.list_fields:
            incompatible_options.append("--list-fields")

        if incompatible_options:
            parser.error(
                "--import-db cannot be combined with: "
                + ", ".join(incompatible_options)
            )

        option_file_dir = Path(args.option_file)

        if not option_file_dir.is_dir():
            parser.error(
                f"Option File directory does not exist: {option_file_dir}"
            )

        database_path = _get_database_path()

        try:
            result = import_option_file(
                option_file_dir=option_file_dir,
                database_path=database_path,
            )
        except Exception as exc:
            parser.error(f"Database import failed: {exc}")

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            "Database import finished: "
            f"{result['importedTedCount']} TED files and "
            f"{result['importedPlayerCount']} players imported."
        )

        for warning in result["warnings"]:
            print(f"NOTICE: {warning}")

        return

    # Validate regular processing modes.
    if args.option_file and (args.ted or args.input_dir):
        parser.error(
            "Use --option-file, positional TED paths, or --input-dir, "
            "not multiple modes."
        )

    if args.in_place and not args.option_file:
        parser.error("--in-place can only be used with --option-file.")

    if args.option_file and args.out:
        parser.error("--out cannot be used with --option-file.")

    if args.option_file and not args.in_place and not args.output_dir:
        parser.error("--option-file requires --in-place or --output-dir.")

    if args.option_file and args.in_place and args.output_dir:
        parser.error(
            "Use --in-place or --output-dir with --option-file, not both."
        )

    if args.output_dir and args.out:
        parser.error("Use --output-dir or --out, not both.")

    if args.ted and args.input_dir:
        parser.error("Use positional TED paths or --input-dir, not both.")

    # List recognized fields.
    if args.list_fields:
        print(json.dumps(PLAYER_FIELDS, ensure_ascii=False, indent=2))
        if not args.ted and not args.input_dir and not args.option_file:
            return

    # Discover input TED files.
    option_file_dir = None

    if args.option_file:
        option_file_dir = Path(args.option_file).resolve()

        if not option_file_dir.is_dir():
            parser.error(
                f"Option File directory does not exist: {option_file_dir}"
            )

        ted_files = find_option_file_teds(option_file_dir)

        if not ted_files:
            parser.error(
                f"No TED files found inside Option File: {option_file_dir}"
            )

    elif args.input_dir:
        input_dir = Path(args.input_dir)

        if not input_dir.is_dir():
            parser.error(f"Input directory does not exist: {input_dir}")

        ted_files = sorted(
            path
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".ted"
        )

    else:
        ted_files = [Path(path) for path in args.ted]

    if not ted_files:
        parser.error(
            "Specify at least one TED file or a directory containing TED files."
        )

    for ted_file in ted_files:
        if not ted_file.is_file():
            parser.error(f"TED file does not exist: {ted_file}")

    # Validate single-file output options.
    if args.out and len(ted_files) != 1:
        parser.error("--out can only be used when processing one TED file.")

    if args.json_out and len(ted_files) != 1:
        parser.error("--json can only be used when processing one TED file.")

    if args.decrypted and len(ted_files) != 1:
        parser.error("--decrypted can only be used when processing one TED file.")

    # Load each configuration once and reuse it for every TED file.
    rules_list = []

    for config_path in args.config:
        try:
            rules_list.append(load_rules(config_path))
        except (OSError, ValueError) as exc:
            parser.error(
                f"Failed to load configuration {config_path!r}: {exc}"
            )

    output_dir = Path(args.output_dir) if args.output_dir else None

    if output_dir:
        resolved_output_dir = output_dir.resolve()

        if option_file_dir:
            if resolved_output_dir.is_relative_to(option_file_dir):
                parser.error(
                    "The output directory must not be inside "
                    "the source Option File directory."
                )
        else:
            if any(
                ted_file.resolve().parent == resolved_output_dir
                for ted_file in ted_files
            ):
                parser.error(
                    "The output directory must not be the same directory "
                    "as an input TED file."
                )

        output_dir.mkdir(parents=True, exist_ok=True)

    database_path = _get_database_path()
    connection = None
    edit_run_id = None
    rule_ids_by_hash = {}
    registered_teds = {}

    # Database integration is optional for files that have not been imported.
    try:
        connection = get_connection(database_path)
        migrate_database(connection)

        for ted_file in ted_files:
            registered_ted = _find_registered_ted(
                connection=connection,
                ted_path=ted_file,
                option_file_dir=option_file_dir,
            )

            if registered_ted is not None:
                registered_teds[str(ted_file.resolve())] = registered_ted

        if registered_teds:
            run_config = {
                "command": "ted-edit",
                "optionFile": (
                    str(option_file_dir)
                    if option_file_dir
                    else None
                ),
                "configFiles": args.config,
                "manualEdits": args.set,
                "inPlace": args.in_place,
                "outputDir": (
                    str(output_dir.resolve())
                    if output_dir
                    else None
                ),
                "registeredTedCount": len(registered_teds),
            }

            with connection:
                edit_run_id = create_edit_run(
                    connection=connection,
                    config=run_config,
                    status="running",
                )

                rule_ids_by_hash = _build_rule_records(
                    connection=connection,
                    edit_run_id=edit_run_id,
                    rules_list=rules_list,
                )

            print(
                f"Database editing history enabled: run #{edit_run_id}."
            )

        else:
            connection.close()
            connection = None

    except Exception as exc:
        if connection is not None:
            connection.close()
            connection = None

        print(
            "NOTICE: Database history is unavailable. "
            f"TED editing will continue without database history: {exc}"
        )

    results = []
    failures = []

    for ted_file in ted_files:
        if args.in_place:
            output_path = ted_file

        elif output_dir:
            if option_file_dir:
                relative_path = ted_file.resolve().relative_to(
                    option_file_dir
                )
                output_path = output_dir / relative_path
            else:
                output_path = output_dir / ted_file.name

        elif args.out:
            output_path = Path(args.out)

        else:
            output_path = None

        decrypted_path = (
            Path(args.decrypted)
            if args.decrypted
            else None
        )

        try:
            source_content = ted_file.read_bytes()

            registered_ted = registered_teds.get(
                str(ted_file.resolve())
            )

            ted_rules_list = rules_list

            if (
                connection is not None
                and edit_run_id is not None
                and registered_ted is not None
            ):
                ted_rules_list = _prepare_rules_for_ted(
                    connection=connection,
                    ted_path=ted_file,
                    rules_list=rules_list,
                )

            result = process_ted(
                ted_path=ted_file,
                rules_list=ted_rules_list,
                output_path=output_path,
                manual_edits=args.set,
                decrypted_path=decrypted_path,
            )

            if (
                connection is not None
                and edit_run_id is not None
                and registered_ted is not None
            ):
                try:
                    with connection:
                        source_version_id = _get_source_version_id(
                            connection=connection,
                            ted_file_id=registered_ted["ted_file_id"],
                            source_content=source_content,
                        )

                        _register_ted_edit_history(
                            connection=connection,
                            edit_run_id=edit_run_id,
                            ted_file_id=registered_ted["ted_file_id"],
                            source_version_id=source_version_id,
                            result=result,
                            output_path=output_path,
                            source_content=source_content,
                            rule_ids_by_hash=rule_ids_by_hash,
                        )

                    result["databaseHistory"] = {
                        "registered": True,
                        "saved": True,
                        "tedFileId": registered_ted["ted_file_id"],
                        "editRunId": edit_run_id,
                        "sourceVersionId": source_version_id,
                    }

                except Exception as exc:
                    failures.append({
                        "sourceFile": str(ted_file),
                        "error": (
                            "TED was processed, but database history "
                            f"could not be saved: {exc}"
                        ),
                    })

                    print(
                        f"ERROR saving database history for "
                        f"{ted_file.name}: {exc}"
                    )

                    result["databaseHistory"] = {
                        "registered": True,
                        "saved": False,
                        "error": str(exc),
                    }

            elif registered_ted is None:
                result["databaseHistory"] = {
                    "registered": False,
                }

            results.append(result)

            if args.json_out:
                Path(args.json_out).write_text(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                print(f"JSON saved: {args.json_out}")

        except Exception as exc:
            failures.append({
                "sourceFile": str(ted_file),
                "error": str(exc),
            })

            print(f"ERROR processing {ted_file.name}: {exc}")

    if connection is not None and edit_run_id is not None:
        try:
            with connection:
                update_edit_run_status(
                    connection=connection,
                    edit_run_id=edit_run_id,
                    status="failed" if failures else "completed",
                )
        except Exception as exc:
            print(f"ERROR finalizing database edit run: {exc}")
            failures.append({
                "sourceFile": None,
                "error": f"Failed to finalize edit run: {exc}",
            })

    if connection is not None:
        connection.close()

    if not args.json_out:
        print(
            json.dumps(
                {
                    "processedCount": len(results),
                    "failureCount": len(failures),
                    "editRunId": edit_run_id,
                    "results": results,
                    "failures": failures,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    print(
        f"Finished: {len(results)} succeeded, "
        f"{len(failures)} failed out of {len(ted_files)} TED files."
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
