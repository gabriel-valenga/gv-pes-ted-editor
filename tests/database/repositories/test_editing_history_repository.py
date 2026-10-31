
import json
import sqlite3

import pytest

from database.migration_runner import migrate_database
from database.repositories.option_file_repository import (
    create_option_file,
    create_option_file_import,
)
from database.repositories.ted_file_repository import create_ted_file
from database.repositories.ted_version_repository import create_ted_version
from database.repositories.editing_history_repository import (
    create_edit_run,
    get_edit_run,
    update_edit_run_status,
    create_edit_run_ted_file,
    get_edit_run_ted_file,
    list_edit_run_ted_files,
    update_edit_run_ted_file,
    create_edit_run_rule,
    get_edit_run_rule,
    list_edit_run_rules,
    create_edit_change,
    get_edit_change,
    list_edit_changes,
)


@pytest.fixture
def connection(tmp_path):
    """Create a temporary database with the latest schema."""
    database_path = tmp_path / "test.db"

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    migrate_database(connection)

    yield connection

    connection.close()


@pytest.fixture
def ted_file_id(connection):
    """Create a TED file for editing history tests."""
    option_file_id = create_option_file(
        connection,
        "Test Option File",
    )

    import_id = create_option_file_import(
        connection,
        option_file_id,
    )

    return create_ted_file(
        connection,
        import_id=import_id,
        file_name="team.ted",
    )


@pytest.fixture
def source_version_id(connection, ted_file_id):
    """Create an original TED version."""
    return create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=1,
        version_type="original",
        content=b"original content",
    )


@pytest.fixture
def edit_run_id(connection):
    """Create an editing run."""
    return create_edit_run(
        connection,
        config={
            "operation": "bulk_edit",
            "attributes": {
                "speed": -2,
                "shooting": 3,
            },
        },
    )


@pytest.fixture
def run_ted_file_id(
    connection,
    edit_run_id,
    ted_file_id,
    source_version_id,
):
    """Register a TED file in an editing run."""
    return create_edit_run_ted_file(
        connection,
        edit_run_id=edit_run_id,
        ted_file_id=ted_file_id,
        source_version_id=source_version_id,
    )


@pytest.fixture
def rule_id(connection, edit_run_id):
    """Create an editing rule."""
    return create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule={
            "field": "speed",
            "operation": "subtract",
            "value": 2,
        },
        rule_name="Decrease speed",
    )


# Edit Runs


def test_create_edit_run(connection):
    config = {
        "operation": "bulk_edit",
        "attributes": {
            "speed": -2,
            "shooting": 3,
        },
    }

    edit_run_id = create_edit_run(
        connection,
        config=config,
    )

    edit_run = get_edit_run(
        connection,
        edit_run_id,
    )

    assert edit_run is not None
    assert edit_run["status"] == "running"
    assert json.loads(edit_run["config_json"]) == config
    assert edit_run["started_at"] is not None
    assert edit_run["completed_at"] is None


def test_create_edit_run_with_invalid_status(connection):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run(
            connection,
            config={},
            status="invalid",
        )


def test_get_edit_run_not_found(connection):
    edit_run = get_edit_run(
        connection,
        999,
    )

    assert edit_run is None


def test_update_edit_run_status(connection, edit_run_id):
    result = update_edit_run_status(
        connection,
        edit_run_id,
        "completed",
    )

    edit_run = get_edit_run(
        connection,
        edit_run_id,
    )

    assert result is True
    assert edit_run["status"] == "completed"
    assert edit_run["completed_at"] is not None


def test_update_edit_run_status_to_failed(connection, edit_run_id):
    result = update_edit_run_status(
        connection,
        edit_run_id,
        "failed",
    )

    edit_run = get_edit_run(
        connection,
        edit_run_id,
    )

    assert result is True
    assert edit_run["status"] == "failed"
    assert edit_run["completed_at"] is not None


