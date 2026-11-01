
"""Classify PES TED teams using country names and TEditor country IDs."""

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


def load_country_catalog(
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> dict[str, Any]:
    """Load the local multilingual country catalog."""
    with Path(catalog_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def find_country_match(
    team_name: str,
    catalog: dict[str, Any],
) -> dict[str, Any] | None:
    """Find an exact localized country-name match."""
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
            return matches[0]

        if len(matches) > 1:
            return None

    return None


def classify_team(
    team_name: str,
    country_id: int | None,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> str:
    """
    Classify a team using its localized country name and TEditor country ID.

    Both values must match the same country in the catalog.
    """
    if not isinstance(team_name, str) or not team_name.strip():
        return "club"

    if not isinstance(country_id, int) or isinstance(country_id, bool):
        return "club"

    catalog = load_country_catalog(catalog_path)

    country = find_country_match(team_name, catalog)

    if country is None:
        return "club"

    if country.get("editor_id") != country_id:
        return "club"

    return "national_team"
