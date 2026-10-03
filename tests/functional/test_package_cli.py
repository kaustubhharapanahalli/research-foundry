"""End-to-end tests for the installed-style command interface."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from research_foundry import __version__, cli
from research_foundry.constants import REPOSITORY_ENV, TEMPLATE_NAMES
from tests.conftest import GIT_ENV, ROOT
from tools.throwaway import snapshot


@pytest.fixture(autouse=True)
def _offline_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep release-tag resolution on a local, missing repository."""
    monkeypatch.setenv(REPOSITORY_ENV, str(tmp_path / "offline-repository"))


@pytest.mark.parametrize("template", TEMPLATE_NAMES)
def test_new_generates_every_template_with_defaults(
    template: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every template renders through the real command with no input."""
    output = tmp_path / template
    assert cli.main(["new", template, "-o", str(output)]) == 0
    project = Path(capsys.readouterr().out.strip())
    assert project.parent == output
    state = json.loads((project / ".cruft.json").read_text())
    assert state["directory"] == template
    assert state["commit"] == f"v{__version__}"


def test_new_is_byte_deterministic(tmp_path: Path) -> None:
    """The same explicit answers generate byte-identical trees."""
    answers = ["--answer", "project_name=Repeatable"]
    assert (
        cli.main(["new", "workspace", "-o", str(tmp_path / "a"), *answers])
        == 0
    )
    assert (
        cli.main(["new", "workspace", "-o", str(tmp_path / "b"), *answers])
        == 0
    )
    left = tmp_path / "a" / "repeatable-workspace"
    right = tmp_path / "b" / "repeatable-workspace"
    left_tree = {
        str(path.relative_to(left)): path.read_bytes()
        for path in left.rglob("*")
        if path.is_file()
    }
    right_tree = {
        str(path.relative_to(right)): path.read_bytes()
        for path in right.rglob("*")
        if path.is_file()
    }
    assert left_tree == right_tree


@pytest.mark.parametrize(
    ("arguments", "reason"),
    [
        (["new", "unknown"], "Unknown template"),
        (
            ["new", "workspace", "--answer", "typo=yes"],
            "does not ask for typo",
        ),
        (
            [
                "new",
                "software",
                "--answer",
                "backend_django=no",
                "--answer",
                "frontend_nextjs=yes",
            ],
            "needs backend_django",
        ),
    ],
)
def test_new_refusals_name_the_problem(
    arguments: list[str], reason: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every generation refusal is corrective and uses exit status two."""
    assert cli.main(arguments) == 2
    assert reason in capsys.readouterr().err


def _git(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run Git with the isolated test identity."""
    return subprocess.run(
        ["git", *argv],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        check=True,
        capture_output=True,
        text=True,
    )


def test_new_check_update_round_trip_through_a_local_bare_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Generated cruft metadata supports an entirely local release update."""
    source = snapshot(ROOT, tmp_path / "source", GIT_ENV)
    _git(["tag", f"v{__version__}"], source)
    bare = tmp_path / "foundry.git"
    _git(["init", "--bare", str(bare)], tmp_path)
    _git(["remote", "add", "release", str(bare)], source)
    _git(["push", "release", "main", "--tags"], source)
    monkeypatch.setenv(REPOSITORY_ENV, str(bare))

    output = tmp_path / "projects"
    assert cli.main(["new", "workspace", "-o", str(output)]) == 0
    project = Path(capsys.readouterr().out.strip())
    _git(["init", "-q", "-b", "main"], project)
    _git(["add", "-A"], project)
    _git(["commit", "-qm", "generated"], project)
    assert cli.main(["check", str(project)]) == 0

    shared = source / "_shared" / "base" / "editorconfig"
    shared.write_text(
        shared.read_text() + "\n[*.round-trip]\nindent_size = 3\n"
    )
    _git(["add", str(shared)], source)
    _git(["commit", "-qm", "change shared base"], source)
    _git(["push", "release", "main"], source)
    assert cli.main(["check", str(project)]) == 1
    assert cli.main(["update", str(project), "--yes"]) == 0
    assert "[*.round-trip]" in (project / ".editorconfig").read_text()
