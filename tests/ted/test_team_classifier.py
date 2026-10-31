import json
import pytest
from ted.team_classifier import classify_team


@pytest.fixture
def catalog_path(tmp_path):
    """Create a temporary country catalog for classifier tests."""
    catalog = {
        "language_priority": ["en"],
        "countries": [
            {
                "code": "FR",
                "code_alpha3": "FRA",
                "editor_code": "FRA",
                "names": {
                    "en": "France",
                },
            },
            {
                "code": "DE",
                "code_alpha3": "DEU",
                "editor_code": None,
                "names": {
                    "en": "Germany",
                },
            },
        ],
    }

    path = tmp_path / "countries.json"
    path.write_text(
        json.dumps(catalog, ensure_ascii=False),
        encoding="utf-8",
    )

    return path


def test_classify_country_using_editor_code(catalog_path):
    assert classify_team("France", "FRA", catalog_path) == "national_team"


def test_editor_code_mismatch_returns_club(catalog_path):
    assert classify_team("France", "GER", catalog_path) == "club"


def test_classify_country_using_fallback(catalog_path):
    assert classify_team("Germany", "GER", catalog_path) == "national_team"


def test_fallback_mismatch_returns_club(catalog_path):
    assert classify_team("Germany", "FRA", catalog_path) == "club"


def test_non_country_name_returns_club(catalog_path):
    assert classify_team("Manchester United", "ENG", catalog_path) == "club"


@pytest.mark.parametrize(
    ("team_name", "country_region"),
    [
        ("", "FRA"),
        ("France", ""),
        ("   ", "FRA"),
        ("France", "   "),
    ],
)
def test_empty_values_return_club(
    team_name,
    country_region,
    catalog_path,
):
    assert classify_team(
        team_name,
        country_region,
        catalog_path,
    ) == "club"