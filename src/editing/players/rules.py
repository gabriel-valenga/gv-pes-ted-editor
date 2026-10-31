
import json
import math
from pathlib import Path
from editing.players.conditions import (
    evaluate_conditions,
    evaluate_band,
    prepare_player,
)
from editing.players.operations import apply_edit
from ted.fields import PLAYER_FIELDS
from ted.reader import extract_players


CONFIG_FORMAT = "pes-gv-ted-rules-config"
CONFIG_VERSION = 1

VALID_LANGUAGES = {"pt-BR", "en"}

VALID_POSITIONS = {
    "GK", "RB", "CB", "LB", "DMF", "CMF",
    "AMF", "RMF", "LMF", "RWF", "LWF", "SS", "CF",
}

VALID_OPERATIONS = {"set", "delta", "percentage"}

VALID_CONDITION_OPERATORS = {
    "eq", "ne", "gt", "gte", "lt", "lte",
    "in", "not_in", "between",
}

CALCULATED_FIELDS = {
    "bmi",
    "overall",
}

FIELD_BY_NAME = {
    field["key"]: field
    for field in PLAYER_FIELDS
}

# Editable numeric player attributes.
# These are the original PES attributes with values from 40 to 99.
NUMERIC_ATTRIBUTE_FIELDS = {
    field["key"]
    for field in PLAYER_FIELDS
    if (
        field.get("type") == "bitfield"
        and field.get("lengthInBit") == 7
        and not field.get("transform")
    )
}

# Boolean special skills.
BOOLEAN_SKILL_FIELDS = {
    field["key"]
    for field in PLAYER_FIELDS
    if (
        field.get("type") == "bitfield"
        and field.get("lengthInBit") == 1
        and field.get("transform") == "j"
    )
}
# Player reputation field.
# It uses a 3-bit field with logical values from 1 to 8.
REPUTATION_FIELDS = {
    "reputation",
}


def _is_finite_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _validate_condition(condition):
    if not isinstance(condition, dict):
        raise ValueError("Each condition must be an object.")
    allowed_fields = {"field", "operator", "value"}

    unknown_fields = set(condition) - allowed_fields

    if unknown_fields:
        raise ValueError(
            f"Unknown condition fields: {sorted(unknown_fields)}"
        )

    field_name = condition.get("field")
    operator = condition.get("operator")

    if not isinstance(field_name, str):
        raise ValueError("Condition field must be a string.")

    if field_name.startswith("calculated."):
        calculated_name = field_name.split(".", 1)[1]

        if calculated_name not in CALCULATED_FIELDS:
            raise ValueError(
                f"Unknown calculated field: {field_name}"
            )
    elif field_name not in FIELD_BY_NAME:
        raise ValueError(f"Unknown condition field: {field_name}")

    if not isinstance(operator, str):
        raise ValueError("Condition operator must be a string.")

    if operator not in VALID_CONDITION_OPERATORS:
        raise ValueError(f"Invalid condition operator: {operator}")

    if "value" not in condition:
        raise ValueError(
            f"Condition '{field_name}' requires a value."
        )

    value = condition["value"]

    if operator in {"gt", "gte", "lt", "lte"}:
        if not _is_finite_number(value):
            raise ValueError(
                f"Operator '{operator}' requires a numeric value."
            )

    elif operator in {"in", "not_in"}:
        if not isinstance(value, list) or not value:
            raise ValueError(
                f"Operator '{operator}' requires a non-empty list."
            )

    elif operator == "between":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(_is_finite_number(item) for item in value)
        ):
            raise ValueError(
                "Operator 'between' requires two numeric values."
            )

        if value[0] > value[1]:
            raise ValueError(
                "The minimum of a 'between' condition "
                "cannot exceed its maximum."
            )


def _validate_operation(operation):
    if not isinstance(operation, dict):
        raise ValueError("Each operation must be an object.")
    allowed_fields = {"field", "operation", "value"}

    unknown_fields = set(operation) - allowed_fields

    if unknown_fields:
        raise ValueError(
            f"Unknown operation fields: {sorted(unknown_fields)}"
        )

    field_name = operation.get("field")
    operation_type = operation.get("operation")
    value = operation.get("value")

    if not isinstance(field_name, str):
        raise ValueError("Operation field must be a string.")

    if field_name not in FIELD_BY_NAME:
        raise ValueError(f"Unknown operation field: {field_name}")

    if not isinstance(operation_type, str):
        raise ValueError("Operation type must be a string.")

    if operation_type not in VALID_OPERATIONS:
        raise ValueError(
            f"Invalid operation '{operation_type}' "
            f"for field '{field_name}'."
        )

    if field_name in NUMERIC_ATTRIBUTE_FIELDS:
        if not _is_finite_number(value):
            raise ValueError(
                f"Operation on '{field_name}' requires a finite number."
            )

        if operation_type == "set" and not float(value).is_integer():
            raise ValueError(
                f"Operation 'set' on '{field_name}' requires an integer."
            )

    elif field_name in BOOLEAN_SKILL_FIELDS:
        if operation_type != "set":
            raise ValueError(
                f"Boolean skill '{field_name}' only supports 'set'."
            )

        if not isinstance(value, bool):
            raise ValueError(
                f"Boolean skill '{field_name}' requires true or false."
            )

    elif field_name in REPUTATION_FIELDS:
        if operation_type != "set":
            raise ValueError(
                f"Reputation field '{field_name}' only supports 'set'."
            )

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 8
        ):
            raise ValueError(
                f"Reputation field '{field_name}' requires an integer from 1 to 8."
            )

    else:
        raise ValueError(
            f"Field '{field_name}' cannot be modified by this rules engine."
        )


