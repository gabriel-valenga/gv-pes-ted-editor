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

## Project Status

**Early development — core functionality under testing.**

The current Python script has been tested with individual player attribute and skill modifications. Broader compatibility, complete field coverage, and additional validation are still in progress.

Not every field exposed by TEditor has been mapped yet. Team data, tactics, player appearance data, and other structures require further investigation and testing.

## Roadmap

- [x] Implement the initial TED decryption logic.
- [x] Parse mapped player fields.
- [x] Modify individual player attributes and skills.
- [x] Save modified TED files with the correct PES 2021 encryption mask.
- [x] Implement batch editing through configurable rules.
- [x] Validate modified TED files in PES 2021 across multiple teams.
- [ ] Expand field coverage to match TEditor's data model.
- [ ] Reproduce and validate TEditor's overall rating calculations.
- [ ] Add automated tests for reading, writing, encryption, and data integrity.
- [ ] Introduce a local SQLite database for player data and edit history.
- [ ] Support CSV import and export for external analysis and editing.
- [ ] Build a standalone desktop application.

## Getting Started

### Requirements

- Python 3
- A PES 2021 `.ted` file for testing

The current prototype uses Python's standard library for its core operations.

### Usage

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

- **[PES 2021 Utilities](https://github.com/srafols/pes2021-utilities)** by [srafols](https://github.com/srafols) — This project provided a Python reference for working with PES 2021 TED files, particularly the decryption and data extraction logic. Parts of this project are based on or adapted from code originally published in [PES 2021 Utilities](https://github.com/srafols/pes2021-utilities) by srafols, licensed under the MIT License. See the relevant upstream repository for the original copyright and license notices.

- **[PES GV Bulk Editor (JavaScript)](https://github.com/gabriel-valenga/teditor-pes-gv-bulk-tools)** — An earlier project of mine that extended TEditor.app through browser console scripts to support batch editing of player attributes. It inspired the development of this independent Python-based TED reader and editor.

## Disclaimer

This is an independent, community-oriented project. It is not affiliated with or endorsed by Konami or the developers of TEditor.

Use it at your own risk and keep backups of your files.

## License

MIT

This project is an independent effort and is not affiliated with or endorsed by Konami or the developers of TEditor.app.
