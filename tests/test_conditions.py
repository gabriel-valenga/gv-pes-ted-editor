
import pytest

from editing.players.conditions import (
    prepare_player,
    get_condition_value,
    evaluate_condition,
    evaluate_conditions,
    evaluate_band,
)


@pytest.fixture
def player():
    return {
        "playerName": "Test Player",
        "age": 28,
        "weight": 85,
        "height": 180,
        "registeredPosition": "CF",
        "playingStyle": "goalPoacher",
        "speed": 85,
        "stamina": 80,
    }


@pytest.mark.parametrize(
    "operator, expected, result",
    [
        ("eq", 28, True),
        ("eq", 25, False),
        ("ne", 25, True),
        ("ne", 28, False),
        ("gt", 25, True),
        ("gte", 28, True),
        ("lt", 30, True),
        ("lte", 28, True),
        ("in", [25, 28, 30], True),
        ("not_in", [25, 30], True),
        ("between", [25, 30], True),
        ("between", [29, 35], False),
    ],
)
def test_evaluate_condition_operators(player, operator, expected, result):
    condition = {
        "field": "age",
        "operator": operator,
        "value": expected,
    }

    assert evaluate_condition(player, condition) is result


def test_evaluate_condition_with_calculated_field(player):
    prepared = prepare_player(player)

    condition = {
        "field": "calculated.bmi",
        "operator": "gt",
        "value": 25,
    }

    assert evaluate_condition(prepared, condition) is True


def test_get_original_field_value(player):
    assert get_condition_value(player, "age") == 28


def test_get_calculated_field_value(player):
    prepared = prepare_player(player)

    assert get_condition_value(prepared, "calculated.bmi") == 26.2


def test_get_unknown_calculated_field(player):
    prepared = prepare_player(player)

    assert get_condition_value(prepared, "calculated.unknown") is None


def test_condition_with_missing_field(player):
    condition = {
        "field": "unknownField",
        "operator": "eq",
        "value": 10,
    }

    assert evaluate_condition(player, condition) is False


def test_condition_with_none_value():
    player = {"age": None}

    condition = {
        "field": "age",
        "operator": "eq",
        "value": 25,
    }

    assert evaluate_condition(player, condition) is False


def test_condition_with_dict_value():
    player = {"age": {"read_error": "Invalid field"}}

    condition = {
        "field": "age",
        "operator": "eq",
        "value": 25,
    }

    assert evaluate_condition(player, condition) is False


def test_evaluate_conditions_and(player):
    conditions = [
        {"field": "age", "operator": "gte", "value": 25},
        {"field": "weight", "operator": "gte", "value": 80},
    ]

    assert evaluate_conditions(player, conditions, "AND") is True


def test_evaluate_conditions_and_failure(player):
    conditions = [
        {"field": "age", "operator": "gte", "value": 25},
        {"field": "weight", "operator": "lt", "value": 80},
    ]

    assert evaluate_conditions(player, conditions, "AND") is False


def test_evaluate_conditions_or(player):
    conditions = [
        {"field": "age", "operator": "lt", "value": 20},
        {"field": "registeredPosition", "operator": "eq", "value": "CF"},
    ]

    assert evaluate_conditions(player, conditions, "OR") is True


def test_evaluate_conditions_or_failure(player):
    conditions = [
        {"field": "age", "operator": "lt", "value": 20},
        {"field": "registeredPosition", "operator": "eq", "value": "GK"},
    ]

    assert evaluate_conditions(player, conditions, "OR") is False


def test_empty_conditions_pass(player):
    assert evaluate_conditions(player, []) is True


def test_invalid_condition_logic(player):
    with pytest.raises(ValueError):
        evaluate_conditions(player, [], "XOR")


@pytest.mark.parametrize(
    "value, minimum, maximum, expected",
    [
        (25, 20, 30, True),
        (20, 20, 30, True),
        (30, 20, 30, True),
        (19, 20, 30, False),
        (31, 20, 30, False),
        (None, 20, 30, False),
    ],
)
def test_evaluate_band(value, minimum, maximum, expected):
    assert evaluate_band(value, minimum, maximum) is expected


def test_prepare_player_does_not_modify_original(player):
    original = player.copy()

    prepare_player(player)

    assert player == original
    assert "calculated" not in player
