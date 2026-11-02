
import sqlite3

from database.repositories.player_overall_repository import (
    create_player_position_overall,
    create_player_registered_overall,
)
from editing.players.overall import (
    POSITION_WEIGHTS,
    calculate_overall,
)

OVERALL_CALCULATION_VERSION = "1"


def _row_to_dict(row: sqlite3.Row, columns: list[str]) -> dict:
    """Convert a database row into a dictionary."""
    if isinstance(row, sqlite3.Row):
        return dict(row)

    return dict(zip(columns, row))


def backfill_player_overalls(
    connection: sqlite3.Connection,
) -> dict:
    """Calculate and persist missing player Overalls."""

    cursor = connection.execute(
        "SELECT * FROM player_records ORDER BY id"
    )

    columns = [description[0] for description in cursor.description]
    player_rows = cursor.fetchall()

    stats = {
        "players_processed": 0,
        "position_overalls_inserted": 0,
        "position_overalls_skipped": 0,
        "registered_overalls_inserted": 0,
        "registered_overalls_skipped": 0,
        "invalid_position_results": 0,
        "invalid_registered_results": 0,
    }

    with connection:
        for row in player_rows:
            player = _row_to_dict(row, columns)
            player_record_id = player["id"]

            stats["players_processed"] += 1

            # Calculate Overalls for all supported positions.
            for position in POSITION_WEIGHTS:
                overall = calculate_overall(
                    player,
                    position=position,
                )

                if overall is None:
                    stats["invalid_position_results"] += 1
                    continue

                inserted = create_player_position_overall(
                    connection=connection,
                    player_record_id=player_record_id,
                    position=position,
                    overall=overall,
                    calculation_version=OVERALL_CALCULATION_VERSION,
                )

                if inserted:
                    stats["position_overalls_inserted"] += 1
                else:
                    stats["position_overalls_skipped"] += 1

            # Calculate Overall for the registered position.
            registered_position = player.get("registeredPosition")

            if registered_position not in POSITION_WEIGHTS:
                stats["invalid_registered_results"] += 1
                continue

            registered_overall = calculate_overall(player)

            if registered_overall is None:
                stats["invalid_registered_results"] += 1
                continue

            inserted = create_player_registered_overall(
                connection=connection,
                player_record_id=player_record_id,
                registered_position=registered_position,
                overall=registered_overall,
                calculation_version=OVERALL_CALCULATION_VERSION,
            )

            if inserted:
                stats["registered_overalls_inserted"] += 1
            else:
                stats["registered_overalls_skipped"] += 1

    return stats
