import hashlib

def decrypt_ted(raw: bytes) -> bytearray:
    """Decrypts the data region used by the original script."""
    if len(raw) < 80:
        raise ValueError("TED file too small (less than 80 bytes).")
    e = 5
    key = raw[64 + e:80] + raw[48:64 + e]
    if len(key) != 32:
        raise ValueError(f"Unexpected XOR key: {len(key)} bytes (expected 32).")
    dec = bytearray(len(raw))
    # The TEditor/base script treats the first 80 bytes as a header.
    dec[:80] = raw[:48] + b"\x00" * 32
    for i in range(80, len(raw)):
        dec[i] = raw[i] ^ key[(i - 80) % 32]
    return dec


def encrypt_ted(data: bytes | bytearray, original_raw: bytes) -> bytes:
    if len(data) != len(original_raw):
        raise ValueError(
            "The size of the edited data differs from the original from TED."
        )

    if len(data) < 80:
        raise ValueError("TED file too small (less than 80 bytes).")

    # The TEditor derives the mask key from SHA-256 of the data region.
    digest = hashlib.sha256(data[80:]).digest()

    # PES 2021 (t=5): bytes 21-31 followed by bytes 0-20.
    key = digest[21:32] + digest[0:21]

    # Preserve the original header and replace its 32-byte hash field.
    out = bytearray(original_raw)
    out[48:80] = digest

    # Apply the XOR mask to the data region.
    for i in range(80, len(data)):
        out[i] = data[i] ^ key[(i - 80) % 32]

    return bytes(out)

