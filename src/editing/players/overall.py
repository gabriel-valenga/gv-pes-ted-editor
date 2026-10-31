import math


"""
Player Overall calculation.

Reproduces the Overall calculation reconstructed from the
PES 2021 TEditor implementation.

The registered position is used as the target position.
"""


POSITION_WEIGHTS = {
    "GK": {
        "jump": 11,
        "physicalContact": 11,
        "gkAwareness": 50,
        "gkReflexes": 48,
    },
    "CB": {
        "headingAbility": 22,
        "speed": 10,
        "jump": 19,
        "physicalContact": 19,
        "stamina": 9,
        "defensiveProwess": 25,
        "ballWinning": 17,
        "aggression": 8,
        "weakFootAccuracy": 23,
    },
    "LB": {
        "attackingProwess": 6,
        "ballControl": 9,
        "dribbling": 9,
        "tightPossession": 5,
        "loftedPass": 14,
        "speed": 16,
        "acceleration": 14,
        "jump": 11,
        "physicalContact": 8,
        "balance": 4,
        "stamina": 14,
        "defensiveProwess": 14,
        "ballWinning": 8,
        "aggression": 5,
        "weakFootAccuracy": 56,
    },
    "RB": {
        "attackingProwess": 6,
        "ballControl": 9,
        "dribbling": 9,
        "tightPossession": 5,
        "loftedPass": 14,
        "speed": 16,
        "acceleration": 14,
        "jump": 11,
        "physicalContact": 8,
        "balance": 4,
        "stamina": 14,
        "defensiveProwess": 14,
        "ballWinning": 8,
        "aggression": 5,
        "weakFootAccuracy": 56,
    },
    "DMF": {
        "attackingProwess": 7,
        "ballControl": 18,
        "dribbling": 10,
        "tightPossession": 5,
        "lowPass": 18,
        "loftedPass": 19,
        "curl": 12,
        "speed": 3,
        "acceleration": 3,
        "jump": 5,
        "physicalContact": 9,
        "balance": 4,
        "stamina": 14,
        "defensiveProwess": 7,
        "ballWinning": 3,
        "aggression": 1,
        "weakFootAccuracy": 23,
    },
    "CMF": {
        "attackingProwess": 5,
        "ballControl": 23,
        "dribbling": 16,
        "tightPossession": 8,
        "lowPass": 23,
        "loftedPass": 21,
        "speed": 4,
        "acceleration": 6,
        "physicalContact": 3,
        "balance": 2,
        "stamina": 17,
        "defensiveProwess": 3,
        "weakFootAccuracy": 23,
    },
    "LMF": {
        "attackingProwess": 7,
        "ballControl": 15,
        "dribbling": 17,
        "tightPossession": 8,
        "lowPass": 7,
        "loftedPass": 12,
        "curl": 4,
        "speed": 24,
        "acceleration": 21,
        "stamina": 13,
        "weakFootAccuracy": 56,
    },
    "RMF": {
        "attackingProwess": 7,
        "ballControl": 15,
        "dribbling": 17,
        "tightPossession": 8,
        "lowPass": 7,
        "loftedPass": 12,
        "curl": 4,
        "speed": 24,
        "acceleration": 21,
        "stamina": 13,
        "weakFootAccuracy": 56,
    },
    "AMF": {
        "attackingProwess": 14,
        "ballControl": 23,
        "dribbling": 17,
        "tightPossession": 7,
        "lowPass": 21,
        "loftedPass": 14,
        "finishing": 17,
        "speed": 5,
        "acceleration": 7,
        "physicalContact": 2,
        "balance": 3,
        "stamina": 3,
        "weakFootAccuracy": 37,
    },
    "LWF": {
        "attackingProwess": 17,
        "ballControl": 19,
        "dribbling": 15,
        "tightPossession": 7,
        "lowPass": 5,
        "loftedPass": 9,
        "finishing": 11,
        "speed": 15,
        "acceleration": 15,
        "kickingPower": 5,
        "physicalContact": 2,
        "balance": 4,
        "stamina": 6,
        "weakFootAccuracy": 47,
    },
    "RWF": {
        "attackingProwess": 17,
        "ballControl": 19,
        "dribbling": 15,
        "tightPossession": 7,
        "lowPass": 5,
        "loftedPass": 9,
        "finishing": 11,
        "speed": 15,
        "acceleration": 15,
        "kickingPower": 5,
        "physicalContact": 2,
        "balance": 4,
        "stamina": 6,
        "weakFootAccuracy": 47,
    },
    "SS": {
        "attackingProwess": 15,
        "ballControl": 19,
        "dribbling": 13,
        "tightPossession": 6,
        "lowPass": 9,
        "loftedPass": 9,
        "finishing": 14,
        "speed": 9,
        "acceleration": 21,
        "kickingPower": 6,
        "physicalContact": 2,
        "balance": 5,
        "stamina": 4,
        "weakFootAccuracy": 37,
    },
    "CF": {
        "attackingProwess": 31,
        "ballControl": 23,
        "dribbling": 9,
        "tightPossession": 5,
        "finishing": 36,
        "headingAbility": 3,
        "speed": 5,
        "acceleration": 5,
        "kickingPower": 3,
        "jump": 3,
        "physicalContact": 8,
        "balance": 2,
        "weakFootAccuracy": 38,
    },
}


