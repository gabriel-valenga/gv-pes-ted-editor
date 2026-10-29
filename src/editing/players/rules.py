
import json
import math
from pathlib import Path
from editing.players.operations import apply_edit
from ted.fields import PLAYER_FIELDS
from ted.reader import extract_players

CONFIG_FORMAT = "pes-gv-bulk-tools-config"
CONFIG_VERSION = 1

VALID_LANGUAGES = {"pt-BR", "en"}

VALID_POSITIONS = {
    "GK", "CB", "DMF", "CMF", "LB",
    "AMF", "RWF", "LWF", "RB", "CF",
}


def load_rules(file_path: str | Path) -> dict:
    """Load and validate a JSON editing rules file."""

    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(config, dict):
        raise ValueError("The configuration must be a JSON object.")

    if config.get("format") != CONFIG_FORMAT:
        raise ValueError("Unrecognized configuration format.")

    if config.get("version") != CONFIG_VERSION:
        raise ValueError("Unsupported configuration version.")

    if config.get("language") not in VALID_LANGUAGES:
        raise ValueError("Invalid language. Use 'pt-BR' or 'en'.")

    targets = config.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("'targets' must be an object.")

    if not isinstance(targets.get("allPositions"), bool):
        raise ValueError("'targets.allPositions' must be a boolean.")

    positions = targets.get("positions")
    if not isinstance(positions, list):
        raise ValueError("'targets.positions' must be a list.")

    if any(
        not isinstance(position, str) or position not in VALID_POSITIONS
        for position in positions
    ):
        raise ValueError("The configuration contains an invalid position.")

    attributes = config.get("attributes")
    if not isinstance(attributes, list):
        raise ValueError("'attributes' must be a list.")

    normalized_attributes = []

    for index, rule in enumerate(attributes):
        if not isinstance(rule, dict):
            raise ValueError(f"Invalid attribute rule at index {index}.")                
        field = rule.get("field")

        if not isinstance(field, str) or not field:
            raise ValueError(f"Invalid field in attribute rule {index}.")

        has_delta = "delta" in rule
        has_value = "value" in rule

        if has_delta == has_value:
            raise ValueError(
                f"Attribute rule {index} must contain exactly one "
                "of 'delta' or 'value'."
            )

        operation = "delta" if has_delta else "set"
        raw_value = rule[operation]

        if isinstance(raw_value, bool) or not isinstance(
            raw_value, (int, float, str)
        ):
            raise ValueError(
                f"Invalid numeric value in attribute rule {index}."
            )

        try:
            numeric_value = float(raw_value)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid numeric value in attribute rule {index}."
            ) from exc

        if not math.isfinite(numeric_value):
            raise ValueError(
                f"The value in attribute rule {index} must be finite."
            )

        if not numeric_value.is_integer():
            raise ValueError(
                f"The value in attribute rule {index} must be an integer."
            )

        normalized_attributes.append({
            "field": field,
            "operation": operation,
            "value": numeric_value,
        })
    skills = config.get("specialSkills")
    if not isinstance(skills, dict):
        raise ValueError("'specialSkills' must be an object.")

    normalized_skills = {}

    for key, rule in skills.items():
        if not isinstance(key, str) or not isinstance(rule, dict):
            raise ValueError("Invalid special skill rule.")

        if not isinstance(rule.get("checked"), bool):
            raise ValueError(
                f"'checked' must be a boolean for skill '{key}'."
            )

        if rule.get("action") not in {"true", "false"}:
            raise ValueError(
                f"Invalid 'action' for skill '{key}'."
            )

        normalized_skills[key] = {
            "checked": rule["checked"],
            "action": rule["action"],
        }

    reputation = config.get(
        "reputation",
        {"enabled": False, "bands": []},
    )

    if not isinstance(reputation, dict):
        raise ValueError("'reputation' must be an object.")

    if not isinstance(reputation.get("enabled"), bool):
        raise ValueError("'reputation.enabled' must be a boolean.")

    bands = reputation.get("bands")
    if not isinstance(bands, list):
        raise ValueError("'reputation.bands' must be a list.")

    normalized_bands = []

    for index, band in enumerate(bands):
        if not isinstance(band, dict):
            raise ValueError(
                f"Invalid reputation band at index {index}."
            )

        values = (
            "overallStart",
            "overallEnd",
            "reputationStart",
            "reputationEnd",
        )

        try:
            normalized = {
                key: float(band[key])
                for key in values
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid values in reputation band {index}."
            ) from exc

        if not all(
            math.isfinite(value)
            for value in normalized.values()
        ):
            raise ValueError(
                f"Non-finite values in reputation band {index}."
            )

        if normalized["overallStart"] > normalized["overallEnd"]:
            raise ValueError(
                f"The overall range is reversed in reputation band {index}."
            )

        if (
            normalized["reputationStart"]
            > normalized["reputationEnd"]
        ):
            raise ValueError(
                f"The reputation range is reversed in band {index}."
            )

        normalized_bands.append(normalized)

    if reputation["enabled"] and not normalized_bands:
        raise ValueError(
            "Reputation adjustment is enabled, but no bands are configured."
        )

    return {
        "language": config["language"],
        "targets": {
            "allPositions": targets["allPositions"],
            "positions": list(dict.fromkeys(positions)),
        },
        "attributes": normalized_attributes,
        "specialSkills": normalized_skills,
        "reputation": {
            "enabled": reputation["enabled"],
            "bands": normalized_bands,
        },
    }


