
import json

from editing.players.rules import load_rules, apply_rules
from ted.fields import FIELD_BY_NAME, set_field
from ted.reader import (
    PLAYERS_START,
    PLAYER_RECORD_LEN,
    extract_players,
)


def create_ted_data(players):
    """
    Create a TED buffer containing real player records.

    Each player must provide a unique ID and may provide
    additional fields such as speed or registeredPosition.
    """
    data = bytearray(
        PLAYERS_START + len(players) * PLAYER_RECORD_LEN
    )

    for index, player_data in enumerate(players):
        start = PLAYERS_START + index * PLAYER_RECORD_LEN
        record = bytearray(PLAYER_RECORD_LEN)

        player_id = player_data["id"]
        record[0:4] = player_id.to_bytes(4, "little")

        for field_name, value in player_data.items():
            if field_name == "id":
                continue

            set_field(
                record,
                FIELD_BY_NAME[field_name],
                value,
            )

        data[start:start + PLAYER_RECORD_LEN] = record

    return data


def create_config(rules, all_positions=True, positions=None):
    return {
        "format": "pes-gv-ted-rules-config",
        "version": 1,
        "language": "pt-BR",
        "targets": {
            "allPositions": all_positions,
            "positions": positions or [],
        },
        "rules": rules,
    }


def create_rule(
    name,
    operations,
    conditions=None,
    condition_logic="AND",
    enabled=True,
    bands=None,
):
    return {
        "name": name,
        "enabled": enabled,
        "conditionLogic": condition_logic,
        "conditions": conditions or [],
        "operations": operations,
        "bands": bands or [],
    }


def load_test_rules(tmp_path, config):
    config_path = tmp_path / "test_rules.json"

    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    return load_rules(config_path)


def get_player(data, index):
    players = extract_players(data)

    return next(
        player for player in players
        if player["index"] == index
    )


