
import json

import pytest

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
                "code": "FR",
                "editor_code": "FRA",
                "editor_id": 208,
                "names": {"en": "France"},
            },
        ],
    }

    catalog_path = tmp_path / "countries.json"
    catalog_path.write_text(
        json.dumps(catalog),
        encoding="utf-8",
    )

    return catalog_path


@pytest.mark.parametrize(
    ("team_name", "country_id"),
    [
        ("Brazil", 146),
        ("France", 208),
        (" brazil ", 146),
        ("FRANCE", 208),
    ],
)
def test_classify_matching_country(
    country_catalog,
    team_name,
    country_id,
):
    assert classify_team(
        team_name,
        country_id,
        country_catalog,
    ) == "national_team"


@pytest.mark.parametrize(
    ("team_name", "country_id"),
    [
        ("Chelsea", 204),
        ("Atlético Mineiro", 150),
        ("Brazil", 204),
        ("France", 146),
        ("Unknown Team", 146),
    ],
)
def test_non_matching_country_returns_club(
    country_catalog,
    team_name,
    country_id,
):
    assert classify_team(
        team_name,
        country_id,
        country_catalog,
    ) == "club"


@pytest.mark.parametrize(
    ("team_name", "country_id"),
    [
        ("", 146),
        ("   ", 146),
        ("Brazil", None),
        ("Brazil", 0),
    ],
)
def test_empty_or_invalid_values_return_club(
    country_catalog,
    team_name,
    country_id,
):
    assert classify_team(
        team_name,
        country_id,
        country_catalog,
    ) == "club"
