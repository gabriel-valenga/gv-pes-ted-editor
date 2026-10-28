#!/usr/bin/env python3
# PES GV - PES 2021 TED logical reader/editor
# Phase 1: player record fields extracted from TEditor's Jd schema.
# Does not rebuild records: modifies only the bytes of the fields that are explicitly edited.

from __future__ import annotations
import argparse
import json
from pathlib import Path
from editing.operations import apply_edit
from ted.crypto import decrypt_ted, encrypt_ted
from ted.fields import PLAYER_FIELDS
from ted.reader import EXPECTED_TED_SIZE, extract_player_field, extract_players, get_team_summary
from ted.writer import save_ted, validate_ted_round_trip


def main():
    parser = argparse.ArgumentParser(description="Reads and edits player fields in PES 2021 TED files.")
    parser.add_argument("ted", nargs="?", help="Path to the encrypted .ted file")
    parser.add_argument("--json", dest="json_out", help="Save JSON dump of read operation")
    parser.add_argument("--decrypted", help="Save decrypted buffer for debugging")
    parser.add_argument("--set", action="append", default=[], metavar="INDEX:FIELD=VALUE",
                        help='Edit field. Ex.: --set "0:speed=90" ou --set "0:playerName=Gabriel Valenga"')
    parser.add_argument("--out", help="Save the edited, encrypted TED (use a copy for testing)")
    parser.add_argument("--list-fields", action="store_true", help="List the recognized player fields")
    args = parser.parse_args()

    if args.list_fields:
        print(json.dumps(PLAYER_FIELDS, ensure_ascii=False, indent=2))
        if not args.ted:
            return

    if not args.ted:
        parser.error("Specify the TED path, or use --list-fields.")
    path = Path(args.ted)
    original_raw = path.read_bytes()
    if len(original_raw) != EXPECTED_TED_SIZE:
        print(f"NOTICE: size {len(original_raw)} bytes; original script expected {EXPECTED_TED_SIZE}.")
    data = decrypt_ted(original_raw)

    if args.decrypted:
        Path(args.decrypted).write_bytes(data)
        print(f"Decrypted debug buffer saved in: {args.decrypted}")

    edits = []
    for edit in args.set:
        try:
            left, value = edit.split("=", 1)
            index_text, field_name = left.split(":", 1)
            index = int(index_text)
            before = extract_player_field(data, index, field_name)
            apply_edit(data, index, field_name, value)
            after = extract_player_field(data, index, field_name)
            edits.append({"index": index, "field": field_name, "before": before, "after": after})
        except Exception as exc:
            parser.error(f"Failed to apply --set {edit!r}: {exc}")

    if args.out:
        save_ted(path_to_save=args.out, data=data, original_raw=original_raw)
        validate_ted_round_trip(encrypted_ted=encrypt_ted, data=data)
    result = {
        "sourceFile": str(path),
        "fileSize": len(original_raw),
        "team": get_team_summary(data),
        "playerCount": len(extract_players(data)),
        "players": extract_players(data),
        "edits": edits,
        "notes": [
            "The values presented apply the getter conversions from the TEditor player schema, where identified.",
            "playerAppearance is exposed as hexadecimal bytes; the internal structure has yet to be decoded.",
            "TEditor OVR, full tactics, and complete team fields are not yet implemented at this stage." 
        ]
    }
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON saved to: {args.json_out}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        

if __name__ == "__main__":
    main()