def test_apply_rule_to_all_players(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70},
        {"id": 2, "speed": 75},
        {"id": 3, "speed": 80},
    ])

    config = create_config([
        create_rule(
            name="Increase speed",
            operations=[
                {
                    "field": "speed",
                    "operation": "set",
                    "value": 90,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 3

    assert get_player(data, 0)["speed"] == 90
    assert get_player(data, 1)["speed"] == 90
    assert get_player(data, 2)["speed"] == 90


def test_apply_rule_only_to_selected_positions(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70, "registeredPosition": "GK"},
        {"id": 2, "speed": 75, "registeredPosition": "CB"},
        {"id": 3, "speed": 80, "registeredPosition": "CF"},
    ])

    config = create_config(
        rules=[
            create_rule(
                name="Increase goalkeeper speed",
                operations=[
                    {
                        "field": "speed",
                        "operation": "set",
                        "value": 90,
                    }
                ],
            )
        ],
        all_positions=False,
        positions=["GK"],
    )

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 1

    assert get_player(data, 0)["speed"] == 90
    assert get_player(data, 1)["speed"] == 75
    assert get_player(data, 2)["speed"] == 80


def test_apply_rule_with_and_conditions(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70, "age": 25},
        {"id": 2, "speed": 75, "age": 30},
        {"id": 3, "speed": 80, "age": 25},
    ])

    config = create_config([
        create_rule(
            name="AND conditions",
            conditions=[
                {
                    "field": "speed",
                    "operator": "gte",
                    "value": 75,
                },
                {
                    "field": "age",
                    "operator": "eq",
                    "value": 25,
                },
            ],
            condition_logic="AND",
            operations=[
                {
                    "field": "speed",
                    "operation": "set",
                    "value": 95,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 1

    assert get_player(data, 0)["speed"] == 70
    assert get_player(data, 1)["speed"] == 75
    assert get_player(data, 2)["speed"] == 95


def test_apply_rule_with_or_conditions(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70, "age": 25},
        {"id": 2, "speed": 75, "age": 30},
        {"id": 3, "speed": 80, "age": 35},
    ])

    config = create_config([
        create_rule(
            name="OR conditions",
            conditions=[
                {
                    "field": "age",
                    "operator": "eq",
                    "value": 25,
                },
                {
                    "field": "age",
                    "operator": "eq",
                    "value": 35,
                },
            ],
            condition_logic="OR",
            operations=[
                {
                    "field": "speed",
                    "operation": "set",
                    "value": 95,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 2

    assert get_player(data, 0)["speed"] == 95
    assert get_player(data, 1)["speed"] == 75
    assert get_player(data, 2)["speed"] == 95


def test_disabled_rule_is_not_applied(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70},
        {"id": 2, "speed": 80},
    ])

    config = create_config([
        create_rule(
            name="Disabled rule",
            enabled=False,
            operations=[
                {
                    "field": "speed",
                    "operation": "set",
                    "value": 99,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert edits == []

    assert get_player(data, 0)["speed"] == 70
    assert get_player(data, 1)["speed"] == 80


def test_operations_are_applied_sequentially(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 70},
    ])

    config = create_config([
        create_rule(
            name="Sequential operations",
            operations=[
                {
                    "field": "speed",
                    "operation": "delta",
                    "value": 4,
                },
                {
                    "field": "speed",
                    "operation": "percentage",
                    "value": 10,
                },
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    # 70 + 4 = 74
    # 74 + 10% = 81.4, rounded to 81
    assert len(edits) == 2
    assert get_player(data, 0)["speed"] == 81

    assert edits[0]["before"] == 70
    assert edits[0]["after"] == 74
    assert edits[1]["before"] == 74
    assert edits[1]["after"] == 81



def test_band_applies_operation_inside_range(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 60},
        {"id": 2, "speed": 75},
        {"id": 3, "speed": 90},
    ])

    config = create_config([
        create_rule(
            name="Speed band",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 70,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 99,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert len(edits) == 1
    assert get_player(data, 0)["speed"] == 60
    assert get_player(data, 1)["speed"] == 99
    assert get_player(data, 2)["speed"] == 90



def test_band_does_not_apply_outside_range(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 50},
        {"id": 2, "speed": 85},
        {"id": 3, "speed": 95},
    ])

    config = create_config([
        create_rule(
            name="Speed band",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 60,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 99,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert edits == []
    assert get_player(data, 0)["speed"] == 50
    assert get_player(data, 1)["speed"] == 85
    assert get_player(data, 2)["speed"] == 95



def test_band_uses_calculated_bmi(tmp_path):
    data = create_ted_data([
        {"id": 1, "weight": 60, "height": 180, "speed": 70},
        {"id": 2, "weight": 90, "height": 180, "speed": 70},
        {"id": 3, "weight": 100, "height": 180, "speed": 70},
    ])

    config = create_config([
        create_rule(
            name="BMI band",
            operations=[],
            bands=[
                {
                    "field": "calculated.bmi",
                    "ranges": [
                        {
                            "min": 27,
                            "max": 32,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 85,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert len(edits) == 2
    assert get_player(data, 0)["speed"] == 70
    assert get_player(data, 1)["speed"] == 85
    assert get_player(data, 2)["speed"] == 85



def test_multiple_ranges_apply_different_operations(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 50},
        {"id": 2, "speed": 70},
        {"id": 3, "speed": 90},
    ])

    config = create_config([
        create_rule(
            name="Multiple speed bands",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 40,
                            "max": 60,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 65,
                                }
                            ],
                        },
                        {
                            "min": 61,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 85,
                                }
                            ],
                        },
                        {
                            "min": 81,
                            "max": 99,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 99,
                                }
                            ],
                        },
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert len(edits) == 3
    assert get_player(data, 0)["speed"] == 65
    assert get_player(data, 1)["speed"] == 85
    assert get_player(data, 2)["speed"] == 99



def test_band_includes_minimum_and_maximum_values(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 69},
        {"id": 2, "speed": 70},
        {"id": 3, "speed": 80},
        {"id": 4, "speed": 81},
    ])

    config = create_config([
        create_rule(
            name="Inclusive boundaries",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 70,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 99,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert len(edits) == 2
    assert get_player(data, 0)["speed"] == 69
    assert get_player(data, 1)["speed"] == 99
    assert get_player(data, 2)["speed"] == 99
    assert get_player(data, 3)["speed"] == 81



def test_band_includes_minimum_and_maximum_values(tmp_path):
    data = create_ted_data([
        {"id": 1, "speed": 69},
        {"id": 2, "speed": 70},
        {"id": 3, "speed": 80},
        {"id": 4, "speed": 81},
    ])

    config = create_config([
        create_rule(
            name="Inclusive boundaries",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 70,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 99,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    assert len(edits) == 2
    assert get_player(data, 0)["speed"] == 69
    assert get_player(data, 1)["speed"] == 99
    assert get_player(data, 2)["speed"] == 99
    assert get_player(data, 3)["speed"] == 81


def test_band_rejects_modification_of_weight(tmp_path):
    config = create_config([
        create_rule(
            name="Invalid weight modification",
            operations=[],
            bands=[
                {
                    "field": "calculated.bmi",
                    "ranges": [
                        {
                            "min": 20,
                            "max": 25,
                            "operations": [
                                {
                                    "field": "weight",
                                    "operation": "set",
                                    "value": 100,
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ])

    config_path = tmp_path / "invalid_rules.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    import pytest

    with pytest.raises(ValueError, match="cannot be modified"):
        load_rules(config_path)


def test_overlapping_ranges_apply_both_operations(tmp_path):
    data = create_ted_data([
        {
            "id": 1,
            "speed": 75,
        },
    ])

    config = create_config([
        create_rule(
            name="Overlapping ranges",
            operations=[],
            bands=[
                {
                    "field": "speed",
                    "ranges": [
                        {
                            "min": 60,
                            "max": 80,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "delta",
                                    "value": 5,
                                }
                            ],
                        },
                        {
                            "min": 70,
                            "max": 90,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "delta",
                                    "value": 10,
                                }
                            ],
                        },
                    ],
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    player = get_player(data, 0)

    assert player["speed"] == 90
    assert len(edits) == 2
    