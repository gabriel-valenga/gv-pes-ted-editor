
import pytest

from editing.players.overall import (
    calculate_overall,
    transform_general_score,
    calculate_general_score,
    calculate_position_score,
)


@pytest.mark.parametrize(
    "score, expected",
    [
        (60, 51),
        (61, 52),
        (62, 56),
        (63, 59),
        (64, 62),
        (65, 65),
        (66, 67),
        (67, 70),
        (68, 73),
        (69, 75),
        (70, 77),
        (71, 79),
        (72, 82),
        (73, 83),
        (74, 86),
        (75, 87),
        (76, 89),
        (77, 90),
        (78, 92),
        (85, 99),
        (99, 113),
    ],
)
def test_transform_general_score(score, expected):
    assert transform_general_score(score) == expected


def make_player():
    return {
        "attackingProwess": 70,
        "ballControl": 70,
        "dribbling": 70,
        "tightPossession": 70,
        "lowPass": 70,
        "loftedPass": 70,
        "finishing": 70,
        "headingAbility": 70,
        "placeKicking": 70,
        "curl": 70,
        "speed": 70,
        "acceleration": 70,
        "kickingPower": 70,
        "jump": 70,
        "physicalContact": 70,
        "balance": 70,
        "stamina": 70,
        "defensiveProwess": 70,
        "ballWinning": 70,
        "aggression": 70,
        "gkAwareness": 70,
        "gkReach": 70,
        "gkCatching": 70,
        "gkClearing": 70,
        "gkReflexes": 70,
        "weakFootAccuracy": 3,
    }


def test_general_score_all_attributes_equal_70():
    player = make_player()

    assert calculate_general_score(player) == 70


def test_general_score_all_attributes_equal_65():
    player = make_player()

    for field in player:
        player[field] = 65

    assert calculate_general_score(player) == 65


def test_general_score_uses_integer_average_for_goalkeeper_attributes():
    player = make_player()

    player["gkAwareness"] = 80
    player["gkReach"] = 71

    # Integer average: (80 + 71) // 2 = 75.
    assert calculate_general_score(player) == 70


def test_general_score_returns_none_when_attribute_is_missing():
    player = make_player()
    del player["speed"]

    assert calculate_general_score(player) is None


def test_position_score_cb_with_all_attributes_equal_70():
    player = make_player()

    score = calculate_position_score(player, "CB")

    # Other attributes: (70 - 25) * 129 = 5805.
    # Weak foot accuracy: (3 - 1) * 23 = 46.
    # Result: trunc((5805 + 46 + 50) / 100) = 59.
    assert score == 59


def test_position_score_gk_uses_goalkeeper_aggregations():
    player = make_player()

    player["gkAwareness"] = 80
    player["gkReach"] = 70

    score = calculate_position_score(player, "GK")

    # Jump: (70 - 25) * 11.
    # Physical contact: (70 - 25) * 11.
    # Goalkeeper awareness: (75 - 25) * 50.
    # Goalkeeper reflexes: (70 - 25) * 48.
    # Result: trunc((495 + 495 + 2500 + 2160 + 50) / 100) = 57.
    assert score == 57


def test_position_score_returns_none_for_invalid_position():
    player = make_player()

    assert calculate_position_score(player, "INVALID") is None


def test_position_score_returns_none_when_required_attribute_is_missing():
    player = make_player()
    del player["speed"]

    assert calculate_position_score(player, "CB") is None



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
def test_position_score_returns_valid_score_for_all_positions(position):
    player = make_player()

    score = calculate_position_score(player, position)

    assert isinstance(score, int)
    assert score >= 0



def test_overall_cb_uses_position_and_general_score_blend():
    player = make_player()
    player["registeredPosition"] = "CB"

    position_score = calculate_position_score(player, "CB")
    general_score = calculate_general_score(player)

    expected = int(
        (position_score + 8) * 0.60
        + transform_general_score(general_score) * 0.40
        + 0.5
    )

    assert calculate_overall(player) == expected


def test_overall_gk_uses_only_adjusted_position_score():
    player = make_player()
    player["registeredPosition"] = "GK"

    position_score = calculate_position_score(player, "GK")

    expected = max(40, position_score + 8)

    assert calculate_overall(player) == expected


def test_overall_returns_none_when_registered_position_is_missing():
    player = make_player()

    assert calculate_overall(player) is None


def test_overall_returns_none_when_registered_position_is_invalid():
    player = make_player()
    player["registeredPosition"] = "INVALID"

    assert calculate_overall(player) is None


def test_overall_never_returns_less_than_40():
    player = make_player()

    for field in player:
        if field != "weakFootAccuracy":
            player[field] = 40

    player["weakFootAccuracy"] = 1
    player["registeredPosition"] = "CB"

    result = calculate_overall(player)

    assert result >= 40



def test_overall_gk_does_not_require_general_attributes():
    player = make_player()
    player["registeredPosition"] = "GK"

    del player["attackingProwess"]
    del player["ballControl"]

    position_score = calculate_position_score(player, "GK")

    expected = max(40, position_score + 8)

    assert calculate_overall(player) == expected


def test_overall_outfield_requires_general_attributes():
    player = make_player()
    player["registeredPosition"] = "CB"

    del player["attackingProwess"]

    assert calculate_overall(player) is None


@pytest.mark.parametrize(
    "position, expected",
    [
        ("GK", 62),
        ("CB", 71),
        ("LB", 74),
        ("RB", 74),
        ("DMF", 74),
        ("CMF", 71),
        ("LMF", 71),
        ("RMF", 71),
        ("AMF", 72),
        ("LWF", 72),
        ("RWF", 72),
        ("SS", 72),
        ("CF", 72),
    ],
)
def test_overall_returns_expected_value_for_each_position(position, expected):
    player = make_player()
    player["registeredPosition"] = position

    assert calculate_overall(player) == expected