def test_update_edit_run_status_not_found(connection):
    result = update_edit_run_status(
        connection,
        999,
        "completed",
    )

    assert result is False


def test_update_edit_run_status_with_invalid_status(
    connection,
    edit_run_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        update_edit_run_status(
            connection,
            edit_run_id,
            "invalid",
        )


# Edit Run TED Files


def test_create_edit_run_ted_file(
    connection,
    edit_run_id,
    ted_file_id,
    source_version_id,
):
    run_ted_file_id = create_edit_run_ted_file(
        connection,
        edit_run_id=edit_run_id,
        ted_file_id=ted_file_id,
        source_version_id=source_version_id,
    )

    run_ted_file = get_edit_run_ted_file(
        connection,
        run_ted_file_id,
    )

    assert run_ted_file is not None
    assert run_ted_file["edit_run_id"] == edit_run_id
    assert run_ted_file["ted_file_id"] == ted_file_id
    assert run_ted_file["source_version_id"] == source_version_id
    assert run_ted_file["output_version_id"] is None
    assert run_ted_file["status"] == "pending"
    assert run_ted_file["started_at"] is None


def test_create_edit_run_ted_file_with_invalid_status(
    connection,
    edit_run_id,
    ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_ted_file(
            connection,
            edit_run_id=edit_run_id,
            ted_file_id=ted_file_id,
            status="invalid",
        )


def test_create_edit_run_ted_file_with_invalid_edit_run(
    connection,
    ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_ted_file(
            connection,
            edit_run_id=999,
            ted_file_id=ted_file_id,
        )


def test_create_edit_run_ted_file_with_invalid_ted_file(
    connection,
    edit_run_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_ted_file(
            connection,
            edit_run_id=edit_run_id,
            ted_file_id=999,
        )


def test_create_duplicate_ted_file_in_same_run(
    connection,
    run_ted_file_id,
    edit_run_id,
    ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_ted_file(
            connection,
            edit_run_id=edit_run_id,
            ted_file_id=ted_file_id,
        )


def test_create_same_ted_file_in_different_runs(
    connection,
    ted_file_id,
):
    first_run_id = create_edit_run(
        connection,
        config={},
    )

    second_run_id = create_edit_run(
        connection,
        config={},
    )

    first_entry_id = create_edit_run_ted_file(
        connection,
        edit_run_id=first_run_id,
        ted_file_id=ted_file_id,
    )

    second_entry_id = create_edit_run_ted_file(
        connection,
        edit_run_id=second_run_id,
        ted_file_id=ted_file_id,
    )

    assert first_entry_id != second_entry_id


def test_get_edit_run_ted_file_not_found(connection):
    result = get_edit_run_ted_file(
        connection,
        999,
    )

    assert result is None


def test_list_edit_run_ted_files(
    connection,
    edit_run_id,
    ted_file_id,
    run_ted_file_id,
):
    another_option_file_id = create_option_file(
        connection,
        "Another Option File",
    )

    another_import_id = create_option_file_import(
        connection,
        another_option_file_id,
    )

    another_ted_file_id = create_ted_file(
        connection,
        import_id=another_import_id,
        file_name="another_team.ted",
    )

    another_entry_id = create_edit_run_ted_file(
        connection,
        edit_run_id=edit_run_id,
        ted_file_id=another_ted_file_id,
    )

    entries = list_edit_run_ted_files(
        connection,
        edit_run_id,
    )

    assert len(entries) == 2
    assert {
        entry["id"]
        for entry in entries
    } == {run_ted_file_id, another_entry_id}


def test_list_edit_run_ted_files_empty(
    connection,
    edit_run_id,
):
    entries = list_edit_run_ted_files(
        connection,
        edit_run_id,
    )

    assert entries == []


def test_update_edit_run_ted_file(
    connection,
    run_ted_file_id,
    ted_file_id,
    source_version_id,
):
    output_version_id = create_ted_version(
        connection,
        ted_file_id=ted_file_id,
        version_number=2,
        version_type="edited",
        content=b"edited content",
    )

    result = update_edit_run_ted_file(
        connection,
        run_ted_file_id=run_ted_file_id,
        status="completed",
        source_version_id=source_version_id,
        output_version_id=output_version_id,
    )

    entry = get_edit_run_ted_file(
        connection,
        run_ted_file_id,
    )

    assert result is True
    assert entry["status"] == "completed"
    assert entry["source_version_id"] == source_version_id
    assert entry["output_version_id"] == output_version_id
    assert entry["completed_at"] is not None


def test_update_edit_run_ted_file_not_found(connection):
    result = update_edit_run_ted_file(
        connection,
        run_ted_file_id=999,
        status="completed",
    )

    assert result is False


def test_update_edit_run_ted_file_with_invalid_status(
    connection,
    run_ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        update_edit_run_ted_file(
            connection,
            run_ted_file_id=run_ted_file_id,
            status="invalid",
        )


# Edit Run Rules


def test_create_edit_run_rule(connection, edit_run_id):
    rule = {
        "field": "speed",
        "operation": "subtract",
        "value": 2,
    }

    rule_id = create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule=rule,
        rule_name="Decrease speed",
    )

    saved_rule = get_edit_run_rule(
        connection,
        rule_id,
    )

    assert saved_rule is not None
    assert saved_rule["edit_run_id"] == edit_run_id
    assert saved_rule["rule_order"] == 1
    assert saved_rule["rule_name"] == "Decrease speed"
    assert json.loads(saved_rule["rule_json"]) == rule
    assert saved_rule["created_at"] is not None


def test_create_edit_run_rule_without_name(
    connection,
    edit_run_id,
):
    rule_id = create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule={"field": "speed"},
    )

    saved_rule = get_edit_run_rule(
        connection,
        rule_id,
    )

    assert saved_rule["rule_name"] is None


def test_create_edit_run_rule_with_invalid_edit_run(connection):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_rule(
            connection,
            edit_run_id=999,
            rule_order=1,
            rule={},
        )


def test_create_duplicate_rule_order(
    connection,
    edit_run_id,
):
    create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule={"field": "speed"},
    )

    with pytest.raises(sqlite3.IntegrityError):
        create_edit_run_rule(
            connection,
            edit_run_id=edit_run_id,
            rule_order=1,
            rule={"field": "shooting"},
        )


def test_same_rule_order_in_different_runs(connection):
    first_run_id = create_edit_run(
        connection,
        config={},
    )

    second_run_id = create_edit_run(
        connection,
        config={},
    )

    first_rule_id = create_edit_run_rule(
        connection,
        edit_run_id=first_run_id,
        rule_order=1,
        rule={"field": "speed"},
    )

    second_rule_id = create_edit_run_rule(
        connection,
        edit_run_id=second_run_id,
        rule_order=1,
        rule={"field": "shooting"},
    )

    assert first_rule_id != second_rule_id


def test_get_edit_run_rule_not_found(connection):
    rule = get_edit_run_rule(
        connection,
        999,
    )

    assert rule is None


def test_list_edit_run_rules(connection, edit_run_id):
    second_rule_id = create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=2,
        rule={"field": "shooting"},
    )

    first_rule_id = create_edit_run_rule(
        connection,
        edit_run_id=edit_run_id,
        rule_order=1,
        rule={"field": "speed"},
    )

    rules = list_edit_run_rules(
        connection,
        edit_run_id,
    )

    assert len(rules) == 2
    assert [
        rule["rule_order"]
        for rule in rules
    ] == [1, 2]

    assert [
        rule["id"]
        for rule in rules
    ] == [first_rule_id, second_rule_id]


def test_list_edit_run_rules_empty(
    connection,
    edit_run_id,
):
    rules = list_edit_run_rules(
        connection,
        edit_run_id,
    )

    assert rules == []


# Edit Changes


def test_create_edit_change(
    connection,
    run_ted_file_id,
    rule_id,
):
    change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        rule_id=rule_id,
        player_index=10,
        player_id=12345,
        field_name="speed",
        old_value=85,
        new_value=83,
    )

    change = get_edit_change(
        connection,
        change_id,
    )

    assert change is not None
    assert change["edit_run_ted_file_id"] == run_ted_file_id
    assert change["edit_run_rule_id"] == rule_id
    assert change["player_index"] == 10
    assert change["player_id"] == 12345
    assert change["field_name"] == "speed"
    assert json.loads(change["old_value"]) == 85
    assert json.loads(change["new_value"]) == 83
    assert change["created_at"] is not None


def test_create_edit_change_without_rule(
    connection,
    run_ted_file_id,
):
    change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        player_index=5,
        field_name="shooting",
        old_value=70,
        new_value=75,
    )

    change = get_edit_change(
        connection,
        change_id,
    )

    assert change is not None
    assert change["edit_run_rule_id"] is None


