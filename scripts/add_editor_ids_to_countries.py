
import json
from pathlib import Path


EDITOR_IDS = {
    "OTH": 260,
    "AFG": 1,
    "ALB": 191,
    "ALG": 44,
    "ASA": 161,
    "AND": 192,
    "ANG": 45,
    "AIA": 103,
    "ATG": 104,
    "ARG": 144,
    "ARM": 193,
    "ARU": 105,
    "AUS": 162,
    "AUT": 194,
    "AZE": 195,
    "BAH": 106,
    "BHR": 2,
    "BAN": 3,
    "BRB": 107,
    "BLR": 196,
    "BEL": 197,
    "BLZ": 108,
    "BEN": 46,
    "BER": 109,
    "BHU": 4,
    "BOL": 145,
    "BIH": 198,
    "BOT": 47,
    "BRA": 146,
    "VGB": 136,
    "BRU": 5,
    "BUL": 199,
    "BFA": 48,
    "BDI": 49,
    "CAM": 6,
    "CMR": 50,
    "CAN": 110,
    "CPV": 51,
    "CAY": 111,
    "CTA": 52,
    "CHA": 53,
    "CHI": 147,
    "CHN": 7,
    "TPE": 298,
    "COL": 148,
    "COM": 54,
    "CGO": 98,
    "COD": 55,
    "COK": 163,
    "CRC": 112,
    "CIV": 56,
    "CRO": 200,
    "CUB": 113,
    "CUW": 140,
    "CYP": 201,
    "CZE": 202,
    "DEN": 203,
    "DJI": 57,
    "DMA": 114,
    "DOM": 115,
    "ECU": 149,
    "EGY": 58,
    "SLV": 116,
    "ENG": 204,
    "EQG": 59,
    "ERI": 60,
    "EST": 205,
    "SWZ": 89,
    "ETH": 61,
    "FRO": 206,
    "FIJ": 164,
    "FIN": 207,
    "FRA": 208,
    "GUF": 138,
    "GAB": 62,
    "GAM": 63,
    "GEO": 209,
    "GER": 210,
    "GHA": 64,
    "GIB": 245,
    "GRE": 211,
    "GRN": 117,
    "GUM": 176,
    "GUA": 119,
    "GUI": 65,
    "GNB": 66,
    "GUY": 159,
    "HAI": 120,
    "HON": 121,
    "HKG": 8,
    "HUN": 212,
    "ISL": 213,
    "IND": 9,
    "IDN": 10,
    "IRN": 11,
    "IRQ": 12,
    "ISR": 189,
    "ITA": 215,
    "JAM": 122,
    "JPN": 13,
    "JOR": 14,
    "KAZ": 216,
    "KEN": 67,
    "PRK": 15,
    "KOR": 16,
    "KVX": 311,
    "KUW": 17,
    "KGZ": 40,
    "LAO": 18,
    "LVA": 217,
    "LBN": 19,
    "LES": 68,
    "LBR": 69,
    "LBY": 70,
    "LIE": 218,
    "LTU": 219,
    "LUX": 220,
    "MAC": 20,
    "MAD": 71,
    "MWI": 72,
    "MAS": 21,
    "MDV": 22,
    "MLI": 73,
    "MLT": 222,
    "MTN": 74,
    "MRI": 75,
    "MEX": 124,
    "MDA": 223,
    "MON": 250,
    "MNG": 23,
    "MNE": 304,
    "MSR": 125,
    "MAR": 76,
    "MOZ": 77,
    "MYA": 24,
    "NAM": 78,
    "NEP": 25,
    "NED": 224,
    "NCL": 165,
    "NZL": 166,
    "NCA": 127,
    "NIG": 79,
    "NGA": 80,
    "MKD": 221,
    "NIR": 225,
    "NOR": 226,
    "OMA": 26,
    "PAK": 27,
    "PLW": 184,
    "PLE": 28,
    "PAN": 128,
    "PNG": 167,
    "PAR": 150,
    "PER": 151,
    "PHI": 29,
    "POL": 227,
    "POR": 228,
    "PUR": 129,
    "QAT": 30,
    "IRL": 214,
    "ROU": 229,
    "RUS": 230,
    "RWA": 81,
    "SKN": 130,
    "LCA": 131,
    "VIN": 132,
    "SAM": 168,
    "SMR": 231,
    "STP": 82,
    "KSA": 31,
    "SCO": 232,
    "SEN": 83,
    "SRB": 303,
    "SEY": 84,
    "SLE": 85,
    "SIN": 32,
    "SVK": 234,
    "SVN": 235,
    "SOL": 169,
    "SOM": 86,
    "RSA": 87,
    "SSD": 312,
    "ESP": 236,
    "SRI": 33,
    "SDN": 88,
    "SUR": 139,
    "SWE": 237,
    "SUI": 238,
    "SYR": 34,
    "TAH": 170,
    "TJK": 41,
    "TAN": 90,
    "THA": 36,
    "TLS": 43,
    "TOG": 91,
    "TGA": 171,
    "TRI": 133,
    "TUN": 92,
    "TUR": 190,
    "TKM": 42,
    "TCA": 134,
    "UGA": 93,
    "UKR": 239,
    "UAE": 37,
    "URU": 152,
    "VIR": 137,
    "USA": 135,
    "UZB": 240,
    "VAN": 172,
    "VEN": 153,
    "VIE": 38,
    "WAL": 241,
    "YEM": 39,
    "ZAM": 94,
    "ZIM": 95,
}


