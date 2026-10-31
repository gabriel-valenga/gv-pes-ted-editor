import pytest

from ted.team_classifier import classify_team


@pytest.mark.parametrize(
    ("team_name", "country_region", "expected"),
    [
        # English
        ("Brazil", "BRA", "national_team"),
        ("Spain", "SPA", "national_team"),
        ("Germany", "GER", "national_team"),

        # Spanish
        ("España", "ESP", "national_team"),
        ("Argentina", "ARG", "national_team"),

        # Portuguese
        ("Brasil", "BRA", "national_team"),

        # Other countries
        ("France", "FRA", "national_team"),
        ("Italia", "ITA", "national_team"),
        ("Deutschland", "DEU", "national_team"),

        # Abbreviation mismatch
        ("España", "BRA", "club"),
        ("Brazil", "ARG", "club"),

        # Names that are not countries
        ("Brasiliense", "BRA", "club"),
        ("Manchester United", "ENG", "club"),

        # Invalid or missing data
        ("", "BRA", "club"),
        ("Brazil", "", "club"),
        ("Brazil", "BR", "club"),
    ],
)
def test_classify_team(team_name, country_region, expected):
    assert classify_team(team_name, country_region) == expected
    