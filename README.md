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
- Support calculated player attributes, including BMI and Overall.
- Validate rule configurations before applying changes.
- Validate rule application across all supported editable numeric attributes and boolean special skills.
- Process multiple TED files using the command-line interface.
- Combine multiple rule configurations and manual edits in a single processing operation.

## Project Status

**Core functionality implemented — automated test suite passing.**

The project currently supports TED decryption, player data extraction, individual editing, and batch editing through a configurable rules engine.

The rules engine has automated tests covering calculations, conditions, operations, configuration validation, and rule application. The test suite validates the application of rules to all supported editable numeric attributes and boolean special skills.

The Overall rating calculation has also been reproduced and validated against TEditor's behavior.

The current field coverage is focused on the player data required by the project. Additional TED structures and fields may be investigated as future requirements arise.

## Roadmap

- [x] Implement the initial TED decryption logic.
- [x] Parse mapped player fields.
- [x] Modify individual player attributes and skills.
- [x] Save modified TED files with the correct PES 2021 encryption mask.
- [x] Implement batch editing through configurable rules.
- [x] Validate modified TED files in PES 2021 across multiple teams.
- [x] Implement automated tests for the rules engine.
- [x] Reproduce and validate TEditor's Overall rating calculations.
- [x] Expand automated tests for reading, writing, encryption, and data integrity.
- [x] Introduce a local SQLite database for player data and edit history.
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

It supports player selection, conditional evaluation, numeric operations, boolean skill changes, reputation updates, and attribute-based ranges.

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

Conditions can reference original player fields and supported calculated fields, such as `calculated.bmi` and `calculated.overall`.

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

The `reputation` field also supports the `set` operation, with integer values from `1` to `8`.

### Attribute-Based Ranges (Bands)

Bands allow operations to be applied according to a player's attribute value.

Each band defines:

- `field`: the attribute or calculated field used for evaluation.
- `ranges`: a list of minimum and maximum values.
- `operations`: the operations executed when a range matches.

Range boundaries are inclusive.

**Overlapping ranges are allowed.** When multiple ranges match, all matching ranges are executed sequentially.

### Calculated Fields

The rules engine currently supports the following calculated fields:

- `calculated.bmi`: Body Mass Index, calculated from the player's weight and height.
- `calculated.overall`: Player Overall rating, calculated using the position-specific and general score calculations reproduced from TEditor's implementation.

Calculated fields can be used in conditions and bands.

Both fields are virtual and are not written to the TED file.

### Field Restrictions

The rules engine modifies supported numeric player attributes, boolean special skills, and the `reputation` field.

Player registration data, including `weight` and `height`, cannot be modified through rules.

Calculated fields are read-only.

## Batch Editing with the CLI

The CLI supports applying one or more JSON rule configurations to a TED file or multiple TED files.

### 1. Create a Rules Configuration

Create a JSON file, for example `rules/player_rules.json`:

```json
{
  "format": "pes-gv-ted-rules-config",
  "version": 1,
  "language": "en",
  "targets": {
    "allPositions": true,
    "positions": []
  },
  "rules": [
    {
      "name": "Increase speed",
      "enabled": true,
      "conditionLogic": "AND",
      "conditions": [],
      "operations": [
        {
          "field": "speed",
          "operation": "delta",
          "value": 5
        }
      ],
      "bands": []
    },
    {
      "name": "Boost finishing for fast attackers",
      "enabled": true,
      "conditionLogic": "AND",
      "conditions": [
        {
          "field": "speed",
          "operator": "gte",
          "value": 80
        }
      ],
      "operations": [
        {
          "field": "finishing",
          "operation": "delta",
          "value": 10
        }
      ],
      "bands": []
    }
  ]
}
```

This configuration contains two rules:

- `Increase speed`: adds 5 points to the speed attribute of all selected players.
- `Boost finishing for fast attackers`: adds 10 points to finishing for players whose speed is at least 80.

Rules are evaluated in the order in which they appear in the configuration.

### 2. Process a Single TED File

Use `--config` to apply a rules configuration and `--out` to specify the output file:

```bash
python cli.py "team.ted" --config "rules/player_rules.json" --out "output/team_edited.ted"
```

### 3. Apply Multiple Configurations

Multiple configuration files can be supplied using repeated `--config` arguments:

```bash
python cli.py "team.ted" \
  --config "rules/physical_attributes.json" \
  --config "rules/technical_attributes.json" \
  --out "output/team_edited.ted"
```

Configurations are applied sequentially in the order provided.

All rules from the first configuration are applied before the second configuration is processed.

### 4. Process Multiple TED Files

To process every `.ted` file directly inside a directory, use `--input-dir` and `--output-dir`:

```bash
python cli.py \
  --input-dir "input/teams" \
  --config "rules/player_rules.json" \
  --output-dir "output/teams"
```

The original filenames are preserved in the output directory.

**Directory processing is non-recursive:** subdirectories are not searched.

Individual processing failures do not stop the remaining files from being processed. The CLI reports successful and failed files at the end and exits with a non-zero status if any file fails.

### 5. Export Processing Results to JSON

For a single TED file, use `--json` to export the processing results:

```bash
python cli.py \
  "team.ted" \
  --config "rules/player_rules.json" \
  --out "output/team_edited.ted" \
  --json "output/results.json"
```

The JSON report includes player data, applied edits, team information, and processing details.

The `--json` option is available only when processing a single TED file. When it is omitted, the processing report is printed to the terminal as JSON.

The output directory for the JSON file must already exist.

### 6. Combine Rules with Manual Edits

Manual field edits can also be supplied using `--set`:

```bash
python cli.py \
  "team.ted" \
  --config "rules/player_rules.json" \
  --set "0:speed=95" \
  --set "1:finishing=90" \
  --out "output/team_edited.ted"
```

Manual edits are applied **after all configuration rules**.

Multiple `--set` arguments are supported.

### 7. Save the Decrypted Buffer

For debugging, use `--decrypted` to save the decrypted TED buffer:

```bash
python cli.py \
  "team.ted" \
  --decrypted "debug/team_decrypted.bin"
```

The decrypted buffer is saved before rules and manual edits are applied.

This option is available only when processing a single TED file. The parent directory must already exist or be creatable by the application.

### CLI Options

| Argument | Description |
|---|---|
| `TED` | One or more encrypted TED file paths. |
| `--config JSON` | Rules configuration file. Can be repeated; configurations are applied sequentially. |
| `--input-dir DIR` | Process all `.ted` files directly inside a directory (non-recursively). |
| `--output-dir DIR` | Output directory for processed TED files. Original filenames are preserved. |
| `--out FILE` | Output path for a single TED file. |
| `--json FILE` | Export the processing result as JSON. Single-file processing only. |
| `--set INDEX:FIELD=VALUE` | Apply a manual player field edit. Can be repeated. Manual edits are applied after all configuration rules. |
| `--decrypted FILE` | Save the decrypted buffer before edits are applied. Single-file processing only. Intended for debugging. |
| `--list-fields` | Print all recognized player fields as JSON. Can be combined with processing arguments. |
| `--help` | Display command-line usage and available options. |

Use `--output-dir` or `--out`, not both.

For additional options, run:

```bash
python cli.py --help
```

## Design Goals

The project is being developed incrementally, with an emphasis on:

- Preserving binary data that is not explicitly modified.
- Keeping field definitions and value conversions consistent with the currently supported data model.
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