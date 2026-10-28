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
    """Re-apply XOR to the edited data, preserving the original 80 bytes of the header."""
    if len(data) != len(original_raw):
        raise ValueError("The size of the edited data differs from the original from TED.")
    e = 5
    key = original_raw[64 + e:80] + original_raw[48:64 + e]
    if len(key) != 32:
        raise ValueError("It was not possible to reconstruct the 32-byte XOR key.")
    out = bytearray(original_raw)
    for i in range(80, len(data)):
        out[i] = data[i] ^ key[(i - 80) % 32]
    return bytes(out)
