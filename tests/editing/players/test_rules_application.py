import pytest
import json
import sqlite3
import cli
from editing.players.rules import build_rule_hash
from editing.players.rules import (
    load_rules,
    apply_rules,
    NUMERIC_ATTRIBUTE_FIELDS,
    BOOLEAN_SKILL_FIELDS,
)
from editing.players.conditions import prepare_player
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


def create_overall_player(player_id, position):
    attributes = [
        "attackingProwess",
        "ballControl",
        "dribbling",
        "tightPossession",
        "lowPass",
        "loftedPass",
        "finishing",
        "headingAbility",
        "placeKicking",
        "curl",
        "speed",
        "acceleration",
        "kickingPower",
        "jump",
        "physicalContact",
        "balance",
        "stamina",
        "defensiveProwess",
        "ballWinning",
        "aggression",
        "gkAwareness",
        "gkCatching",
        "gkReach",
        "gkClearing",
        "gkReflexes",
    ]

    player = {
        "id": player_id,
        "registeredPosition": position,
        "weight": 80,
        "height": 180,
        "weakFootAccuracy": 3,
    }

    player.update({field: 70 for field in attributes})

    return player


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


def test_apply_rule_with_calculated_overall_condition(tmp_path):
    data = create_ted_data([
        create_overall_player(1, "GK"),
        create_overall_player(2, "CF"),
    ])

    config = create_config([
        create_rule(
            name="Filter by Overall",
            conditions=[
                {
                    "field": "calculated.overall",
                    "operator": "gte",
                    "value": 50,
                }
            ],
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

    assert edits[0]["playerIndex"] == 0
    assert edits[1]["playerIndex"] == 1

    goalkeeper = get_player(data, 0)
    forward = get_player(data, 1)

    assert goalkeeper["speed"] == 95
    assert forward["speed"] == 95


def test_apply_rule_with_calculated_overall_band(tmp_path):
    data = create_ted_data([
        create_overall_player(1, "GK"),
        create_overall_player(2, "CF"),
    ])

    config = create_config([
        create_rule(
            name="Overall bands",
            operations=[],
            bands=[
                {
                    "field": "calculated.overall",
                    "ranges": [
                        {
                            "min": 60,
                            "max": 65,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 80,
                                }
                            ],
                        },
                        {
                            "min": 71,
                            "max": 75,
                            "operations": [
                                {
                                    "field": "speed",
                                    "operation": "set",
                                    "value": 90,
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

    assert len(edits) == 2

    goalkeeper = get_player(data, 0)
    forward = get_player(data, 1)

    assert goalkeeper["speed"] == 80
    assert forward["speed"] == 90


def test_overall_is_recalculated_between_rules(tmp_path):
    data = create_ted_data([
        create_overall_player(1, "CF"),
    ])

    original_player = get_player(data, 0)
    original_overall = prepare_player(
        original_player
    )["calculated"]["overall"]

    config = create_config([
        create_rule(
            name="Increase finishing",
            operations=[
                {
                    "field": "finishing",
                    "operation": "set",
                    "value": 99,
                }
            ],
        ),
        create_rule(
            name="Apply speed bonus to improved players",
            conditions=[
                {
                    "field": "calculated.overall",
                    "operator": "gt",
                    "value": original_overall,
                }
            ],
            operations=[
                {
                    "field": "speed",
                    "operation": "set",
                    "value": 95,
                }
            ],
        ),
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    updated_player = get_player(data, 0)
    updated_overall = prepare_player(
        updated_player
    )["calculated"]["overall"]

    assert updated_overall > original_overall
    assert updated_player["finishing"] == 99
    assert updated_player["speed"] == 95
    assert len(edits) == 2


@pytest.mark.parametrize("reputation_value", range(1, 9))
def test_apply_reputation_values_and_read_from_ted(
    tmp_path,
    reputation_value,
):
    initial_reputation = 8 if reputation_value == 1 else 1

    data = create_ted_data([
        {
            "id": 1,
            "reputation": initial_reputation,
            "speed": 70,
        }
    ])

    config = create_config([
        create_rule(
            name="Set reputation",
            operations=[
                {
                    "field": "reputation",
                    "operation": "set",
                    "value": reputation_value,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    player = get_player(data, 0)

    assert player["reputation"] == reputation_value
    assert player["speed"] == 70
    assert len(edits) == 1
    assert edits[0]["field"] == "reputation"
    assert edits[0]["before"] == initial_reputation
    assert edits[0]["after"] == reputation_value


def test_reputation_is_set_from_calculated_overall_bands(tmp_path):
    goalkeeper_data = create_overall_player(1, "GK")
    forward_data = create_overall_player(2, "CF")

    goalkeeper_data["reputation"] = 8
    forward_data["reputation"] = 8

    data = create_ted_data([
        goalkeeper_data,
        forward_data,
    ])

    config = create_config([
        create_rule(
            name="Reputation based on Overall",
            operations=[],
            bands=[
                {
                    "field": "calculated.overall",
                    "ranges": [
                        {
                            "min": 0,
                            "max": 57,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 1,
                                }
                            ],
                        },
                        {
                            "min": 58,
                            "max": 62,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 2,
                                }
                            ],
                        },
                        {
                            "min": 63,
                            "max": 67,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 3,
                                }
                            ],
                        },
                        {
                            "min": 68,
                            "max": 72,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 4,
                                }
                            ],
                        },
                        {
                            "min": 73,
                            "max": 77,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 5,
                                }
                            ],
                        },
                        {
                            "min": 78,
                            "max": 82,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 6,
                                }
                            ],
                        },
                        {
                            "min": 83,
                            "max": 87,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 7,
                                }
                            ],
                        },
                        {
                            "min": 88,
                            "max": 1000,
                            "operations": [
                                {
                                    "field": "reputation",
                                    "operation": "set",
                                    "value": 8,
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

    goalkeeper = get_player(data, 0)
    forward = get_player(data, 1)

    assert goalkeeper["reputation"] == 2
    assert forward["reputation"] == 4


@pytest.mark.parametrize(
    "field_name",
    sorted(NUMERIC_ATTRIBUTE_FIELDS),
)
@pytest.mark.parametrize(
    ("operation_type", "operation_value", "expected_value"),
    [
        ("set", 90, 90),
        ("delta", 5, 75),
        ("percentage", 10, 77),
    ],
)
def test_all_numeric_attributes_are_editable(
    tmp_path,
    field_name,
    operation_type,
    operation_value,
    expected_value,
):
    sentinel_field = next(
        name
        for name in NUMERIC_ATTRIBUTE_FIELDS
        if name != field_name
    )

    data = create_ted_data([
        {
            "id": 1,
            field_name: 70,
            sentinel_field: 65,
        }
    ])

    config = create_config([
        create_rule(
            name=f"Edit {field_name}",
            operations=[
                {
                    "field": field_name,
                    "operation": operation_type,
                    "value": operation_value,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    player = get_player(data, 0)

    assert player[field_name] == expected_value
    assert player[sentinel_field] == 65
    assert len(edits) == 1
    assert edits[0]["field"] == field_name
    assert edits[0]["after"] == expected_value


@pytest.mark.parametrize(
    "field_name",
    sorted(BOOLEAN_SKILL_FIELDS),
)
@pytest.mark.parametrize("skill_value", [True, False])
def test_all_boolean_skills_are_editable(
    tmp_path,
    field_name,
    skill_value,
):
    sentinel_field = next(
        name
        for name in BOOLEAN_SKILL_FIELDS
        if name != field_name
    )

    data = create_ted_data([
        {
            "id": 1,
            field_name: not skill_value,
            sentinel_field: True,
        }
    ])

    config = create_config([
        create_rule(
            name=f"Edit {field_name}",
            operations=[
                {
                    "field": field_name,
                    "operation": "set",
                    "value": skill_value,
                }
            ],
        )
    ])

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    player = get_player(data, 0)

    assert player[field_name] is skill_value
    assert player[sentinel_field] is True
    assert len(edits) == 1
    assert edits[0]["field"] == field_name
    assert edits[0]["after"] is skill_value



# --------------------------------------------------
# Player IDs and player settings application tests
# --------------------------------------------------

def test_apply_player_settings_to_specific_player(tmp_path):
    data = create_ted_data([
        {"id": 1001, "registeredPosition": "CF"},
        {"id": 1002, "registeredPosition": "CF"},
        {"id": 1003, "registeredPosition": "CF"},
    ])

    rule = create_rule(
        name="Edit specific player",
        operations=[],
    )
    rule["playerIds"] = [1002]
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 1
    assert get_player(data, 0)["registeredPosition"] == "CF"
    assert get_player(data, 1)["registeredPosition"] == "AMF"
    assert get_player(data, 2)["registeredPosition"] == "CF"


def test_apply_player_settings_to_multiple_players(tmp_path):
    data = create_ted_data([
        {"id": 1001, "registeredPosition": "CF"},
        {"id": 1002, "registeredPosition": "CF"},
        {"id": 1003, "registeredPosition": "CF"},
    ])

    rule = create_rule(
        name="Edit multiple players",
        operations=[],
    )
    rule["playerIds"] = [1001, 1003]
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 2
    assert get_player(data, 0)["registeredPosition"] == "AMF"
    assert get_player(data, 1)["registeredPosition"] == "CF"
    assert get_player(data, 2)["registeredPosition"] == "AMF"


def test_nonexistent_player_id_does_not_modify_other_players(tmp_path):
    data = create_ted_data([
        {"id": 1001, "registeredPosition": "CF"},
        {"id": 1002, "registeredPosition": "CF"},
    ])

    rule = create_rule(
        name="Nonexistent player",
        operations=[],
    )
    rule["playerIds"] = [9999]
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert edits == []
    assert get_player(data, 0)["registeredPosition"] == "CF"
    assert get_player(data, 1)["registeredPosition"] == "CF"


def test_player_ids_respect_global_position_targets(tmp_path):
    data = create_ted_data([
        {"id": 1001, "registeredPosition": "CF"},
        {"id": 1002, "registeredPosition": "GK"},
    ])

    rule = create_rule(
        name="Player ID and global targets",
        operations=[],
    )
    rule["playerIds"] = [1002]
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config(
        [rule],
        all_positions=False,
        positions=["CF"],
    )

    rules = load_test_rules(tmp_path, config)
    edits = apply_rules(data, rules)

    # Player IDs are currently an additional filter
    # after the global position selection.
    assert edits == []
    assert get_player(data, 0)["registeredPosition"] == "CF"
    assert get_player(data, 1)["registeredPosition"] == "GK"


def test_apply_all_three_player_settings(tmp_path):
    data = create_ted_data([
        {
            "id": 1001,
            "registeredPosition": "CF",
            "playingStyle": "goalPoacher",
            "positionCmf": "C",
            "positionAmf": "C",
            "positionSs": "C",
        }
    ])

    rule = create_rule(
        name="Apply all player settings",
        operations=[],
    )
    rule["playerIds"] = [1001]
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
        "playablePositions": {
            "CMF": "A",
            "AMF": "B",
            "SS": "C",
        },
        "playingStyle": "creativePlaymaker",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)
    player = get_player(data, 0)

    assert player["registeredPosition"] == "AMF"
    assert player["positionCmf"] == "A"
    assert player["positionAmf"] == "B"
    assert player["positionSs"] == "C"
    assert player["playingStyle"] == "creativePlaymaker"

    assert len(edits) == 4


@pytest.mark.parametrize(
    "affinity",
    ["C", "B", "A"],
)
def test_apply_playable_position_affinity_levels(
    tmp_path,
    affinity,
):
    data = create_ted_data([
        {
            "id": 1001,
            "positionCmf": "C",
        }
    ])

    rule = create_rule(
        name="Set playable position affinity",
        operations=[],
    )
    rule["playerSettings"] = {
        "playablePositions": {
            "CMF": affinity,
        }
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)
    player = get_player(data, 0)

    assert player["positionCmf"] == affinity
    assert len(edits) == (1 if affinity != "C" else 0)


def test_unmodified_playable_positions_are_preserved(tmp_path):
    data = create_ted_data([
        {
            "id": 1001,
            "positionCmf": "A",
            "positionAmf": "B",
            "positionSs": "C",
            "positionCf": "A",
        }
    ])

    rule = create_rule(
        name="Modify only CMF",
        operations=[],
    )
    rule["playerSettings"] = {
        "playablePositions": {
            "CMF": "C",
        }
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)
    player = get_player(data, 0)

    assert player["positionCmf"] == "C"
    assert player["positionAmf"] == "B"
    assert player["positionSs"] == "C"
    assert player["positionCf"] == "A"

    assert len(edits) == 1


def test_apply_only_playing_style(tmp_path):
    data = create_ted_data([
        {
            "id": 1001,
            "registeredPosition": "CF",
            "playingStyle": "goalPoacher",
            "positionCmf": "A",
        }
    ])

    rule = create_rule(
        name="Change playing style",
        operations=[],
    )
    rule["playerSettings"] = {
        "playingStyle": "creativePlaymaker",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)
    player = get_player(data, 0)

    assert player["playingStyle"] == "creativePlaymaker"
    assert player["registeredPosition"] == "CF"
    assert player["positionCmf"] == "A"

    assert len(edits) == 1


def test_player_settings_are_recorded_in_edit_history(tmp_path):
    data = create_ted_data([
        {
            "id": 1001,
            "registeredPosition": "CF",
            "playingStyle": "goalPoacher",
            "positionCmf": "C",
        }
    ])

    rule = create_rule(
        name="Check edit history",
        operations=[],
    )
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
        "playablePositions": {
            "CMF": "A",
        },
        "playingStyle": "creativePlaymaker",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 3

    assert {edit["field"] for edit in edits} == {
        "registeredPosition",
        "positionCmf",
        "playingStyle",
    }

    assert all(edit["playerIndex"] == 0 for edit in edits)


def test_player_settings_respect_conditions(tmp_path):
    data = create_ted_data([
        {
            "id": 1001,
            "age": 20,
            "registeredPosition": "CF",
        },
        {
            "id": 1002,
            "age": 30,
            "registeredPosition": "CF",
        },
    ])

    rule = create_rule(
        name="Player settings with condition",
        operations=[],
        conditions=[
            {
                "field": "age",
                "operator": "gte",
                "value": 25,
            }
        ],
    )
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert len(edits) == 1
    assert get_player(data, 0)["registeredPosition"] == "CF"
    assert get_player(data, 1)["registeredPosition"] == "AMF"


def test_player_settings_are_applied_only_once_when_unchanged(
    tmp_path,
):
    data = create_ted_data([
        {
            "id": 1001,
            "registeredPosition": "AMF",
        }
    ])

    rule = create_rule(
        name="Unchanged position",
        operations=[],
    )
    rule["playerSettings"] = {
        "registeredPosition": "AMF",
    }

    config = create_config([rule])
    rules = load_test_rules(tmp_path, config)

    edits = apply_rules(data, rules)

    assert edits == []
    assert get_player(data, 0)["registeredPosition"] == "AMF"




def test_prepare_rules_excludes_players_already_processed(
    tmp_path,
    monkeypatch,
):
    rule = create_rule(
        name="Increase speed",
        operations=[
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    )

    config = load_test_rules(
        tmp_path,
        create_config([rule]),
    )

    rule_hash = build_rule_hash(
        config["rules"][0]
    )

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE player_rule_applications (
            player_id INTEGER NOT NULL,
            rule_hash TEXT NOT NULL,
            first_ted_file_id INTEGER NOT NULL
        )
    """)

    ted_file_id = 1

    connection.execute("""
        INSERT INTO player_rule_applications (
            player_id,
            rule_hash,
            first_ted_file_id
        )
        VALUES (?, ?, ?)
    """, (1001, rule_hash, ted_file_id))

    monkeypatch.setattr(
        cli,
        "decrypt_ted",
        lambda content: b"decrypted",
    )

    monkeypatch.setattr(
        cli,
        "extract_players",
        lambda data: [
            {"playerId": 1001, "index": 0},
            {"playerId": 1002, "index": 1},
            {"playerId": 1003, "index": 2},
        ],
    )

    ted_path = tmp_path / "second_team.ted"
    ted_path.write_bytes(b"fake ted")

    prepared = cli._prepare_rules_for_ted(
        connection=connection,
        ted_path=ted_path,
        ted_file_id=ted_file_id,
        rules_list=[config],
    )

    prepared_player_ids = prepared[0]["rules"][0]["playerIds"]

    assert prepared_player_ids == [1002, 1003]

    connection.close()



def test_prepare_rules_preserves_existing_player_restrictions(
    tmp_path,
    monkeypatch,
):
    rule = create_rule(
        name="Increase speed",
        operations=[
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    )

    rule["playerIds"] = [1001, 1002]

    config = load_test_rules(
        tmp_path,
        create_config([rule]),
    )

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE player_rule_applications (
            player_id INTEGER NOT NULL,
            rule_hash TEXT NOT NULL,
            first_ted_file_id INTEGER NOT NULL
        )
    """)

    ted_file_id = 1

    monkeypatch.setattr(
        cli,
        "decrypt_ted",
        lambda content: b"decrypted",
    )

    monkeypatch.setattr(
        cli,
        "extract_players",
        lambda data: [
            {"playerId": 1001, "index": 0},
            {"playerId": 1002, "index": 1},
            {"playerId": 1003, "index": 2},
        ],
    )

    ted_path = tmp_path / "second_team.ted"
    ted_path.write_bytes(b"fake ted")

    prepared = cli._prepare_rules_for_ted(
        connection=connection,
        ted_path=ted_path,
        ted_file_id=ted_file_id,
        rules_list=[config],
    )

    prepared_player_ids = prepared[0]["rules"][0]["playerIds"]

    assert prepared_player_ids == [1001, 1002]

    connection.close()


def test_prepare_rules_preserves_original_hash(
    tmp_path,
    monkeypatch,
):
    rule = create_rule(
        name="Increase speed",
        operations=[
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    )

    config = load_test_rules(
        tmp_path,
        create_config([rule]),
    )

    original_hash = build_rule_hash(config["rules"][0])

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE player_rule_applications (
            player_id INTEGER NOT NULL,
            rule_hash TEXT NOT NULL,
            first_ted_file_id INTEGER NOT NULL
        )
    """)

    ted_file_id = 1

    monkeypatch.setattr(
        cli,
        "decrypt_ted",
        lambda content: b"decrypted",
    )

    monkeypatch.setattr(
        cli,
        "extract_players",
        lambda data: [
            {"playerId": 1001, "index": 0},
        ],
    )

    ted_path = tmp_path / "second_team.ted"
    ted_path.write_bytes(b"fake ted")

    prepared = cli._prepare_rules_for_ted(
        connection=connection,
        ted_path=ted_path,
        ted_file_id=ted_file_id,
        rules_list=[config],
    )

    prepared_rule = prepared[0]["rules"][0]

    assert prepared_rule["_originalRuleHash"] == original_hash

    connection.close()
