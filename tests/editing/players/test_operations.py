
import json
import pytest

from ted.fields import FIELD_BY_NAME, set_field, get_field
from ted.reader import PLAYER_RECORD_LEN, PLAYERS_START
from editing.players.operations import apply_edit


@pytest.fixture
def ted_data():
    data = bytearray(PLAYERS_START + PLAYER_RECORD_LEN)

    # Simulate an existing player record.
    data[PLAYERS_START:PLAYERS_START + 4] = (
        12345
    ).to_bytes(4, "little")

    return data


def test_apply_edit_numeric_field(ted_data):
    apply_edit(ted_data, 0, "speed", "90")

    record = ted_data[PLAYERS_START:PLAYERS_START + PLAYER_RECORD_LEN]

    assert get_field(record, FIELD_BY_NAME["speed"]) == 90


def test_apply_edit_boolean_field(ted_data):
    apply_edit(ted_data, 0, "acrobaticClear", "true")

    record = ted_data[PLAYERS_START:PLAYERS_START + PLAYER_RECORD_LEN]

    assert get_field(
        record,
        FIELD_BY_NAME["acrobaticClear"],
    ) is True


def test_apply_edit_string_field(ted_data):
    apply_edit(ted_data, 0, "playerName", '"Test Player"')

    record = ted_data[PLAYERS_START:PLAYERS_START + PLAYER_RECORD_LEN]

    assert get_field(record, FIELD_BY_NAME["playerName"]) == "Test Player"


def test_apply_edit_unknown_field(ted_data):
    with pytest.raises(KeyError):
        apply_edit(ted_data, 0, "unknownField", "90")


@pytest.mark.parametrize("player_index", [-1, 1])
def test_apply_edit_invalid_player_index(ted_data, player_index):
    with pytest.raises(IndexError):
        apply_edit(ted_data, player_index, "speed", "90")


def test_apply_edit_empty_player_record(ted_data):
    ted_data[PLAYERS_START:PLAYERS_START + 4] = b"\x00\x00\x00\x00"

    with pytest.raises(ValueError):
        apply_edit(ted_data, 0, "speed", "90")


def test_apply_edit_invalid_field_value(ted_data):
    with pytest.raises((ValueError, TypeError)):
        apply_edit(ted_data, 0, "speed", '"invalid"')


def test_apply_edit_does_not_modify_other_records(ted_data):
    original_data = bytearray(ted_data)

    apply_edit(ted_data, 0, "speed", "90")

    assert ted_data[:PLAYERS_START] == original_data[:PLAYERS_START]