def _validate_bands(bands):
    if not isinstance(bands, list):
        raise ValueError("'bands' must be a list.")

    for band in bands:
        if not isinstance(band, dict):
            raise ValueError("Each band must be an object.")

        allowed_fields = {"field", "ranges"}
        unknown_fields = set(band) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"Unknown band fields: {sorted(unknown_fields)}"
            )

        field_name = band.get("field")

        if not isinstance(field_name, str):
            raise ValueError("Band field must be a string.")

        if field_name.startswith("calculated."):
            calculated_name = field_name.split(".", 1)[1]

            if calculated_name not in CALCULATED_FIELDS:
                raise ValueError(
                    f"Unknown calculated band field: {field_name}"
                )
        elif field_name not in FIELD_BY_NAME:
            raise ValueError(f"Unknown band field: {field_name}")

        ranges = band.get("ranges")

        if not isinstance(ranges, list) or not ranges:
            raise ValueError(
                f"Band '{field_name}' requires at least one range."
            )

        for value_range in ranges:
            if not isinstance(value_range, dict):
                raise ValueError(
                    f"Each range in band '{field_name}' must be an object."
                )
            allowed_fields = {"min", "max", "operations"}
            unknown_fields = set(value_range) - allowed_fields

            if unknown_fields:
                raise ValueError(
                    f"Unknown range fields: {sorted(unknown_fields)}"
                )
            minimum = value_range.get("min")
            maximum = value_range.get("max")
            operations = value_range.get("operations")

            if (
                not _is_finite_number(minimum)
                or not _is_finite_number(maximum)
            ):
                raise ValueError(
                    f"Invalid numeric range for '{field_name}'."
                )

            if minimum > maximum:
                raise ValueError(
                    f"Range minimum exceeds maximum for '{field_name}'."
                )

            if not isinstance(operations, list) or not operations:
                raise ValueError(
                    "Each range must contain at least one operation."
                )

            for operation in operations:
                _validate_operation(operation)


def _validate_rule(rule):
    if not isinstance(rule, dict):
        raise ValueError("Each rule must be an object.")
    allowed_fields = {
        "name",
        "enabled",
        "conditionLogic",
        "conditions",
        "operations",
        "bands",
    }

    unknown_fields = set(rule) - allowed_fields

    if unknown_fields:
        raise ValueError(
            f"Unknown rule fields: {sorted(unknown_fields)}"
        )

    name = rule.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Each rule requires a non-empty name.")

    if not isinstance(rule.get("enabled"), bool):
        raise ValueError(
            f"Rule '{rule['name']}' requires an enabled boolean."
        )

    logic = rule.get("conditionLogic", "AND")

    if not isinstance(logic, str) or logic not in {"AND", "OR"}:
        raise ValueError(
            f"Invalid conditionLogic in rule '{rule['name']}'."
        )

    conditions = rule.get("conditions", [])
    operations = rule.get("operations", [])
    bands = rule.get("bands", [])

    if not isinstance(conditions, list):
        raise ValueError("'conditions' must be a list.")

    if not isinstance(operations, list):
        raise ValueError("'operations' must be a list.")

    for condition in conditions:
        _validate_condition(condition)

    for operation in operations:
        _validate_operation(operation)

    _validate_bands(bands)

    if not operations and not bands:
        raise ValueError(
            f"Rule '{rule['name']}' has no operations or bands."
        )


