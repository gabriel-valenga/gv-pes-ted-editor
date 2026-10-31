
#!/usr/bin/env python3
# PES GV - PES 2021 TED logical reader/editor
# Applies editing rules to one or more TED files.
# Only explicitly edited fields should be modified.

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from editing.players.operations import apply_edit
from editing.players.rules import load_rules, apply_rules
from ted.crypto import decrypt_ted, encrypt_ted
from ted.fields import PLAYER_FIELDS
from ted.reader import (
    EXPECTED_TED_SIZE,
    extract_player_field,
    extract_players,
    get_team_summary,
)
from ted.writer import save_ted, validate_ted_round_trip


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


def main():
    parser = argparse.ArgumentParser(
        description="Read and edit one or more PES 2021 TED files."
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
        help="Process all .ted files inside '_ted' directories of an Option File.",
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

    # Validate processing modes.
    if args.option_file and (args.ted or args.input_dir):
        parser.error(
            "Use --option-file, positional TED paths, or --input-dir, not multiple modes."
        )

    if args.in_place and not args.option_file:
        parser.error("--in-place can only be used with --option-file.")

    if args.option_file and args.out:
        parser.error("--out cannot be used with --option-file.")

    if args.option_file and not args.in_place and not args.output_dir:
        parser.error(
            "--option-file requires --in-place or --output-dir."
        )

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
    if args.option_file:
        option_file_dir = Path(args.option_file)

        if not option_file_dir.is_dir():
            parser.error(
                f"Option File directory does not exist: {option_file_dir}"
            )

        ted_files = find_option_file_teds(option_file_dir)

        if not ted_files:
            parser.error(
                f"No TED files found inside '_ted' directories: {option_file_dir}"
            )

    elif args.input_dir:
        input_dir = Path(args.input_dir)

        if not input_dir.is_dir():
            parser.error(f"Input directory does not exist: {input_dir}")

        ted_files = sorted(
            path for path in input_dir.iterdir()
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

        if args.option_file:
            resolved_option_file_dir = Path(args.option_file).resolve()

            # Prevent output files from being created inside the source Option File.
            if resolved_output_dir.is_relative_to(resolved_option_file_dir):
                parser.error(
                    "The output directory must not be inside the source Option File directory."
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

    results = []
    failures = []

    for ted_file in ted_files:

        # Determine the destination path.
        if args.in_place:
            output_path = ted_file

        elif output_dir:
            if args.option_file:
                relative_path = ted_file.relative_to(Path(args.option_file))
                output_path = output_dir / relative_path
            else:
                output_path = output_dir / ted_file.name

        elif args.out:
            output_path = Path(args.out)

        else:
            output_path = None

        decrypted_path = Path(args.decrypted) if args.decrypted else None

        try:
            result = process_ted(
                ted_path=ted_file,
                rules_list=rules_list,
                output_path=output_path,
                manual_edits=args.set,
                decrypted_path=decrypted_path,
            )

            results.append(result)

            if args.json_out:
                Path(args.json_out).write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"JSON saved: {args.json_out}")

        except Exception as exc:
            failures.append({
                "sourceFile": str(ted_file),
                "error": str(exc),
            })

            print(f"ERROR processing {ted_file.name}: {exc}")

    if not args.json_out:
        print(json.dumps({
            "processedCount": len(results),
            "failureCount": len(failures),
            "results": results,
            "failures": failures,
        }, ensure_ascii=False, indent=2))

    print(
        f"Finished: {len(results)} succeeded, "
        f"{len(failures)} failed out of {len(ted_files)} TED files."
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