POSITION_ADJUSTMENTS = {
    "GK": 8,
    "CB": 8,
    "LB": 9,
    "RB": 9,
    "DMF": 9,
    "CMF": 8,
    "LMF": 8,
    "RMF": 8,
    "AMF": 8,
    "LWF": 10,
    "RWF": 10,
    "SS": 9,
    "CF": 8,
}


FAMILIARITY_FIELDS = {
    "GK": "positionGk",
    "CB": "positionCb",
    "LB": "positionLb",
    "RB": "positionRb",
    "DMF": "positionDmf",
    "CMF": "positionCmf",
    "LMF": "positionLmf",
    "RMF": "positionRmf",
    "AMF": "positionAmf",
    "LWF": "positionLwf",
    "RWF": "positionRwf",
    "SS": "positionSs",
    "CF": "positionCf",
}


FAMILIARITY_BONUSES = {
    "GK": {"A": 5, "B": 3},
    "CB": {"A": 5, "B": 3},
    "LB": {"A": 4, "B": 2},
    "RB": {"A": 4, "B": 2},
    "DMF": {"A": 4, "B": 2},
    "CMF": {"A": 5, "B": 3},
    "LMF": {"A": 5, "B": 3},
    "RMF": {"A": 5, "B": 3},
    "AMF": {"A": 5, "B": 3},
    "LWF": {"A": 4, "B": 2},
    "RWF": {"A": 4, "B": 2},
    "SS": {"A": 5, "B": 3},
    "CF": {"A": 5, "B": 3},
}


GENERAL_ATTRIBUTES = [
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
]


def _valid_number(value):
    """Check whether a value can be used as a finite numeric attribute."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def calculate_general_score(player):
    """
    Calculate the general score using the 22 values
    described in the reconstructed TEditor formula.
    """
    import math

    values = []

    for attribute in GENERAL_ATTRIBUTES:
        value = player.get(attribute)

        if not _valid_number(value):
            print(
                f"DEBUG: attribute={attribute}",
                f"value={value!r}"
            )
            return None

        values.append(value)

    gk_awareness = player.get("gkAwareness")
    gk_reach = player.get("gkReach")

    gk_catching = player.get("gkCatching")
    gk_clearing = player.get("gkClearing")
    gk_reflexes = player.get("gkReflexes")

    gk_values = [
        gk_awareness,
        gk_reach,
        gk_catching,
        gk_clearing,
        gk_reflexes,
    ]

    if not all(_valid_number(value) for value in gk_values):
        return None

    values.append(math.trunc((gk_awareness + gk_reach) / 2))
    values.append(math.trunc(
        (gk_catching + gk_clearing + gk_reflexes) / 3
    ))

    total = sum(values)

    return math.trunc(
        (math.trunc(total * 100 / 22) + 50) / 100
    )



def transform_general_score(score):
    """Transform the general score using the reconstructed lookup table."""
    if score is None:
        return None

    if score <= 61:
        return score - 9
    if score <= 62:
        return score - 6
    if score <= 63:
        return score - 4
    if score <= 64:
        return score - 2
    if score <= 65:
        return score
    if score <= 66:
        return score + 1
    if score <= 67:
        return score + 3
    if score <= 68:
        return score + 5
    if score <= 69:
        return score + 6
    if score <= 70:
        return score + 7
    if score <= 71:
        return score + 8
    if score <= 73:
        return score + 10
    if score <= 75:
        return score + 12
    if score <= 77:
        return score + 13

    return score + 14


def calculate_position_score(player, position):
    """
    Calculate the position-specific score.

    Regular attributes use (value - 25) * weight.
    weakFootAccuracy uses (value - 1) * weight.
    """
    import math

    weights = POSITION_WEIGHTS.get(position)

    if weights is None:
        return None

    total = 0

    for attribute, weight in weights.items():
        if position == "GK" and attribute == "gkAwareness":
            awareness = player.get("gkAwareness")
            reach = player.get("gkReach")

            if not _valid_number(awareness) or not _valid_number(reach):
                return None

            value = math.trunc((awareness + reach) / 2)

        elif position == "GK" and attribute == "gkReflexes":
            catching = player.get("gkCatching")
            clearing = player.get("gkClearing")
            reflexes = player.get("gkReflexes")

            if not all(_valid_number(v) for v in (catching, clearing, reflexes)):
                return None

            value = math.trunc((catching + clearing + reflexes) / 3)

        else:
            value = player.get(attribute)

            if not _valid_number(value):
                print(
                    f"DEBUG: position={position}, "
                    f"attribute={attribute}, "
                    f"value={value!r}"
                )
                return None

        if attribute == "weakFootAccuracy":
            total += (value - 1) * weight
        else:
            total += (value - 25) * weight

    return math.trunc((total + 50) / 100)



def calculate_overall(player):
    """
    Calculate the player's Overall using registeredPosition.

    Returns None when required data is missing or invalid.
    """
    position = player.get("registeredPosition")

    if position not in POSITION_WEIGHTS:
        return None

    position_score = calculate_position_score(player, position)

    if position_score is None:
        return None

    adjusted_score = position_score + POSITION_ADJUSTMENTS[position]

    if position == "GK":
        return max(40, adjusted_score)

    general_score = calculate_general_score(player)

    if general_score is None:
        return None

    transformed_general = transform_general_score(general_score)

    overall = math.trunc(
        (adjusted_score * 60 + transformed_general * 40 + 50) / 100
    )

    return max(40, overall)

