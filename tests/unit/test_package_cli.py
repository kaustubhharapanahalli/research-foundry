"""Focused tests for the packaged command-line interface."""

import json
from pathlib import Path

import pytest
from research_foundry import cli, server
from research_foundry.layout import LayoutFinding, LayoutResult
from research_foundry.templates import FoundryError


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
        "choices": ["iclr", "neurips", "article"],
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


def test_layout_command_prints_a_success_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The layout command prints the shared checker report."""
    monkeypatch.setattr(cli, "check_layout", lambda _path: LayoutResult(()))

    assert cli.main(["layout"]) == 0
    assert capsys.readouterr().out.strip() == (
        "layout matches the template contract"
    )


def test_layout_command_returns_one_for_findings(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The layout command uses exit status one when paths differ."""
    result = LayoutResult((LayoutFinding("extra", "archive"),))
    monkeypatch.setattr(cli, "check_layout", lambda _path: result)

    assert cli.main(["layout", "/workspace"]) == 1
    assert capsys.readouterr().out.strip() == "extra: archive"


def test_layout_command_returns_two_for_a_refusal(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A refused workspace prints its corrective error to standard error."""

    def refuse(_path: Path) -> LayoutResult:
        raise FoundryError("initialize Git in the workspace root and retry")

    monkeypatch.setattr(cli, "check_layout", refuse)

    assert cli.main(["layout", "/workspace"]) == 2
    assert "initialize Git" in capsys.readouterr().err


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
