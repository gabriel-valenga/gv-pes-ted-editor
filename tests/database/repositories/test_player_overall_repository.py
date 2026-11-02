
from database.repositories.player_overall_repository import (
    create_player_position_overall,
    create_player_registered_overall,
    get_player_position_overalls,
    get_player_registered_overall,
)


CALCULATION_VERSION = "1"


def test_create_and_get_player_position_overall(
    db_connection,
    sample_player,
):
    """Persist and retrieve a player's Overall for a specific position."""

    player_record_id = sample_player["id"]

    inserted = create_player_position_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        position="CF",
        overall=85,
        calculation_version=CALCULATION_VERSION,
    )

    assert inserted is True

    results = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=CALCULATION_VERSION,
    )

    assert len(results) == 1
    assert results[0]["position"] == "CF"
    assert results[0]["overall"] == 85


def test_create_and_get_player_registered_overall(
    db_connection,
    sample_player,
):
    """Persist and retrieve a player's registered Overall."""

    player_record_id = sample_player["id"]

    inserted = create_player_registered_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        registered_position="CF",
        overall=85,
        calculation_version=CALCULATION_VERSION,
    )

    assert inserted is True

    result = get_player_registered_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=CALCULATION_VERSION,
    )

    assert result is not None
    assert result["registered_position"] == "CF"
    assert result["overall"] == 85


def test_position_overall_does_not_create_duplicates(
    db_connection,
    sample_player,
):
    """Ignore duplicate position Overall records for the same version."""

    player_record_id = sample_player["id"]

    arguments = {
        "connection": db_connection,
        "player_record_id": player_record_id,
        "position": "CF",
        "overall": 85,
        "calculation_version": CALCULATION_VERSION,
    }

    first_insert = create_player_position_overall(**arguments)
    second_insert = create_player_position_overall(**arguments)

    assert first_insert is True
    assert second_insert is False

    results = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=CALCULATION_VERSION,
    )

    assert len(results) == 1


def test_registered_overall_does_not_create_duplicates(
    db_connection,
    sample_player,
):
    """Ignore duplicate registered Overall records for the same version."""

    player_record_id = sample_player["id"]

    arguments = {
        "connection": db_connection,
        "player_record_id": player_record_id,
        "registered_position": "CF",
        "overall": 85,
        "calculation_version": CALCULATION_VERSION,
    }

    first_insert = create_player_registered_overall(**arguments)
    second_insert = create_player_registered_overall(**arguments)

    assert first_insert is True
    assert second_insert is False

    result = get_player_registered_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=CALCULATION_VERSION,
    )

    assert result is not None


def test_position_overall_supports_multiple_positions(
    db_connection,
    sample_player,
):
    """Store multiple position Overalls for the same player."""

    player_record_id = sample_player["id"]

    positions = {
        "CF": 85,
        "SS": 83,
        "AMF": 80,
    }

    for position, overall in positions.items():
        create_player_position_overall(
            connection=db_connection,
            player_record_id=player_record_id,
            position=position,
            overall=overall,
            calculation_version=CALCULATION_VERSION,
        )

    results = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=CALCULATION_VERSION,
    )

    stored_results = {
        row["position"]: row["overall"]
        for row in results
    }

    assert stored_results == positions


def test_position_overall_supports_multiple_calculation_versions(
    db_connection,
    sample_player,
):
    """Preserve results from different calculation versions."""

    player_record_id = sample_player["id"]

    create_player_position_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        position="CF",
        overall=85,
        calculation_version="1",
    )

    create_player_position_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        position="CF",
        overall=87,
        calculation_version="2",
    )

    version_1 = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version="1",
    )

    version_2 = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version="2",
    )

    assert version_1[0]["overall"] == 85
    assert version_2[0]["overall"] == 87