def apply_rules(data: bytearray, rules: dict) -> list[dict]:
    """Apply configured attribute and special skill rules to selected players."""

    if rules["reputation"]["enabled"]:
        raise NotImplementedError(
            "Reputation rules require an overall rating calculation, "
            "which is not implemented yet."
        )

    fields = {field["key"]: field for field in PLAYER_FIELDS}

    # Identify seven-bit numeric player attributes.
    attribute_fields = {
        key: field
        for key, field in fields.items()
        if field.get("type") == "bitfield"
        and field.get("lengthInBit") == 7
        and not field.get("transform")
    }

    players = extract_players(data)
    positions = set(rules["targets"]["positions"])
    all_positions = rules["targets"]["allPositions"]

    selected_players = [
        player
        for player in players
        if all_positions
        or player.get("registeredPosition") in positions
    ]

    edits = []

    for player in selected_players:
        player_index = player["index"]

        # Apply numeric attribute adjustments.
        for rule in rules["attributes"]:
            field_name = rule["field"]

            if field_name not in attribute_fields:
                raise ValueError(
                    f"Unsupported numeric attribute: {field_name}"
                )

            before = player.get(field_name)

            if isinstance(before, bool) or not isinstance(before, (int, float)):
                raise ValueError(
                    f"Attribute '{field_name}' has a non-numeric value "
                    f"for player index {player_index}."
                )

            if rule["operation"] == "delta":
                after = round(before + rule["value"])
            else:
                after = int(rule["value"])

            after = max(40, min(99, after))

            if after == before:
                continue

            apply_edit(
                data,
                player_index,
                field_name,
                json.dumps(after),
            )

            edits.append({
                "index": player_index,
                "field": field_name,
                "before": before,
                "after": after,
                "source": "config",
            })

            # Keep the in-memory player data up to date for subsequent rules.
            player[field_name] = after

        # Apply selected special skill rules.
        for skill_name, skill_rule in rules["specialSkills"].items():
            if not skill_rule["checked"]:
                continue

            field = fields.get(skill_name)

            if (
                field is None
                or field.get("type") != "bitfield"
                or field.get("lengthInBit") != 1
                or field.get("transform") != "j"
            ):
                raise ValueError(
                    f"Unsupported special skill: {skill_name}"
                )

            before = player.get(skill_name)
            after = skill_rule["action"] == "true"

            if not isinstance(before, bool):
                raise ValueError(
                    f"Skill '{skill_name}' has an invalid value "
                    f"for player index {player_index}."
                )

            if after == before:
                continue

            apply_edit(
                data,
                player_index,
                skill_name,
                json.dumps(after),
            )

            edits.append({
                "index": player_index,
                "field": skill_name,
                "before": before,
                "after": after,
                "source": "config",
            })

            player[skill_name] = after

    return edits

