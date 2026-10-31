from pathlib import Path

from cli import find_option_file_teds


def test_finds_ted_files_in_root_directory(tmp_path: Path) -> None:
    ted_file = tmp_path / "team.ted"
    ted_file.touch()

    result = find_option_file_teds(tmp_path)

    assert result == [ted_file]


def test_finds_ted_files_in_nested_directories(tmp_path: Path) -> None:
    ted_files = [
        tmp_path / "_TED" / "team1.ted",
        tmp_path / "__TED" / "team2.ted",
        tmp_path / "Premier League" / "team3.ted",
        tmp_path / "DREAM TEAM" / "team4.ted",
        tmp_path / "Backups" / "team5.ted",
    ]

    for ted_file in ted_files:
        ted_file.parent.mkdir(parents=True, exist_ok=True)
        ted_file.touch()

    result = find_option_file_teds(tmp_path)

    assert result == sorted(ted_files)


def test_finds_ted_files_with_uppercase_extension(tmp_path: Path) -> None:
    ted_files = [
        tmp_path / "team1.ted",
        tmp_path / "team2.TED",
        tmp_path / "team3.TeD",
    ]

    for ted_file in ted_files:
        ted_file.touch()

    result = find_option_file_teds(tmp_path)

    assert result == sorted(ted_files)


def test_ignores_files_with_other_extensions(tmp_path: Path) -> None:
    files = [
        tmp_path / "team.png",
        tmp_path / "team.txt",
        tmp_path / "team.ced",
    ]

    for file in files:
        file.touch()

    result = find_option_file_teds(tmp_path)

    assert result == []


def test_returns_empty_list_when_no_ted_files_exist(tmp_path: Path) -> None:
    (tmp_path / "empty_folder").mkdir()

    result = find_option_file_teds(tmp_path)

    assert result == []


def test_returns_sorted_results_without_duplicates(tmp_path: Path) -> None:
    ted_files = [
        tmp_path / "Z" / "team_z.ted",
        tmp_path / "A" / "team_a.ted",
        tmp_path / "team_root.ted",
    ]

    for ted_file in ted_files:
        ted_file.parent.mkdir(parents=True, exist_ok=True)
        ted_file.touch()

    result = find_option_file_teds(tmp_path)

    assert result == sorted(ted_files)
    assert len(result) == len(set(result))
    