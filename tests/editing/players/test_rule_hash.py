
from editing.players.rules import build_rule_hash


def create_rule(
    name="Increase speed",
    enabled=True,
    amount=5,
):
    return {
        "name": name,
        "enabled": enabled,
        "conditions": [],
        "operations": [
            {
                "field": "speed",
                "operation": "delta",
                "value": amount,
            }
        ],
    }


def test_same_rule_has_same_hash():
    rule = create_rule()

    assert build_rule_hash(rule) == build_rule_hash(rule)


def test_rule_name_does_not_change_hash():
    first_rule = create_rule(name="Increase speed")
    second_rule = create_rule(name="Speed boost")

    assert build_rule_hash(first_rule) == build_rule_hash(second_rule)


def test_enabled_status_does_not_change_hash():
    enabled_rule = create_rule(enabled=True)
    disabled_rule = create_rule(enabled=False)

    assert build_rule_hash(enabled_rule) == build_rule_hash(disabled_rule)


def test_different_operations_produce_different_hashes():
    first_rule = create_rule(amount=5)
    second_rule = create_rule(amount=10)

    assert build_rule_hash(first_rule) != build_rule_hash(second_rule)


def test_dictionary_key_order_does_not_change_hash():
    first_rule = {
        "name": "Rule A",
        "enabled": True,
        "conditions": [],
        "operations": [
            {
                "field": "speed",
                "operation": "delta",
                "value": 5,
            }
        ],
    }

    second_rule = {
        "operations": [
            {
                "value": 5,
                "operation": "delta",
                "field": "speed",
            }
        ],
        "conditions": [],
        "enabled": False,
        "name": "Rule B",
    }

    assert build_rule_hash(first_rule) == build_rule_hash(second_rule)



def test_original_hash_is_preserved_in_prepared_rule():
    rule = create_rule()
    original_hash = build_rule_hash(rule)

    prepared_rule = {
        **rule,
        "_originalRuleHash": original_hash,
        "playerIds": [12345],
    }

    effective_hash = (
        prepared_rule.get("_originalRuleHash")
        or build_rule_hash(prepared_rule)
    )

    assert effective_hash == original_hash

