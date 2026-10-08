"""Focused tests for the packaged command-line interface."""

import json
from pathlib import Path

import pytest
from research_foundry import cli, server


def test_templates_lists_the_catalog(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The templates command exposes the public catalog."""
    assert cli.main(["templates"]) == 0
    output = capsys.readouterr().out
    assert "methodology\tMethodology\tThe code repository" in output
    assert "software\tSoftware\tAn application" in output


def test_questions_json_describes_defaults_and_choices(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Machine-readable questions omit Cookiecutter's private keys."""
    assert cli.main(["questions", "paper", "--json"]) == 0
    questions = json.loads(capsys.readouterr().out)
    by_name = {question["name"]: question for question in questions}
    assert by_name["venue"] == {
        "name": "venue",
        "prompt": "Venue style (article is a plain preprint layout)",
        "default": "iclr",
        "choices": ["iclr", "neurips", "icml", "article"],
    }
    assert by_name["project_slug"]["default"] == "my-project"
    assert all(not name.startswith("_") for name in by_name)


def test_new_refuses_a_malformed_answer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The new command explains the required answer syntax."""
    assert cli.main(["new", "workspace", "--answer", "broken"]) == 2
    assert "KEY=VALUE" in capsys.readouterr().err


def test_check_returns_one_when_a_project_is_behind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The check command maps cruft's behind result to exit status one."""
    monkeypatch.setattr(cli, "check_project", lambda _path: False)
    assert cli.main(["check", "/project"]) == 1


def test_update_passes_the_confirmation_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The update command forwards explicit unattended approval."""
    called: list[tuple[Path, bool]] = []

    def update(path: Path, *, yes: bool = False) -> bool:
        called.append((path, yes))
        return True

    monkeypatch.setattr(cli, "update_project", update)
    assert cli.main(["update", "/project", "--yes"]) == 0
    assert called == [(Path("/project"), True)]


def test_install_skills_forwards_the_selected_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The install-skills command preserves the drift-handling mode."""
    called: list[list[str]] = []

    def install(arguments: list[str]) -> int:
        called.append(arguments)
        return 0

    monkeypatch.setattr(cli, "install_skills_main", install)
    assert cli.main(["install-skills", "--adopt"]) == 0
    assert called == [["--adopt"]]


def test_mcp_command_runs_the_stdio_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mcp command dispatches to the server runner."""
    called: list[bool] = []
    monkeypatch.setattr(server, "run", lambda: called.append(True))
    assert cli.main(["mcp"]) == 0
    assert called == [True]
