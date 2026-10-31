
import json
import pytest

from editing.players.rules import (
    CONFIG_FORMAT,
    CONFIG_VERSION,
    VALID_POSITIONS,
    load_rules,
    _validate_condition,
    _validate_operation,
    _calculate_operation,
    _validate_player_ids,
    _validate_player_settings
)


@pytest.fixture
def valid_config():
    return {
        "format": CONFIG_FORMAT,
        "version": CONFIG_VERSION,
        "language": "pt-BR",
        "targets": {
            "allPositions": True,
            "positions": [],
        },
        "rules": [
            {
                "name": "Test rule",
                "enabled": True,
                "conditions": [],
                "conditionLogic": "AND",
                "operations": [
                    {
                        "field": "lowPass",
                        "operation": "delta",
                        "value": -7,
                    }
                ],
                "bands": [],
            }
        ],
    }


@pytest.fixture
def valid_operation():
    return {
        "field": "speed",
        "operation": "delta",
        "value": -5,
    }


def write_config(tmp_path, config):
    path = tmp_path / "test_config.json"
    path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )
    return path


# --------------------------------------------------
# Configuration tests
# --------------------------------------------------

def test_load_valid_config(tmp_path, valid_config):
    path = write_config(tmp_path, valid_config)

    result = load_rules(path)

    assert result["format"] == CONFIG_FORMAT
    assert result["version"] == CONFIG_VERSION
    assert result["language"] == "pt-BR"
    assert len(result["rules"]) == 1


def test_load_config_with_english_language(tmp_path, valid_config):
    valid_config["language"] = "en"

    path = write_config(tmp_path, valid_config)

    result = load_rules(path)

    assert result["language"] == "en"


def test_invalid_config_format(tmp_path, valid_config):
    valid_config["format"] = "invalid-format"

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_config_version(tmp_path, valid_config):
    valid_config["version"] = 99

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_language(tmp_path, valid_config):
    valid_config["language"] = "fr"

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_targets_type(tmp_path, valid_config):
    valid_config["targets"] = []

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_all_positions_type(tmp_path, valid_config):
    valid_config["targets"]["allPositions"] = "true"

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_positions_type(tmp_path, valid_config):
    valid_config["targets"]["positions"] = "GK"

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_invalid_position(tmp_path, valid_config):
    valid_config["targets"]["allPositions"] = False
    valid_config["targets"]["positions"] = ["INVALID"]

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_empty_position_selection(tmp_path, valid_config):
    valid_config["targets"]["allPositions"] = False
    valid_config["targets"]["positions"] = []

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


def test_all_valid_positions_are_recognized():
    assert len(VALID_POSITIONS) == 13


def test_invalid_rules_type(tmp_path, valid_config):
    valid_config["rules"] = {}

    path = write_config(tmp_path, valid_config)

    with pytest.raises(ValueError):
        load_rules(path)


# --------------------------------------------------
# Condition validation tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "operator, value",
    [
        ("eq", 25),
        ("ne", 25),
        ("gt", 25),
        ("gte", 25),
        ("lt", 25),
        ("lte", 25),
        ("in", [20, 25, 30]),
        ("not_in", [20, 30]),
        ("between", [20, 30]),
    ],
)
def test_valid_conditions(operator, value):
    condition = {
        "field": "age",
        "operator": operator,
        "value": value,
    }

    _validate_condition(condition)


def test_valid_calculated_condition():
    condition = {
        "field": "calculated.bmi",
        "operator": "gt",
        "value": 25,
    }

    _validate_condition(condition)


