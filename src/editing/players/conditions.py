
from editing.players.calculations import calculate_player_attributes


# Operators supported by the condition engine.
VALID_OPERATORS = {
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
    "between",
}


def prepare_player(player):
    """
    Return a player dictionary containing calculated attributes.

    Original TED fields are preserved.
    Calculated fields are stored separately and are not TED fields.
    """
    prepared = dict(player)

    prepared["calculated"] = calculate_player_attributes(player)

    return prepared


def get_condition_value(player, field):
    """
    Retrieve an original or calculated player field.

    Examples:
        weight
        speed
        registeredPosition
        playingStyle
        calculated.bmi
    """
    if field.startswith("calculated."):
        calculated_field = field.split(".", 1)[1]
        calculated = player.get("calculated", {})
        return calculated.get(calculated_field)

    return player.get(field)


def evaluate_condition(player, condition):
    """
    Evaluate one condition against a player.
    """
    field = condition["field"]
    operator = condition["operator"]
    expected = condition["value"]

    actual = get_condition_value(player, field)

    if actual is None:
        return False

    if isinstance(actual, dict):
        return False

    if operator == "eq":
        return actual == expected

    if operator == "ne":
        return actual != expected

    if operator == "gt":
        return actual > expected

    if operator == "gte":
        return actual >= expected

    if operator == "lt":
        return actual < expected

    if operator == "lte":
        return actual <= expected

    if operator == "in":
        return actual in expected

    if operator == "not_in":
        return actual not in expected

    if operator == "between":
        minimum, maximum = expected
        return minimum <= actual <= maximum

    raise ValueError(f"Unsupported condition operator: {operator}")


def evaluate_conditions(player, conditions, logic="AND"):
    """
    Evaluate multiple conditions using AND or OR.

    Empty conditions mean that the player passes the condition filter.
    """
    if not conditions:
        return True

    logic = logic.upper()

    if logic not in {"AND", "OR"}:
        raise ValueError(f"Invalid condition logic: {logic}")

    results = [
        evaluate_condition(player, condition)
        for condition in conditions
    ]

    if logic == "AND":
        return all(results)

    return any(results)


def evaluate_band(value, minimum, maximum):
    """
    Check whether a value belongs to an inclusive band.
    """
    if value is None:
        return False

    return minimum <= value <= maximum
