import argparse
import hashlib
import json
import sys
from pathlib import Path

# Allow importing project modules when running this script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ted.crypto import decrypt_ted
from ted.reader import (
    EXPECTED_TED_SIZE,
    MAX_PLAYERS,
    PLAYER_RECORD_LEN,
    PLAYERS_START,
    extract_players,
    get_team_summary,
)


def generate_dump(ted_path: Path) -> dict:
    original_data = ted_path.read_bytes()
    decrypted_data = decrypt_ted(original_data)

    players = extract_players(decrypted_data)
    team = get_team_summary(decrypted_data)

    player_records = []

    for player in players:
        player_index = player["index"]
        offset = PLAYERS_START + player_index * PLAYER_RECORD_LEN

        raw_record = decrypted_data[
            offset:offset + PLAYER_RECORD_LEN
        ]

        player_records.append({
            "index": player_index,
            "offset": offset,
            "fields": {
                key: value
                for key, value in player.items()
                if key != "_recordOffset"
            },
            "raw_hex": raw_record.hex(),
        })

    return {
        "file": {
            "name": ted_path.name,
            "size": len(original_data),
            "expected_size": EXPECTED_TED_SIZE,
            "size_matches_expected": len(original_data) == EXPECTED_TED_SIZE,
            "sha256": hashlib.sha256(original_data).hexdigest(),
        },
        "header": {
            "original_hex": original_data[:80].hex(),
            "decrypted_hex": decrypted_data[:80].hex(),
        },
        "structure": {
            "players_start": PLAYERS_START,
            "player_record_length": PLAYER_RECORD_LEN,
            "max_players": MAX_PLAYERS,
            "extracted_player_count": len(players),
        },
        "team": team,
        "players": player_records,
        "raw_data": {
            "decrypted_hex": decrypted_data.hex(),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a JSON dump from a PES 2021 TED file."
    )

    parser.add_argument(
        "ted_file",
        type=Path,
        help="Path to the TED file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON path.",
    )

    args = parser.parse_args()

    if not args.ted_file.is_file():
        parser.error(f"TED file not found: {args.ted_file}")

    output_path = args.output or args.ted_file.with_suffix(".dump.json")

    try:
        dump = generate_dump(args.ted_file)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(
            json.dumps(dump, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Dump generated: {output_path}")
        print(f"File size: {dump['file']['size']} bytes")
        print(f"Players extracted: {dump['structure']['extracted_player_count']}")
        print(f"SHA-256: {dump['file']['sha256']}")

    except Exception as exc:
        parser.error(f"Failed to generate dump: {exc}")


if __name__ == "__main__":
    main()
    