import json
from ted.fields import FIELD_BY_NAME, set_field
from ted.reader import PLAYER_RECORD_LEN, PLAYERS_START


def apply_edit(data: bytearray, player_index: int, field_name: str, value_text: str):
    if field_name not in FIELD_BY_NAME:
        raise KeyError(f"Unknown field: {field_name}")
    field = FIELD_BY_NAME[field_name]
    start = PLAYERS_START + player_index * PLAYER_RECORD_LEN
    if player_index < 0 or start + PLAYER_RECORD_LEN > len(data):
        raise IndexError("Player index out of file range.")
    rec = bytearray(data[start:start + PLAYER_RECORD_LEN])
    if int.from_bytes(rec[0:4], "little") == 0:
        raise ValueError(f"Player index not exists: {player_index}.")
    # JSON parsing allows numbers, booleans, null, and strings with spaces.
    try:
        value = json.loads(value_text)
    except json.JSONDecodeError:
        value = value_text
    set_field(rec, field, value)
    data[start:start + PLAYER_RECORD_LEN] = rec