def load_rules(config_path):
    """
    Load and validate a PES GV 2.0 configuration.
    """
    config_path = Path(config_path)

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a JSON object.")

    allowed_fields = {
        "format",
        "version",
        "language",
        "targets",
        "rules",
    }

    unknown_fields = set(config) - allowed_fields

    if unknown_fields:
        raise ValueError(
            f"Unknown configuration fields: {sorted(unknown_fields)}"
        )

    if config.get("format") != CONFIG_FORMAT:
        raise ValueError("Invalid configuration format.")

    version = config.get("version")

    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != CONFIG_VERSION
    ):
        raise ValueError(
            f"Unsupported configuration version. "
            f"Expected {CONFIG_VERSION}."
        )

    language = config.get("language")

    if not isinstance(language, str) or language not in VALID_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    targets = config.get("targets")

    if not isinstance(targets, dict):
        raise ValueError("'targets' must be an object.")

    unknown_target_fields = set(targets) - {"allPositions", "positions"}

    if unknown_target_fields:
        raise ValueError(
            f"Unknown target fields: {sorted(unknown_target_fields)}"
        )

    all_positions = targets.get("allPositions")
    positions = targets.get("positions")

    if not isinstance(all_positions, bool):
        raise ValueError("'allPositions' must be a boolean.")

    if not isinstance(positions, list):
        raise ValueError("'positions' must be a list.")

    if not all(isinstance(position, str) for position in positions):
        raise ValueError("Each position must be a string.")

    invalid_positions = set(positions) - VALID_POSITIONS

    if invalid_positions:
        raise ValueError(
            f"Invalid positions: {sorted(invalid_positions)}"
        )

    if not all_positions and not positions:
        raise ValueError(
            "Select all positions or at least one position."
        )

    rules = config.get("rules")

    if not isinstance(rules, list):
        raise ValueError("'rules' must be a list.")

    for rule in rules:
        _validate_rule(rule)

    return {
        "format": CONFIG_FORMAT,
        "version": CONFIG_VERSION,
        "language": language,
        "targets": {
            "allPositions": all_positions,
            "positions": positions,
        },
        "rules": rules,
    }


def _calculate_operation(current_value, operation):
    operation_type = operation["operation"]
    value = operation["value"]

    if operation_type == "set":
        result = int(value)

    elif operation_type == "delta":
        result = round(current_value + value)

    elif operation_type == "percentage":
        result = round(
            current_value * (1 + value / 100)
        )

    else:
        raise ValueError(
            f"Unsupported operation: {operation_type}"
        )

    # PES numeric attributes are limited to 40..99.
    return max(40, min(99, int(result)))


def _apply_operation(data, player, operation):
    field_name = operation["field"]
    operation_type = operation["operation"]
    value = operation["value"]

    before = player.get(field_name)

    if field_name in NUMERIC_ATTRIBUTE_FIELDS:
        if not _is_finite_number(before):
            raise ValueError(
                f"Invalid current value for '{field_name}'."
            )

        after = _calculate_operation(before, operation)

    elif field_name in BOOLEAN_SKILL_FIELDS:
        after = value

    elif field_name in REPUTATION_FIELDS:
        before = player.get(field_name)

        if (
            not isinstance(before, int)
            or isinstance(before, bool)
            or not 1 <= before <= 8
        ):
            raise ValueError(
                f"Invalid current value for '{field_name}'."
            )

        after = value

    else:
        raise ValueError(
            f"Unsupported editable field: {field_name}"
        )

    if before == after:
        return None

    apply_edit(
        data,
        player["index"],
        field_name,
        json.dumps(after),
    )

    # Keep the in-memory player synchronized with the TED.
    player[field_name] = after

    return {
        "playerIndex": player["index"],
        "field": field_name,
        "before": before,
        "after": after,
    }


def _apply_operations(data, player, operations, edits):
    for operation in operations:
        edit = _apply_operation(data, player, operation)

        if edit is not None:
            edits.append(edit)


def apply_rules(data: bytearray, rules: dict):
    """
    Apply a PES GV 2.0 configuration to TED player records.

    Rules and operations are executed sequentially.
    """
    edits = []

    players = extract_players(data)

    targets = rules["targets"]

    if targets["allPositions"]:
        selected_players = players
    else:
        selected_players = [
            player
            for player in players
            if player.get("registeredPosition") in targets["positions"]
        ]

    for rule in rules["rules"]:
        if not rule["enabled"]:
            continue

        for original_player in selected_players:
            # Recalculate virtual attributes for each rule.
            # They are never written into the TED record.
            player = prepare_player(original_player)

            if not evaluate_conditions(
                player,
                rule.get("conditions", []),
                rule.get("conditionLogic", "AND"),
            ):
                continue

            # General operations are applied first.
            _apply_operations(
                data,
                original_player,
                rule.get("operations", []),
                edits,
            )

            # Bands are evaluated using the player's current values.
            # The calculated attributes are refreshed before each band.
            for band in rule.get("bands", []):
                current_player = prepare_player(original_player)

                band_value = band["field"]

                if band_value.startswith("calculated."):
                    value = current_player["calculated"].get(
                        band_value.split(".", 1)[1]
                    )
                else:
                    value = current_player.get(band_value)

                for value_range in band["ranges"]:
                    if evaluate_band(
                        value,
                        value_range["min"],
                        value_range["max"],
                    ):
                        _apply_operations(
                            data,
                            original_player,
                            value_range["operations"],
                            edits,
                        )

    return edits