def test_unknown_condition_field():
    condition = {
        "field": "unknownField",
        "operator": "eq",
        "value": 25,
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


def test_unknown_calculated_field():
    condition = {
        "field": "calculated.unknown",
        "operator": "gt",
        "value": 80,
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


def test_invalid_condition_operator():
    condition = {
        "field": "age",
        "operator": "contains",
        "value": 25,
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


def test_missing_condition_value():
    condition = {
        "field": "age",
        "operator": "eq",
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


def test_invalid_between_range():
    condition = {
        "field": "age",
        "operator": "between",
        "value": [30, 20],
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


def test_empty_in_list():
    condition = {
        "field": "age",
        "operator": "in",
        "value": [],
    }

    with pytest.raises(ValueError):
        _validate_condition(condition)


# --------------------------------------------------
# Operation validation tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "operation_type, value",
    [
        ("set", 90),
        ("delta", -5),
        ("percentage", 10),
        ("percentage", -15),
    ],
)
def test_valid_numeric_operations(operation_type, value):
    operation = {
        "field": "speed",
        "operation": operation_type,
        "value": value,
    }

    _validate_operation(operation)


def test_valid_boolean_skill_operation():
    operation = {
        "field": "acrobaticClear",
        "operation": "set",
        "value": False,
    }

    _validate_operation(operation)


@pytest.mark.parametrize("value", [1, 2, 3, 4, 5, 6, 7, 8])
def test_valid_reputation_operation(value):
    operation = {
        "field": "reputation",
        "operation": "set",
        "value": value,
    }

    _validate_operation(operation)


@pytest.mark.parametrize("value", [0, 9, -1, 10, 4.5, True, False])
def test_reputation_rejects_invalid_value(value):
    operation = {
        "field": "reputation",
        "operation": "set",
        "value": value,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


@pytest.mark.parametrize("operation_type", ["delta", "percentage"])
def test_reputation_rejects_unsupported_operations(operation_type):
    operation = {
        "field": "reputation",
        "operation": operation_type,
        "value": 1,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)
        

def test_boolean_skill_rejects_delta():
    operation = {
        "field": "acrobaticClear",
        "operation": "delta",
        "value": 1,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


def test_numeric_operation_rejects_unknown_field():
    operation = {
        "field": "unknownField",
        "operation": "delta",
        "value": 5,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


def test_numeric_operation_rejects_invalid_type():
    operation = {
        "field": "speed",
        "operation": "multiply",
        "value": 2,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


def test_set_rejects_decimal_value():
    operation = {
        "field": "speed",
        "operation": "set",
        "value": 85.5,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


def test_boolean_skill_requires_boolean_value():
    operation = {
        "field": "acrobaticClear",
        "operation": "set",
        "value": 1,
    }

    with pytest.raises(ValueError):
        _validate_operation(operation)


# --------------------------------------------------
# Operation calculation tests
# --------------------------------------------------

def test_calculate_set():
    operation = {
        "operation": "set",
        "value": 90,
    }

    assert _calculate_operation(75, operation) == 90


def test_calculate_delta():
    operation = {
        "operation": "delta",
        "value": -10,
    }

    assert _calculate_operation(85, operation) == 75


def test_calculate_percentage_increase():
    operation = {
        "operation": "percentage",
        "value": 10,
    }

    assert _calculate_operation(80, operation) == 88


def test_calculate_percentage_decrease():
    operation = {
        "operation": "percentage",
        "value": -10,
    }

    assert _calculate_operation(80, operation) == 72


@pytest.mark.parametrize(
    "current, operation, expected",
    [
        (95, {"operation": "delta", "value": 10}, 99),
        (45, {"operation": "delta", "value": -10}, 40),
        (99, {"operation": "set", "value": 120}, 99),
        (20, {"operation": "set", "value": 30}, 40),
    ],
)
def test_numeric_attribute_limits(current, operation, expected):
    assert _calculate_operation(current, operation) == expected


def test_calculate_operation_uses_python_rounding():
    operation = {
        "operation": "delta",
        "value": 0.5,
    }

    assert _calculate_operation(80, operation) == 80



# --------------------------------------------------
# Player IDs validation
# --------------------------------------------------

@pytest.mark.parametrize(
    "player_ids",
    [
        [1],
        [1, 2, 3],
        [12345, 67890],
        [1, 2**32 - 1],
    ],
)
def test_valid_player_ids(player_ids):
    _validate_player_ids(player_ids)


@pytest.mark.parametrize(
    "player_ids",
    [
        [],
        [0],
        [-1],
        [1, 1],
        [1, 2, 1],
        [2**32],
        "123",
        123,
        None,
        {},
    ],
)
def test_invalid_player_ids(player_ids):
    with pytest.raises(ValueError):
        _validate_player_ids(player_ids)


# --------------------------------------------------
# Player settings validation
# --------------------------------------------------

def test_valid_registered_position_setting():
    _validate_player_settings({
        "registeredPosition": "CF",
    })


@pytest.mark.parametrize(
    "position",
    [
        "GK",
        "CB",
        "LB",
        "RB",
        "DMF",
        "CMF",
        "LMF",
        "RMF",
        "AMF",
        "LWF",
        "RWF",
        "SS",
        "CF",
    ],
)
def test_all_registered_positions_are_valid(position):
    _validate_player_settings({
        "registeredPosition": position,
    })


@pytest.mark.parametrize(
    "position",
    [
        "INVALID",
        "B3",
        "",
        None,
        1,
    ],
)
def test_invalid_registered_position_setting(position):
    with pytest.raises(ValueError):
        _validate_player_settings({
            "registeredPosition": position,
        })


def test_valid_playable_positions_setting():
    _validate_player_settings({
        "playablePositions": {
            "GK": "C",
            "CB": "B",
            "CF": "A",
        },
    })


@pytest.mark.parametrize(
    "affinity",
    ["C", "B", "A"],
)
def test_all_playable_position_affinities_are_valid(affinity):
    _validate_player_settings({
        "playablePositions": {
            "CMF": affinity,
        },
    })


@pytest.mark.parametrize(
    "affinity",
    [
        "B3",
        "D",
        "1",
        1,
        True,
        None,
    ],
)
def test_invalid_playable_position_affinity(affinity):
    with pytest.raises(ValueError):
        _validate_player_settings({
            "playablePositions": {
                "CMF": affinity,
            },
        })


@pytest.mark.parametrize(
    "position",
    [
        "INVALID",
        "GK ",
        "",
        "CF2",
    ],
)
def test_invalid_playable_position_name(position):
    with pytest.raises(ValueError):
        _validate_player_settings({
            "playablePositions": {
                position: "A",
            },
        })


@pytest.mark.parametrize(
    "playable_positions",
    [
        [],
        "CMF",
        "A",
        123,
        None,
    ],
)
def test_playable_positions_must_be_an_object(playable_positions):
    with pytest.raises(ValueError):
        _validate_player_settings({
            "playablePositions": playable_positions,
        })


# --------------------------------------------------
# Playing style validation
# --------------------------------------------------

@pytest.mark.parametrize(
    "playing_style",
    [
        "goalPoacher",
        "dummyRunner",
        "foxInTheBox",
        "targetMan",
        "creativePlaymaker",
        "prolificWinger",
        "roamingFlank",
        "crossSpecialist",
        "classicNo10",
        "holePlayer",
        "boxToBox",
        "theDestroyer",
        "orchestrator",
        "anchorMan",
        "offensiveFullBack",
        "fullBackFinisher",
        "defensiveFullBack",
        "buildUp",
        "extraFrontman",
        "offensiveGoalkeeper",
        "defensiveGoalkeeper",
        None,
    ],
)
def test_valid_playing_style_setting(playing_style):
    _validate_player_settings({
        "playingStyle": playing_style,
    })


@pytest.mark.parametrize(
    "playing_style",
    [
        "invalidStyle",
        "",
        "GoalPoacher",
        1,
        True,
    ],
)
def test_invalid_playing_style_setting(playing_style):
    with pytest.raises(ValueError):
        _validate_player_settings({
            "playingStyle": playing_style,
        })


# --------------------------------------------------
# General player settings validation
# --------------------------------------------------

def test_multiple_player_settings_are_valid():
    _validate_player_settings({
        "registeredPosition": "AMF",
        "playablePositions": {
            "CMF": "A",
            "SS": "B",
        },
        "playingStyle": "creativePlaymaker",
    })


def test_empty_player_settings_are_invalid():
    with pytest.raises(ValueError):
        _validate_player_settings({})


@pytest.mark.parametrize(
    "settings",
    [
        [],
        "invalid",
        123,
        None,
    ],
)
def test_player_settings_must_be_an_object(settings):
    with pytest.raises(ValueError):
        _validate_player_settings(settings)


def test_unknown_player_setting_is_invalid():
    with pytest.raises(ValueError):
        _validate_player_settings({
            "unknownSetting": "value",
        })
