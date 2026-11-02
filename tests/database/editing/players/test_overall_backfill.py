
from database.editing.players.overall_backfill import (
    OVERALL_CALCULATION_VERSION,
    backfill_player_overalls,
)

from database.repositories.player_overall_repository import (
    get_player_position_overalls,
    get_player_registered_overall,
)

from editing.players.overall import POSITION_WEIGHTS


def test_backfill_calculates_all_position_overalls(
    db_connection,
    complete_player,
):
    """Calculate and persist Overalls for all supported positions."""

    stats = backfill_player_overalls(db_connection)

    player_record_id = complete_player["id"]

    results = get_player_position_overalls(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=OVERALL_CALCULATION_VERSION,
    )

    registered_result = get_player_registered_overall(
        connection=db_connection,
        player_record_id=player_record_id,
        calculation_version=OVERALL_CALCULATION_VERSION,
    )

    assert stats["players_processed"] == 1
    assert stats["position_overalls_inserted"] == len(POSITION_WEIGHTS)
    assert stats["registered_overalls_inserted"] == 1

    assert len(results) == len(POSITION_WEIGHTS)
    assert registered_result is not None
    assert registered_result["registered_position"] == "CF"

    assert stats["invalid_position_results"] == 0
    assert stats["invalid_registered_results"] == 0


def test_backfill_is_idempotent(
    db_connection,
    complete_player,
):
    """Avoid duplicate records when the backfill runs again."""

    first_run = backfill_player_overalls(db_connection)
    second_run = backfill_player_overalls(db_connection)

    assert first_run["position_overalls_inserted"] == len(POSITION_WEIGHTS)
    assert first_run["registered_overalls_inserted"] == 1

    assert second_run["position_overalls_inserted"] == 0
    assert second_run["registered_overalls_inserted"] == 0

    assert second_run["position_overalls_skipped"] == len(POSITION_WEIGHTS)
    assert second_run["registered_overalls_skipped"] == 1


def test_backfill_skips_players_with_insufficient_attributes(
    db_connection,
    sample_player,
):
    """Skip Overall calculations when required attributes are missing."""

    stats = backfill_player_overalls(db_connection)

    assert stats["players_processed"] == 1

    assert stats["position_overalls_inserted"] == 0
    assert stats["registered_overalls_inserted"] == 0

    assert stats["invalid_position_results"] == len(POSITION_WEIGHTS)
    assert stats["invalid_registered_results"] == 1
