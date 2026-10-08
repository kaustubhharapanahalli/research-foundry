"""End-to-end checks of workspace layouts in temporary Git repositories."""

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from research_foundry import cli
from research_foundry.layout import check_layout
from tests.conftest import GIT_ENV

Render = Callable[..., Path]


def _git(project: Path, *arguments: str) -> None:
    """Run an isolated Git command in a temporary workspace."""
    subprocess.run(
        ["git", *arguments],
        cwd=project,
        env={**os.environ, **GIT_ENV},
        check=True,
        capture_output=True,
        text=True,
    )


def _project(render: Render, tmp_path: Path, *, cruft: bool) -> Path:
    """Render a workspace and initialize its index."""
    project = render("workspace", tmp_path)
    if cruft:
        (project / ".cruft.json").write_text(
            json.dumps(
                {
                    "directory": "workspace",
                    "context": {"cookiecutter": {"repo_name": project.name}},
                }
            ),
            encoding="utf-8",
        )
    _git(project, "init", "-q")
    return project


def _local_rules(project: Path, bullets: str) -> None:
    """Replace the empty section with declared local paths."""
    agents = project / "AGENTS.md"
    text = agents.read_text(encoding="utf-8").replace("_None yet._", bullets)
    agents.write_text(text, encoding="utf-8")


def _index(project: Path) -> None:
    """Refresh the index after a test changes files."""
    _git(project, "add", "-A")


@pytest.mark.functional
@pytest.mark.parametrize(
    "cruft", [True, False], ids=["with-context", "defaults"]
)
def test_declared_workspace_deviations_match(
    render: Render, tmp_path: Path, cruft: bool
) -> None:
    """Named additions and ignored process files produce no findings."""
    project = _project(render, tmp_path, cruft=cruft)
    if cruft:
        _local_rules(
            project,
            "- **`experiments/specs/`** (template: "
            "`experiments/configs/*.yaml` only).\n"
            "- `lit-reviews/_notes.md` are local.\n",
        )
        (project / "experiments" / "specs").mkdir()
        (project / "experiments" / "specs" / "first.md").write_text(
            "spec\n", encoding="utf-8"
        )
        (project / "lit-reviews" / "_notes.md").write_text(
            "notes\n", encoding="utf-8"
        )
        (project / ".agent-state").mkdir()
        (project / ".agent-state" / "x.md").write_text(
            "state\n", encoding="utf-8"
        )
        (project / "journal.md").write_text("local\n", encoding="utf-8")
    else:
        _local_rules(
            project,
            "- **Extra folders** (adds to the template's layout): "
            "`experiments/ledger/`, `experiments/progress/`, `archive/` "
            "and `docs/runbooks/`.\n",
        )
        for relative in (
            "experiments/ledger",
            "experiments/progress",
            "archive",
            "docs/runbooks",
        ):
            folder = project / relative
            folder.mkdir(parents=True)
            (folder / "README.md").write_text("local\n", encoding="utf-8")
    _index(project)

    result = check_layout(project)

    assert not result.findings
    assert result.report == "layout matches the template contract"


@pytest.mark.functional
@pytest.mark.parametrize(
    ("relative", "kind"),
    [
        ("datasets/registry.yaml", "file"),
        ("methodology/theory/<block>.md", "dir"),
        ("lit-reviews/<paper>/", "dir"),
        ("baselines/<paper>/", "dir"),
        ("experiments/configs/*.yaml", "dir"),
        ("results/<batch>/ACCEPTED.md", "dir"),
        ("advisor-logs/advisor-sync-<date>.md", "dir"),
        (".agent-state/<name>.md", "runtime"),
        ("AGENTS.md", "file"),
        ("docs/", "dir"),
    ],
)
def test_missing_contract_paths_are_reported(
    render: Render, tmp_path: Path, relative: str, kind: str
) -> None:
    """Each required contract file or directory is guarded."""
    project = _project(render, tmp_path, cruft=False)
    components = relative.strip("/").split("/")
    for index, component in enumerate(components):
        if "<" in component or "*" in component:
            components = components[:index]
            break
    path = project / "/".join(components)
    if kind == "runtime":
        result = check_layout(project)
        assert not any(
            item.kind == "missing" and item.path == ".agent-state"
            for item in result.findings
        )
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    _index(project)

    result = check_layout(project)

    assert any(
        item.kind == "missing"
        and item.path == path.relative_to(project).as_posix()
        for item in result.findings
    )


@pytest.mark.functional
def test_unnamed_top_level_addition_is_extra_and_named_path_is_not(
    render: Render, tmp_path: Path
) -> None:
    """Local rules can declare an added top-level folder."""
    project = _project(render, tmp_path, cruft=False)
    extra = project / "archive"
    extra.mkdir()
    (extra / "notes.md").write_text("notes\n", encoding="utf-8")
    _index(project)

    assert any(
        item.kind == "extra" and item.path == "archive"
        for item in check_layout(project).findings
    )
    _local_rules(project, "- `archive/` is a local research record.\n")
    _index(project)
    assert not any(
        item.kind == "extra" and item.path == "archive"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_missing_local_rules_section_is_reported(
    render: Render, tmp_path: Path
) -> None:
    """An instructions file without the section receives its own finding."""
    project = _project(render, tmp_path, cruft=False)
    agents = project / "AGENTS.md"
    agents.write_text("# Workspace\n", encoding="utf-8")
    _index(project)

    assert any(
        item.kind == "missing-local-rules" and item.path == "AGENTS.md"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_ignored_top_level_file_is_not_extra(
    render: Render, tmp_path: Path
) -> None:
    """Git-ignored process files do not count as present paths."""
    project = _project(render, tmp_path, cruft=False)
    (project / "journal.md").write_text("local\n", encoding="utf-8")

    assert not any(
        item.path == "journal.md" for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_layout_report_is_deterministic(
    render: Render, tmp_path: Path
) -> None:
    """Repeated checks of one workspace have identical findings and report."""
    project = _project(render, tmp_path, cruft=False)
    first = check_layout(project)
    second = check_layout(project)

    assert first == second


@pytest.mark.functional
def test_layout_check_does_not_modify_the_workspace(
    render: Render, tmp_path: Path
) -> None:
    """Checking paths leaves workspace file contents unchanged."""
    project = _project(render, tmp_path, cruft=False)
    before = {
        item.relative_to(project).as_posix(): item.read_bytes()
        for item in project.rglob("*")
        if item.is_file() and ".git" not in item.parts
    }

    check_layout(project)

    after = {
        item.relative_to(project).as_posix(): item.read_bytes()
        for item in project.rglob("*")
        if item.is_file() and ".git" not in item.parts
    }
    assert after == before


@pytest.mark.functional
def test_layout_command_refuses_a_non_git_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command refuses paths outside a Git repository with status two."""
    assert cli.main(["layout", str(tmp_path)]) == 2
    assert "not a Git repository" in capsys.readouterr().err


@pytest.mark.functional
def test_layout_command_refuses_a_non_workspace_repository(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A repository without workspace markers receives a corrective error."""
    _git(tmp_path, "init", "-q")
    assert cli.main(["layout", str(tmp_path)]) == 2
    assert "does not look like a workspace" in capsys.readouterr().err


@pytest.mark.functional
def test_missing_agents_file_reports_missing_local_rules(
    render: Render, tmp_path: Path
) -> None:
    """An absent instructions file is reported even without its section."""
    project = _project(render, tmp_path, cruft=False)
    (project / "AGENTS.md").unlink()
    _index(project)

    assert any(
        item.kind == "missing-local-rules" and item.path == "AGENTS.md"
        for item in check_layout(project).findings
    )