def test_create_edit_change_with_none_values(
    connection,
    run_ted_file_id,
):
    change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        player_index=5,
        field_name="playerName",
        old_value=None,
        new_value=None,
    )

    change = get_edit_change(
        connection,
        change_id,
    )

    assert change["old_value"] is None
    assert change["new_value"] is None


def test_create_edit_change_preserves_value_types(
    connection,
    run_ted_file_id,
):
    old_value = {
        "enabled": True,
        "values": [1, 2, 3],
    }

    new_value = {
        "enabled": False,
        "values": [4, 5, 6],
    }

    change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        player_index=5,
        field_name="customField",
        old_value=old_value,
        new_value=new_value,
    )

    change = get_edit_change(
        connection,
        change_id,
    )

    assert json.loads(change["old_value"]) == old_value
    assert json.loads(change["new_value"]) == new_value


def test_create_edit_change_with_invalid_run_ted_file(
    connection,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_change(
            connection,
            run_ted_file_id=999,
            player_index=5,
            field_name="speed",
            old_value=80,
            new_value=85,
        )


def test_create_edit_change_with_invalid_rule(
    connection,
    run_ted_file_id,
):
    with pytest.raises(sqlite3.IntegrityError):
        create_edit_change(
            connection,
            run_ted_file_id=run_ted_file_id,
            rule_id=999,
            player_index=5,
            field_name="speed",
            old_value=80,
            new_value=85,
        )


def test_create_edit_change_with_rule_from_another_run(
    connection,
    run_ted_file_id,
):
    another_run_id = create_edit_run(
        connection,
        config={},
    )

    another_rule_id = create_edit_run_rule(
        connection,
        edit_run_id=another_run_id,
        rule_order=1,
        rule={"field": "speed"},
    )

    with pytest.raises(sqlite3.IntegrityError):
        create_edit_change(
            connection,
            run_ted_file_id=run_ted_file_id,
            rule_id=another_rule_id,
            player_index=5,
            field_name="speed",
            old_value=80,
            new_value=85,
        )


def test_get_edit_change_not_found(connection):
    change = get_edit_change(
        connection,
        999,
    )

    assert change is None


def test_list_edit_changes(
    connection,
    run_ted_file_id,
    rule_id,
):
    first_change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        rule_id=rule_id,
        player_index=1,
        field_name="speed",
        old_value=80,
        new_value=78,
    )

    second_change_id = create_edit_change(
        connection,
        run_ted_file_id=run_ted_file_id,
        rule_id=rule_id,
        player_index=2,
        field_name="shooting",
        old_value=70,
        new_value=73,
    )

    changes = list_edit_changes(
        connection,
        run_ted_file_id,
    )

    assert len(changes) == 2
    assert [
        change["id"]
        for change in changes
    ] == [first_change_id, second_change_id]


def test_list_edit_changes_empty(
    connection,
    run_ted_file_id,
):
    changes = list_edit_changes(
        connection,
        run_ted_file_id,
    )

    assert changes == []
