from pathlib import Path
from ted.crypto import decrypt_ted, encrypt_ted


def save_ted(path_to_save, data, original_raw):
    encrypted = encrypt_ted(data, original_raw)
    Path(path_to_save).write_bytes(encrypted)
    print(f"TED file saved to: {path_to_save}")


def validate_ted_round_trip(encrypted_ted, data):
    # Verifies that the saved file retains its size and that decryption restores the edited bytes.
    check = decrypt_ted(encrypted_ted)
    if check[80:] != data[80:]:
        raise RuntimeError("Round-trip validation failed in the data region.")
    print("Round-trip XOR validated (region starting from byte 80).")
     