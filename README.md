# GV PES TED Editor

A Python-based tool for reading, decrypting, inspecting, and editing **PES 2021 `.ted` files**.

The project aims to provide an independent way to inspect and modify TED data, starting with player attributes and skills and gradually expanding toward batch editing, data management, and a standalone desktop application.

## Current Features

- Decrypt PES 2021 TED files using the current reverse-engineered decryption logic.
- Parse player records and recognized fields.
- Read player attributes, skills, position data, and other mapped values.
- Apply individual changes to player fields.
- Write modified data back to a TED file.
- Export parsed data to JSON for inspection and debugging.
- Handle field-level value conversions identified in the TEditor JavaScript implementation.
- Apply batch player edits through configurable rules.
- Filter players by registered position.
- Apply conditional operations and attribute-based ranges.
- Support calculated player attributes, currently including BMI.
- Validate rule configurations before applying changes.

## Project Status

**Core functionality implemented — automated testing in progress.**

The project currently supports TED decryption, player data extraction, individual editing, and batch editing through a configurable rules engine.

The rules engine currently has **115 automated tests** covering calculations, conditions, operations, configuration validation, and rule application.

Not every field exposed by TEditor has been mapped yet. Team data, tactics, player appearance data, and other structures require further investigation and testing.

## Roadmap

- [x] Implement the initial TED decryption logic.
- [x] Parse mapped player fields.
- [x] Modify individual player attributes and skills.
- [x] Save modified TED files with the correct PES 2021 encryption mask.
- [x] Implement batch editing through configurable rules.
- [x] Validate modified TED files in PES 2021 across multiple teams.
- [x] Implement automated tests for the rules engine.
- [ ] Expand field coverage to match TEditor's data model.
- [ ] Reproduce and validate TEditor's overall rating calculations.
- [ ] Expand automated tests for reading, writing, encryption, and data integrity.
- [ ] Introduce a local SQLite database for player data and edit history.
- [ ] Support CSV import and export for external analysis and editing.
- [ ] Build a standalone desktop application.

## Getting Started

### Prerequisites

- Python 3.13 or higher.
- A PES 2021 `.ted` file for testing.

### 1. Clone the repository

```bash
git clone https://github.com/gabriel-valenga/gv-pes-ted-editor.git
cd gv-pes-ted-editor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
.venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The editable installation makes the project's packages available without manually configuring `PYTHONPATH`.

### 5. Run the tests

```bash
python -m pytest -v
```

## Usage

Run the script with a TED file to inspect its contents and export parsed data:

```bash
python cli.py "your_file.ted" --json output.json
```

To modify a player's field, use the supported field-editing syntax:

```bash
python cli.py "your_file.ted" --set "0:speed=90" --out "edited_file.ted"
```

The example changes the `speed` field for the player at physical record index `0`. Player indices start at `0`.

For the complete list of supported fields and command-line options, run:

```bash
python cli.py --help
python cli.py --list-fields
```

> **Important:** Always work on copies of your TED files. Test modified files in TEditor and PES 2021 before using them in your main Option File.

## Rules Engine

The rules engine allows multiple player edits to be applied automatically through a JSON configuration file.

It supports player selection, conditional evaluation, numeric operations, boolean skill changes, and attribute-based ranges.

### Configuration Format

The current configuration format uses:

| Property | Value |
|---|---|
| `format` | `pes-gv-ted-rules-config` |
| `version` | `1` |
| `language` | `pt-BR` or `en` |

The configuration contains a `targets` object and a list of `rules`.

### Player Selection

The `targets` object determines which players are affected.

- `allPositions: true` applies rules to all players.
- `allPositions: false` applies rules only to the positions listed in `positions`.

Supported positions:

`GK`, `RB`, `CB`, `LB`, `DMF`, `CMF`, `AMF`, `RMF`, `LMF`, `RWF`, `LWF`, `SS`, `CF`.

Position selection uses the player's registered position.

### Rule Structure

Each rule contains:

- `name`: rule description.
- `enabled`: determines whether the rule is active.
- `conditionLogic`: combines conditions using `AND` or `OR`.
- `conditions`: conditions that determine whether the rule applies.
- `operations`: general operations applied when the conditions match.
- `bands`: attribute-based ranges with their own operations.

### Conditions

The rules engine supports the following comparison operators:

| Operator | Description |
|---|---|
| `eq` | Equal |
| `ne` | Not equal |
| `gt` | Greater than |
| `gte` | Greater than or equal |
| `lt` | Less than |
| `lte` | Less than or equal |
| `in` | Value belongs to a list |
| `not_in` | Value does not belong to a list |
| `between` | Value falls within an inclusive range |

Conditions can reference original player fields and supported calculated fields, such as `calculated.bmi`.

Multiple conditions are combined using `AND` or `OR`, according to `conditionLogic`.

### Operations

The rules engine supports three operation types for numeric player attributes:

| Operation | Description |
|---|---|
| `set` | Assigns a specific value |
| `delta` | Adds or subtracts a fixed amount |
| `percentage` | Applies a percentage increase or decrease |

Numeric player attributes are constrained to the range **40–99**.

For `set`, the supplied value must be an integer.

Boolean special skills support only the `set` operation, using `true` or `false`.

### Attribute-Based Ranges (Bands)

Bands allow operations to be applied according to a player's attribute value.

Each band defines:

- `field`: the attribute or calculated field used for evaluation.
- `ranges`: a list of minimum and maximum values.
- `operations`: the operations executed when a range matches.

Range boundaries are inclusive.

**Overlapping ranges are allowed.** When multiple ranges match, all matching ranges are executed sequentially.

### Calculated Fields

The rules engine currently supports the calculated field:

- `calculated.bmi`: Body Mass Index, calculated from the player's weight and height.

Calculated fields can be used in conditions and bands.

BMI is virtual and is not written to the TED file.

### Field Restrictions

The rules engine only modifies supported numeric player attributes and boolean special skills.

Player registration data, including `weight` and `height`, cannot be modified through rules.

Calculated fields are read-only.

## Design Goals

The project is being developed incrementally, with an emphasis on:

- Preserving binary data that is not explicitly modified.
- Keeping field definitions and value conversions consistent with the data model exposed by TEditor.
- Validating changes against real TED files.
- Separating binary editing, data storage, and CSV import/export into distinct components.
- Building a reliable foundation before implementing the desktop interface.

## Acknowledgments

This project was made possible by existing tools, community projects, and previous experimentation.

- **[TEditor.app](https://teditor.app/)** — Special thanks to the developers of TEditor for creating a valuable tool for editing PES player and team data. Its JavaScript implementation served as an important technical reference for understanding TED field definitions, value transformations, and player rating calculations.

- **[PES 2021 Utilities](https://github.com/srafols/pes2021-utilities)** by [srafols](https://github.com/srafols) — This project provided a Python reference for working with PES 2021 TED files, particularly the decryption and data extraction logic. Parts of this project are based on or adapted from code originally published in PES 2021 Utilities by srafols, licensed under the MIT License. See the relevant upstream repository for the original copyright and license notices.

- **[PES GV Bulk Editor (JavaScript)](https://github.com/gabriel-valenga/teditor-pes-gv-bulk-tools)** — An earlier project of mine that extended TEditor.app through browser console scripts to support batch editing of player attributes. It inspired the development of this independent Python-based TED reader and editor.

## Disclaimer

This is an independent, community-oriented project. It is not affiliated with or endorsed by Konami or the developers of TEditor.

Use it at your own risk and keep backups of your files.

## License

MIT

This project is an independent effort and is not affiliated with or endorsed by Konami or the developers of TEditor.app.