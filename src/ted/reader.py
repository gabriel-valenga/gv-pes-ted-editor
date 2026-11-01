import struct
from ted.fields import FIELD_BY_NAME, PLAYER_FIELDS, get_field, read_string


PLAYER_RECORD_LEN = 312
MAX_PLAYERS = 40
PLAYERS_START = 2328
EXPECTED_TED_SIZE = 14820
MANAGER_START = 0x29C
MANAGER_RECORD_LEN = 0x58
MANAGER_NAME_OFFSET = 0x09
MANAGER_NAME_LEN = 79

def extract_players(data: bytearray):
    players = []
    for index in range(MAX_PLAYERS):
        start = PLAYERS_START + index * PLAYER_RECORD_LEN
        if start + PLAYER_RECORD_LEN > len(data):
            break
        rec = data[start:start + PLAYER_RECORD_LEN]
        player_id = int.from_bytes(rec[0:4], "little")
        if player_id == 0:
            continue
        item = {"index": index}
        for field in PLAYER_FIELDS:
            try:
                item[field["key"]] = get_field(rec, field)
            except Exception as exc:
                item[field["key"]] = {"read_error": str(exc)}
        item["_recordOffset"] = start
        players.append(item)
    return players


def get_team_summary(data):
    # Team fields
    team_start = 80
    assignment = data[756:1040]

    shirt_numbers = (
        list(struct.unpack_from("<40H", assignment, 164))
        if len(assignment) >= 244
        else []
    )

    # Manager fields
    manager_data_available = (
        len(data) >= MANAGER_START + MANAGER_RECORD_LEN
    )

    if manager_data_available:
        manager_id = int.from_bytes(
            data[MANAGER_START:MANAGER_START + 4],
            "little",
        )

        manager_nationality = int.from_bytes(
            data[MANAGER_START + 4:MANAGER_START + 6],
            "little",
        )

        manager_picture_id = int.from_bytes(
            data[MANAGER_START + 6:MANAGER_START + 8],
            "little",
        )

        manager_name = read_string(
            data,
            MANAGER_START + MANAGER_NAME_OFFSET,
            MANAGER_NAME_LEN,
        )
    else:
        manager_id = None
        manager_nationality = None
        manager_picture_id = None
        manager_name = None

    return {
        "teamName": read_string(data, team_start + 104, 70),
        "shortName": read_string(data, team_start + 174, 4),
        "stadium": read_string(data, team_start + 178, 120),
        "shirtNumbers": shirt_numbers,
        "formationRaw": list(data[1044:1055]) if len(data) >= 1055 else [],
        "managerId": manager_id,
        "managerNationality": manager_nationality,
        "managerPictureId": manager_picture_id,
        "managerName": manager_name,
    }


def extract_player_field(data, player_index, field_name):
    if field_name not in FIELD_BY_NAME:
        raise KeyError(f"Unknown field: {field_name}")
    start = PLAYERS_START + player_index * PLAYER_RECORD_LEN
    if player_index < 0 or start + PLAYER_RECORD_LEN > len(data):
        raise IndexError("Player index out of range.")
    rec = data[start:start + PLAYER_RECORD_LEN]
    return get_field(rec, FIELD_BY_NAME[field_name])