MANUAL_EDITOR_CODES = {
    "United Arab Emirates": "UAE",
    "Angola": "ANG",
    "Aruba": "ARU",
    "Bangladesh": "BAN",
    "Bahamas": "BAH",
    "Bhutan": "BHU",
    "Botswana": "BOT",
    "Costa Rica": "CRC",
    "Fiji": "FIJ",
    "Grenada": "GRN",
    "Guinea": "GUI",
    "Guatemala": "GUA",
    "Lesotho": "LES",
    "Madagascar": "MAD",
    "Nicaragua": "NCA",
    "Nepal": "NEP",
    "Paraguay": "PAR",
    "Saudi Arabia": "KSA",
    "Solomon Islands": "SOL",
    "Seychelles": "SEY",
    "Singapore": "SIN",
    "Togo": "TOG",
    "Tonga": "TGA",
    "Trinidad & Tobago": "TRI",
    "Uruguay": "URU",
    "Vanuatu": "VAN",
    "Samoa": "SAM",
    "South Africa": "RSA",
    "Zimbabwe": "ZIM",
}


def add_editor_ids(input_path: Path, output_path: Path) -> None:
    """Add TEditor IDs and log countries without a matching ID."""
    with input_path.open("r", encoding="utf-8") as file:
        catalog = json.load(file)

    missing_countries = []
    manually_mapped = []

    for country in catalog["countries"]:
        names = country.get("names", {})
        editor_code = country.get("editor_code")

        # Apply a manual mapping only when editor_code is missing.
        if not editor_code:
            matched_code = next(
                (
                    MANUAL_EDITOR_CODES[name]
                    for name in names.values()
                    if name in MANUAL_EDITOR_CODES
                ),
                None,
            )

            if matched_code:
                editor_code = matched_code
                country["editor_code"] = editor_code

                manually_mapped.append({
                    "name": names.get("en", next(iter(names.values()), "Unknown")),
                    "editor_code": editor_code,
                    "editor_id": EDITOR_IDS[editor_code],
                })

        editor_id = EDITOR_IDS.get(editor_code) if editor_code else None
        country["editor_id"] = editor_id

        if editor_id is None:
            missing_countries.append({
                "code": country.get("code"),
                "code_alpha3": country.get("code_alpha3"),
                "editor_code": editor_code,
                "names": names,
                "reason": (
                    "missing_editor_code"
                    if not editor_code
                    else "editor_code_not_found"
                ),
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            catalog,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    missing_path = output_path.with_name(
        "countries_missing_editor_ids.json"
    )

    with missing_path.open("w", encoding="utf-8") as file:
        json.dump(
            missing_countries,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    mapped = len(catalog["countries"]) - len(missing_countries)

    print(f"Countries processed: {len(catalog['countries'])}")
    print(f"Editor IDs mapped: {mapped}")
    print(f"Editor IDs missing: {len(missing_countries)}")
    print(f"Manual mappings applied: {len(manually_mapped)}")
    print(f"Output saved: {output_path}")
    print(f"Missing countries log saved: {missing_path}")

    print("\nManual mappings applied:")
    print("-" * 40)

    for country in manually_mapped:
        print(
            f'"{country["name"]}": '
            f'("{country["editor_code"]}", {country["editor_id"]}),'
        )

    print("\nCountries without editor_id:")
    print("-" * 40)

    for country in missing_countries:
        names = country["names"]
        name = names.get("en") or next(iter(names.values()), "Unknown")

        print(
            f'"{country["editor_code"] or "NULL"}": "{name}",'
        )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    input_path = project_root / "src" / "data" / "countries.json"
    output_path = project_root / "src" / "data" / "countries_updated.json"

    add_editor_ids(input_path, output_path)
