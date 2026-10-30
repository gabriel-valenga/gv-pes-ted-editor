
import json
import pytest

from editing.players.rules import (
    CONFIG_FORMAT,
    CONFIG_VERSION,
    VALID_POSITIONS,
    load_rules,
    _validate_condition,
    _validate_operation,
    _validate_bands,
    _validate_rule,
    _calculate_operation,
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
