
import argparse
import logging
import struct
from pathlib import Path

from ted.crypto import decrypt_ted


logger = logging.getLogger("ted_inspector")


def find_all(data: bytes, pattern: bytes) -> list[int]:
    """Find all occurrences of a byte sequence."""
    offsets = []
    start = 0

    while True:
        offset = data.find(pattern, start)

        if offset == -1:
            break

        offsets.append(offset)
        start = offset + 1

    return offsets


def hex_context(
    data: bytes,
    offset: int,
    radius: int = 32,
) -> str:
    """Return a hexadecimal representation around an offset."""
    start = max(0, offset - radius)
    end = min(len(data), offset + radius)

    return " ".join(
        f"{byte:02X}"
        for byte in data[start:end]
    )


def inspect_pattern(
    data: bytes,
    label: str,
    pattern: bytes,
) -> None:
    """Log all occurrences of a pattern."""
    offsets = find_all(data, pattern)

    logger.info(
        "%s | pattern=%s | occurrences=%s",
        label,
        pattern.hex(" "),
        len(offsets),
    )

    for offset in offsets:
        logger.info(
            "%s found at offset decimal=%d hex=0x%X",
            label,
            offset,
            offset,
        )

        logger.info(
            "Context [%d:%d]: %s",
            max(0, offset - 16),
            min(len(data), offset + len(pattern) + 16),
            hex_context(data, offset, 16),
        )


def inspect_manager_id(
    data: bytes,
    manager_id: int,
) -> None:
    """Search for the manager ID in common integer formats."""
    formats = {
        "uint16_le": "<H",
        "uint32_le": "<I",
        "uint64_le": "<Q",
        "uint16_be": ">H",
        "uint32_be": ">I",
        "uint64_be": ">Q",
    }

    for label, fmt in formats.items():
        try:
            pattern = struct.pack(fmt, manager_id)
        except struct.error:
            continue

        inspect_pattern(
            data,
            f"Manager ID ({label})",
            pattern,
        )


def inspect_text(
    data: bytes,
    label: str,
    value: str,
) -> None:
    """Search for text in common encodings."""
    encodings = {
        "ascii": "ascii",
        "utf8": "utf-8",
        "utf16_le": "utf-16le",
        "utf16_be": "utf-16be",
    }

    for encoding_name, encoding in encodings.items():
        try:
            pattern = value.encode(encoding)
        except UnicodeEncodeError:
            continue

        inspect_pattern(
            data,
            f"{label} ({encoding_name})",
            pattern,
        )


def inspect_region(
    data: bytes,
    start: int,
    end: int,
) -> None:
    """Print bytes with their absolute offsets."""
    end = min(end, len(data))

    logger.info(
        "Detailed region: %d to %d",
        start,
        end,
    )

    for offset in range(start, end, 16):
        chunk = data[offset:min(offset + 16, end)]

        hex_values = " ".join(
            f"{byte:02X}"
            for byte in chunk
        )

        ascii_values = "".join(
            chr(byte) if 32 <= byte <= 126 else "."
            for byte in chunk
        )

        logger.info(
            "%04X | %-47s | %s",
            offset,
            hex_values,
            ascii_values,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect manager fields in a decrypted PES TED file."
    )

    parser.add_argument(
        "ted_file",
        type=Path,
        help="Path to the original TED file.",
    )

    parser.add_argument(
        "--manager-id",
        type=int,
        default=262625,
    )

    parser.add_argument(
        "--association",
        default="ITA",
    )

    parser.add_argument(
        "--manager-name",
        default="ENZO MARESCA",
    )

    parser.add_argument(
        "--region-start",
        type=lambda value: int(value, 0),
        default=640,
    )

    parser.add_argument(
        "--region-end",
        type=lambda value: int(value, 0),
        default=740,
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    ted_path = args.ted_file

    if not ted_path.is_file():
        logger.error("TED file not found: %s", ted_path)
        return

    logger.info("Reading TED: %s", ted_path)

    original_raw = ted_path.read_bytes()

    logger.info(
        "Original file size: %d bytes",
        len(original_raw),
    )

    logger.info("Decrypting TED...")

    decrypted_data = decrypt_ted(original_raw)

    logger.info(
        "Decrypted data size: %d bytes",
        len(decrypted_data),
    )

    logger.info("=" * 70)
    logger.info("SEARCHING MANAGER ID")
    logger.info("=" * 70)

    inspect_manager_id(
        decrypted_data,
        args.manager_id,
    )

    logger.info("=" * 70)
    logger.info("SEARCHING MANAGER ASSOCIATION")
    logger.info("=" * 70)

    inspect_text(
        decrypted_data,
        "Manager association",
        args.association,
    )

    logger.info("=" * 70)
    logger.info("SEARCHING MANAGER NAME")
    logger.info("=" * 70)

    inspect_text(
        decrypted_data,
        "Manager name",
        args.manager_name,
    )

    logger.info("=" * 70)
    logger.info("DETAILED MANAGER REGION")
    logger.info("=" * 70)

    inspect_region(
        decrypted_data,
        start=args.region_start,
        end=args.region_end,
    )

    logger.info("=" * 70)
    logger.info("INSPECTION COMPLETED")


if __name__ == "__main__":
    main()
