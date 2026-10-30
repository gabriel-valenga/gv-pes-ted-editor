
import pytest

from editing.players.calculations import (
    calculate_bmi,
    calculate_player_attributes,
)


def test_calculate_bmi():
    player = {
        "weight": 80,
        "height": 180,
    }

    assert calculate_bmi(player) == 24.7


def test_calculate_bmi_with_decimal_result():
    player = {
        "weight": 90,
        "height": 180,
    }

    assert calculate_bmi(player) == 27.8


@pytest.mark.parametrize(
    "weight, height",
    [
        (None, 180),
        (80, None),
        (0, 180),
        (80, 0),
        (-10, 180),
        (80, -180),
        ("80", 180),
        (80, "180"),
        (True, 180),
        (80, False),
    ],
)
def test_calculate_bmi_with_invalid_values(weight, height):
    player = {
        "weight": weight,
        "height": height,
    }

    assert calculate_bmi(player) is None


def test_calculate_player_attributes():
    player = {
        "weight": 80,
        "height": 180,
    }

    result = calculate_player_attributes(player)

    assert result == {
        "bmi": 24.7,
        "overall": None,
    }


def test_calculated_attributes_do_not_modify_original_player():
    player = {
        "weight": 80,
        "height": 180,
    }

    original_player = player.copy()

    calculate_player_attributes(player)

    assert player == original_player
