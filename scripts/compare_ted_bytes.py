
import struct
from pathlib import Path

from ted.crypto import decrypt_ted


FILES = {
    "Brasil": Path("SEL_UP_BRASIL.ted"),
    "Chelsea": Path("chelsea.ted"),
    "Argentina": Path("SEL_UP_ARGENTINA.ted"),
    "PSG": Path("FRA1_V28_PSG.ted"),
    "MONACO": Path("FRA1_V28_MONACO.ted"),
    "DIJON": Path("FRA2_V28_DIJON.ted"),
    "METZ": Path("FRA2_V28_METZ.ted"),
    "ATLETICO MINEIRO": Path("A-BRA_V28_ATLETICO.ted"),
    "CHAPECOENSE": Path("A-BRA_V28_CHAPE.ted"),
    "ELCHE": Path("ESP1_V28_ELCHE.ted"),
    "RAYO": Path("ESP1_V28_RAYO.ted")
}

START = 80
END = 184


def load_decrypted_files():
    """Load and decrypt all TED files."""
    decrypted = {}

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Ted file not found: {path.resolve()}"
            )

        raw = path.read_bytes()
        decrypted[name] = decrypt_ted(raw)

    return decrypted


def compare_bytes(decrypted):
    """Print byte-by-byte differences."""
    print("\nBYTE-BY-BYTE COMPARISON")

    names = list(decrypted.keys())

    print(f"{'OFFSET':<10}", end="")
    for name in names:
        print(f"{name:<14}", end="")
    print("DIFFERENT")

    print("-" * (10 + 14 * len(names) + 12))

    for offset in range(START, END):
        values = [
            decrypted[name][offset]
            for name in names
        ]

        different = len(set(values)) > 1

        print(f"0x{offset:04X}   ", end="")

        for value in values:
            print(f"{value:02X}{'':<12}", end="")

        print("*" if different else "")


def compare_16bit(decrypted):
    """Compare 16-bit unsigned integers."""
    print("\n16-BIT UNSIGNED INTEGERS")
    print("-" * 80)

    names = list(decrypted.keys())

    for offset in range(START, END - 1, 2):
        values = {
            name: struct.unpack_from(
                "<H",
                decrypted[name],
                offset,
            )[0]
            for name in names
        }

        if len(set(values.values())) > 1:
            result = " | ".join(
                f"{name}={value}"
                for name, value in values.items()
            )

            print(f"0x{offset:04X}: {result}")


def compare_32bit(decrypted):
    """Compare 32-bit unsigned integers."""
    print("\n32-BIT UNSIGNED INTEGERS")
    print("-" * 80)

    names = list(decrypted.keys())

    for offset in range(START, END - 3, 4):
        values = {
            name: struct.unpack_from(
                "<I",
                decrypted[name],
                offset,
            )[0]
            for name in names
        }

        if len(set(values.values())) > 1:
            result = " | ".join(
                f"{name}={value}"
                for name, value in values.items()
            )

            print(f"0x{offset:04X}: {result}")


def main():
    decrypted = load_decrypted_files()

    for name, data in decrypted.items():
        print(f"{name}: {len(data)} bytes")

    if any(len(data) < END for data in decrypted.values()):
        raise ValueError("One of the TED files is smaller than expected.")

    compare_bytes(decrypted)
    compare_16bit(decrypted)
    compare_32bit(decrypted)


if __name__ == "__main__":
    main()
