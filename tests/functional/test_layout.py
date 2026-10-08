"""End-to-end checks of workspace layouts in temporary Git repositories."""

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from research_foundry import cli
from research_foundry.layout import LayoutFinding, LayoutResult, check_layout
from research_foundry.templates import FoundryError
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
        ("docs/adr/", "dir"),
        ("presentations/<deck>/", "dir"),
        ("presentations/_base/", "dir"),
    ],
)
def test_missing_contract_paths_are_reported(
    render: Render, tmp_path: Path, relative: str, kind: str
) -> None:
    """Each required contract file or directory is guarded."""
    project = _project(render, tmp_path, cruft=relative == "AGENTS.md")
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
def test_ordinary_local_mention_does_not_excuse_missing_required_directory(
    render: Render, tmp_path: Path
) -> None:
    """An ordinary path mention does not excuse a missing contract path."""
    project = _project(render, tmp_path, cruft=False)
    shutil.rmtree(project / "baselines")
    _local_rules(project, "The old `baselines/` path is described here.\n")
    _index(project)

    assert any(
        item.kind == "missing" and item.path == "baselines"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_dropped_rule_excuses_missing_required_directory(
    render: Render, tmp_path: Path
) -> None:
    """An explicit Dropped rule excuses a normalized contract target."""
    project = _project(render, tmp_path, cruft=False)
    shutil.rmtree(project / "baselines")
    _local_rules(project, "- Dropped: `baselines/<paper>/`, because unused.\n")
    _index(project)

    assert not any(
        item.kind == "missing" and item.path == "baselines"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_moved_rule_requires_destination_and_declares_it(
    render: Render, tmp_path: Path
) -> None:
    """Moved paths are declared extras, but their destinations are required."""
    project = _project(render, tmp_path, cruft=False)
    shutil.rmtree(project / "advisor-logs")
    destination = project / "meetings"
    destination.mkdir()
    (destination / "notes.md").write_text("notes\n", encoding="utf-8")
    _local_rules(project, "- Moved: `advisor-logs/` to `meetings/`\n")
    _index(project)

    result = check_layout(project)
    assert not any(
        item.path in {"advisor-logs", "meetings"} for item in result.findings
    )

    shutil.rmtree(destination)
    _index(project)
    result = check_layout(project)
    assert result.findings == (LayoutFinding("missing", "meetings"),)


@pytest.mark.functional
def test_rule_for_non_contract_path_has_no_effect(
    render: Render, tmp_path: Path
) -> None:
    """A move for a path outside the contract does not declare its target."""
    project = _project(render, tmp_path, cruft=False)
    destination = project / "meetings"
    destination.mkdir()
    (destination / "notes.md").write_text("notes\n", encoding="utf-8")
    _local_rules(project, "- Moved: `unlisted/` to `meetings/`\n")
    _index(project)

    assert LayoutFinding("extra", "meetings") in check_layout(project).findings


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
    shutil.rmtree(project / "baselines")
    (project / "zzz-notes").mkdir()
    (project / "zzz-notes" / "notes.md").write_text(
        "notes\n", encoding="utf-8"
    )
    (project / "AGENTS.md").write_text("# Workspace\n", encoding="utf-8")
    _index(project)
    first = check_layout(project)
    second = check_layout(project)

    expected = (
        LayoutFinding("extra", "zzz-notes"),
        LayoutFinding("missing", "baselines"),
        LayoutFinding("missing-local-rules", "AGENTS.md"),
    )
    assert first == second == LayoutResult(expected)
    assert first.findings == expected
    assert (
        first.report
        == second.report
        == (
            "extra: zzz-notes\nmissing: baselines\n"
            "missing-local-rules: AGENTS.md"
        )
    )


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
@pytest.mark.parametrize("with_cruft", [False, True])
def test_layout_command_refuses_a_rendered_paper(
    render: Render,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    with_cruft: bool,
) -> None:
    """A rendered paper is not accepted as a workspace."""
    project = render("paper", tmp_path)
    if with_cruft:
        (project / ".cruft.json").write_text(
            json.dumps(
                {
                    "directory": "paper",
                    "context": {"cookiecutter": {"_template_kind": "paper"}},
                }
            ),
            encoding="utf-8",
        )
    _git(project, "init", "-q")
    _git(project, "add", "-A")

    assert cli.main(["layout", str(project)]) == 2
    error = capsys.readouterr().err
    assert (
        "does not look like a workspace" in error
        if not with_cruft
        else "not a workspace" in error
    )


@pytest.mark.functional
def test_layout_command_refuses_unrelated_repository_with_agents(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An AGENTS.md alone does not make a repository a workspace."""
    _git(tmp_path, "init", "-q")
    (tmp_path / "AGENTS.md").write_text(
        "# Instructions\n\n## Local rules\n", encoding="utf-8"
    )
    _git(tmp_path, "add", "AGENTS.md")

    assert cli.main(["layout", str(tmp_path)]) == 2
    assert "does not look like a workspace" in capsys.readouterr().err


@pytest.mark.functional
def test_layout_accepts_cruft_workspace_kind_without_directory(
    render: Render, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cruft metadata can identify the template through its saved context."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps(
            {
                "context": {
                    "cookiecutter": {
                        "repo_name": project.name,
                        "_template_kind": "workspace",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    _git(project, "init", "-q")

    assert cli.main(["layout", str(project)]) != 2
    assert "not a workspace" not in capsys.readouterr().err


@pytest.mark.functional
def test_layout_accepts_workspace_directory_without_saved_context(
    render: Render, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An explicit workspace directory is sufficient without saved answers."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps({"directory": "workspace", "context": {}}),
        encoding="utf-8",
    )
    _git(project, "init", "-q")

    assert cli.main(["layout", str(project)]) != 2
    assert "not a workspace" not in capsys.readouterr().err


@pytest.mark.functional
def test_layout_refuses_cruft_without_workspace_identity(
    render: Render, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cruft metadata without either workspace identity is refused."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps({"context": {"cookiecutter": {"repo_name": project.name}}}),
        encoding="utf-8",
    )
    _git(project, "init", "-q")

    assert cli.main(["layout", str(project)]) == 2
    assert "not a workspace" in capsys.readouterr().err


@pytest.mark.functional
def test_layout_refuses_cruft_naming_another_template_directory(
    render: Render, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A record whose directory names another template is refused alone."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps({"directory": "paper"}), encoding="utf-8"
    )
    _git(project, "init", "-q")

    assert cli.main(["layout", str(project)]) == 2
    assert "not a workspace" in capsys.readouterr().err


@pytest.mark.functional
def test_layout_refuses_cruft_with_non_object_metadata(
    render: Render, tmp_path: Path
) -> None:
    """The cruft record itself must be an object."""
    project = _project(render, tmp_path, cruft=False)
    (project / ".cruft.json").write_text("[]", encoding="utf-8")

    with pytest.raises(FoundryError, match="not a workspace"):
        check_layout(project)


@pytest.mark.functional
def test_layout_refuses_workspace_directory_with_other_template_kind(
    render: Render, tmp_path: Path
) -> None:
    """A conflicting saved template kind invalidates workspace metadata."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps(
            {
                "directory": "workspace",
                "context": {"cookiecutter": {"_template_kind": "paper"}},
            }
        ),
        encoding="utf-8",
    )
    _git(project, "init", "-q")

    with pytest.raises(FoundryError, match="not a workspace"):
        check_layout(project)


@pytest.mark.functional
def test_layout_refuses_cruft_with_non_object_context(
    render: Render, tmp_path: Path
) -> None:
    """A present cruft context must be an object."""
    project = render("workspace", tmp_path)
    (project / ".cruft.json").write_text(
        json.dumps({"directory": "workspace", "context": []}),
        encoding="utf-8",
    )
    _git(project, "init", "-q")

    with pytest.raises(FoundryError, match="invalid answers"):
        check_layout(project)


@pytest.mark.functional
def test_layout_refuses_unreadable_cruft_record(
    render: Render, tmp_path: Path
) -> None:
    """Malformed cruft JSON is reported as an unreadable record."""
    project = _project(render, tmp_path, cruft=False)
    (project / ".cruft.json").write_text("{", encoding="utf-8")

    with pytest.raises(FoundryError, match="unreadable"):
        check_layout(project)


@pytest.mark.functional
def test_layout_refuses_unreadable_agents_file(
    render: Render, tmp_path: Path
) -> None:
    """AGENTS.md must be readable as UTF-8."""
    project = _project(render, tmp_path, cruft=False)
    (project / "AGENTS.md").write_bytes(b"\xff")
    _index(project)

    with pytest.raises(FoundryError, match="AGENTS.md is unreadable"):
        check_layout(project)


@pytest.mark.functional
def test_layout_refuses_a_workspace_subdirectory(
    render: Render, tmp_path: Path
) -> None:
    """The checked path must be the Git repository root."""
    project = _project(render, tmp_path, cruft=False)
    subdirectory = project / "baselines"

    with pytest.raises(FoundryError, match="not the Git repository root"):
        check_layout(subdirectory)


@pytest.mark.functional
def test_layout_refuses_a_non_directory(tmp_path: Path) -> None:
    """A file path is not a workspace directory."""
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("text\n", encoding="utf-8")

    with pytest.raises(FoundryError, match="not a directory"):
        check_layout(file_path)


@pytest.mark.functional
def test_layout_refuses_when_git_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing Git executable is reported as a repository refusal."""

    def missing_git(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", missing_git)

    with pytest.raises(FoundryError, match="not a Git repository"):
        check_layout(tmp_path)


@pytest.mark.functional
def test_empty_required_directory_is_missing_from_git_view(
    render: Render, tmp_path: Path
) -> None:
    """An empty on-disk required directory is absent from the Git view."""
    project = _project(render, tmp_path, cruft=False)
    shutil.rmtree(project / "lit-reviews")
    (project / "lit-reviews").mkdir()
    _index(project)

    assert any(
        item.kind == "missing" and item.path == "lit-reviews"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_ignored_only_required_directory_is_missing_from_git_view(
    render: Render, tmp_path: Path
) -> None:
    """Ignored content does not make a required directory present."""
    project = _project(render, tmp_path, cruft=False)
    shutil.rmtree(project / "lit-reviews")
    (project / ".gitignore").write_text("/lit-reviews/**\n", encoding="utf-8")
    directory = project / "lit-reviews"
    directory.mkdir()
    (directory / "ignored.md").write_text("ignored\n", encoding="utf-8")
    _index(project)

    assert any(
        item.kind == "missing" and item.path == "lit-reviews"
        for item in check_layout(project).findings
    )


@pytest.mark.functional
def test_missing_agents_file_reports_missing_local_rules(
    render: Render, tmp_path: Path
) -> None:
    """An absent instructions file is reported even without its section."""
    project = _project(render, tmp_path, cruft=True)
    (project / "AGENTS.md").unlink()
    _index(project)

    findings = check_layout(project).findings

    assert LayoutFinding("missing-local-rules", "AGENTS.md") in findings
    assert LayoutFinding("missing", "AGENTS.md") in findings


@pytest.mark.functional
def test_untracked_ignored_agents_file_reports_missing_local_rules(
    render: Render, tmp_path: Path
) -> None:
    """Instructions on disk that Git ignores do not reach a clone."""
    project = _project(render, tmp_path, cruft=True)
    with (project / ".gitignore").open("a", encoding="utf-8") as ignore:
        ignore.write("AGENTS.md\n")
    _git(project, "rm", "-q", "--cached", "--ignore-unmatch", "AGENTS.md")
    _index(project)
    assert (project / "AGENTS.md").is_file()

    findings = check_layout(project).findings

    assert LayoutFinding("missing-local-rules", "AGENTS.md") in findings
    assert LayoutFinding("missing", "AGENTS.md") in findings


@pytest.mark.functional
def test_missing_agents_file_without_cruft_is_refused(
    render: Render,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A workspace missing Git-visible instructions needs identification."""
    project = _project(render, tmp_path, cruft=False)
    (project / "AGENTS.md").unlink()
    _index(project)

    assert cli.main(["layout", str(project)]) == 2
    assert "does not look like a workspace" in capsys.readouterr().err
