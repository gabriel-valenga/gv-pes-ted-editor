"""Classify PES TED teams using localized country names and game abbreviations."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "countries.json"
)


def normalize_text(value: str) -> str:
    """Normalize text for case-, accent-, and whitespace-insensitive matching."""
    value = unicodedata.normalize("NFKD", value.strip().casefold())

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return re.sub(r"\s+", " ", value)


def country_abbreviation(country_name: str) -> str:
    """Return the first three letters after removing accents and separators."""
    normalized = normalize_text(country_name)

    letters = "".join(
        char
        for char in normalized
        if char.isalpha()
    )

    return letters[:3].upper()


def load_country_catalog(
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> dict[str, Any]:
    """Load the local multilingual country catalog."""
    with Path(catalog_path).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_country_match(
    team_name: str,
    catalog: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Find an exact localized country-name match using language priority."""
    normalized_team_name = normalize_text(team_name)

    for language in catalog["language_priority"]:
        matches = [
            country
            for country in catalog["countries"]
            if normalize_text(
                country["names"].get(language, "")
            ) == normalized_team_name
        ]

        if len(matches) == 1:
            return matches[0], language

        if len(matches) > 1:
            return None, language

    return None, None


def classify_team(
    team_name: str,
    country_region: str,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> str:
    """
    Classify a team as 'national_team' or 'club'.

    A national team requires an exact localized country-name match
    and a matching three-letter abbreviation derived from that name.
    """
    if not isinstance(team_name, str) or not team_name.strip():
        return "club"

    if not isinstance(country_region, str) or not country_region.strip():
        return "club"

    catalog = load_country_catalog(catalog_path)

    country, language = find_country_match(
        team_name,
        catalog,
    )

    if country is None:
        return "club"

    localized_name = country["names"][language]

    expected_abbreviation = country_abbreviation(
        localized_name
    )

    actual_abbreviation = "".join(
        char
        for char in normalize_text(country_region)
        if char.isalpha()
    ).upper()

    if len(actual_abbreviation) != 3:
        return "club"

    if actual_abbreviation == expected_abbreviation:
        return "national_team"

    return "club"
