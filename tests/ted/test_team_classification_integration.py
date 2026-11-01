
import json

import pytest

from ted.reader import get_team_summary
from ted.team_classifier import classify_team


@pytest.fixture
def country_catalog(tmp_path):
    catalog = {
        "language_priority": ["en"],
        "countries": [
            {
                "code": "BR",
                "editor_code": "BRA",
                "editor_id": 146,
                "names": {"en": "Brazil"},
            },
            {
                "code": "GB-ENG",
                "editor_code": "ENG",
                "editor_id": 204,
                "names": {"en": "England"},
            },
            {
                "code": "PY",
                "editor_code": "PAR",
                "editor_id": 150,
                "names": {"en": "Paraguay"},
            },
        ],
    }

    catalog_path = tmp_path / "countries.json"
    catalog_path.write_text(
        json.dumps(catalog),
        encoding="utf-8",
    )

    return catalog_path


def create_team_data(team_name: str, country_id: int) -> bytearray:
    """Create synthetic TED data containing team name and country ID."""
    data = bytearray(1055)

    team_name_bytes = team_name.encode("utf-8")
    data[184:184 + len(team_name_bytes)] = team_name_bytes

    data[0x005E:0x0060] = country_id.to_bytes(
        2,
        byteorder="little",
    )

    return data


@pytest.mark.parametrize(
    ("team_name", "country_id", "expected_type"),
    [
        ("Brazil", 146, "national_team"),
        ("Chelsea", 204, "club"),
        ("Atlético Mineiro", 150, "club"),
    ],
)
def test_classify_team_from_extracted_country_id(
    country_catalog,
    team_name,
    country_id,
    expected_type,
):
    data = create_team_data(team_name, country_id)

    team_summary = get_team_summary(data)

    team_type = classify_team(
        team_summary["teamName"],
        team_summary["countryId"],
        country_catalog,
    )

    assert team_summary["teamName"].strip() == team_name
    assert team_summary["countryId"] == country_id
    assert team_type == expected_type
