"""Unit tests for the workspace path contract and Local rules."""

# pylint: disable=protected-access

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
from research_foundry import layout
from research_foundry.layout import (
    LayoutRule,
    parse_layout_rules,
    parse_local_rules,
)
from research_foundry.templates import (
    FoundryError,
    create_project,
    plan_project,
)
from tests.conftest import ROOT

CONTRACT_PATH = ROOT / "workspace" / "contract.json"


def test_workspace_contract_is_valid_json_with_complete_entries() -> None:
    """Every contract entry states a supported kind and a purpose."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["about"]
    assert all(
        entry["kind"] in {"file", "dir", "runtime"} and entry["used_by"]
        for entry in contract["entries"]
    )
    assert len({entry["path"] for entry in contract["entries"]}) == len(
        contract["entries"]
    )


def test_workspace_contract_entries_match_a_fresh_render() -> None:
    """Every required file and directory exists, but runtime state does not."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    # plan_project runs the same offline renderer without persistent output.
    files = set(plan_project("workspace", {}))
    directories = {str(Path(name).parent) for name in files}
    directories.update(
        part for name in files for part in _parent_directories(name)
    )

    for entry in contract["entries"]:
        path = layout._contract_target(entry["path"])
        if entry["kind"] == "runtime":
            assert path not in files and path not in directories
        elif entry["kind"] == "file":
            assert path in files
        else:
            assert path in directories


def test_workspace_where_things_go_matches_the_contract() -> None:
    """The documented fixed paths and contract entries agree both ways."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "AGENTS.md" in plan_project("workspace", {})
    with tempfile.TemporaryDirectory() as temporary:
        rendered = create_project("workspace", {}, Path(temporary))
        text = (rendered / "AGENTS.md").read_text(encoding="utf-8")
    section = text.split("## Where things go\n", maxsplit=1)[1].split(
        "\n## ", maxsplit=1
    )[0]
    documented = {
        layout._contract_target(token)
        for token in re.findall(r"`([^`]+)`", section)
        if "/" in token
    }
    contracted = {
        layout._contract_target(entry["path"])
        for entry in contract["entries"]
        if entry["path"] != "AGENTS.md" and entry["kind"] != "runtime"
    }

    assert documented == contracted


@pytest.mark.parametrize(
    ("section", "top_level", "expected"),
    [
        (
            """
- **`experiments/specs/`** (template: `experiments/configs/*.yaml` only).
- `lit-reviews/_notes.md` are local.
""",
            set(),
            {
                "experiments/specs",
                "experiments/configs",
                "lit-reviews/_notes.md",
            },
        ),
        (
            """
- **Extra folders** (adds to the template's layout): `experiments/ledger/`,
  `experiments/progress/`, `archive/` and `docs/runbooks/`.
""",
            set(),
            {
                "experiments/ledger",
                "experiments/progress",
                "archive",
                "docs/runbooks",
            },
        ),
        ("- `notes` is maintained locally.\n", {"notes"}, {"notes"}),
        ("- `ordinary words` are not paths.\n", set(), set()),
    ],
)
def test_local_rules_parse_named_paths(
    section: str, top_level: set[str], expected: set[str]
) -> None:
    """Backticked paths normalize to the path prefix they declare."""
    text = f"# Instructions\n\n## Local rules\n{section}\n## Commands\n"
    assert parse_local_rules(text, top_level) == expected


def test_local_rules_stop_at_the_next_second_level_heading() -> None:
    """Paths after Local rules cannot declare workspace deviations."""
    text = (
        "## Local rules\n- `experiments/local/` is allowed.\n"
        "## Commands\n- `archive/` is not a local rule.\n"
    )

    assert parse_local_rules(text, set()) == {"experiments/local"}


@pytest.mark.parametrize("token", ["/read", "/theory"])
def test_local_rules_ignore_slash_commands(token: str) -> None:
    """Slash commands are not workspace-relative paths."""
    assert parse_local_rules(f"## Local rules\n- `{token}`\n", set()) == set()


@pytest.mark.parametrize(
    ("heading", "tail"),
    [
        ("## Local Rules", ""),
        ("## Local rules (this workspace)", ""),
        ("## Local rules", "```md\n## Example\n- `ignored/path`\n```\n"),
    ],
)
def test_local_rules_heading_and_fences(heading: str, tail: str) -> None:
    """Headings are case-insensitive, may be suffixed, and respect fences."""
    text = (
        f"{heading}\n- `experiments/local/` is allowed.\n"
        f"{tail}## Commands\n- `archive/` is not local.\n"
    )
    assert parse_local_rules(text, set()) == {"experiments/local"}


def test_local_rules_ignore_fenced_backticks() -> None:
    """Backticked text inside a fenced block is not a declaration."""
    text = "## Local rules\n```text\n- `archive/` is an example.\n```\n"
    assert parse_local_rules(text, set()) == set()


def test_fenced_heading_does_not_end_local_rules_section() -> None:
    """A heading inside a fence cannot hide declarations that follow it."""
    text = (
        "## Local rules\n```md\n## Example\n```\n"
        "- `after/fence/` is allowed.\n## Commands\n"
    )

    assert parse_local_rules(text, set()) == {"after/fence"}


@pytest.mark.parametrize(
    "token",
    [
        "/absolute/path",
        "https://example.org/path",
        "../outside/path",
        "foo/bar baz",
    ],
)
def test_local_rules_ignore_non_workspace_paths(token: str) -> None:
    """Absolute, URL, and escaping paths are not workspace-relative."""
    assert parse_local_rules(f"## Local rules\n- `{token}`\n", set()) == set()


def test_layout_rule_parser_recognizes_explicit_deviations() -> None:
    """Moved and Dropped rules normalize contract paths and ignore prose."""
    assert parse_layout_rules(
        "\n".join(
            [
                "## Local rules",
                "- **mOvEd:** `baselines/<paper>/` to `meetings/`.",
                "- dRoPpEd: `advisor-logs/`, because unused.",
                "- Moved: a rule without a backticked path.",
                "- Moved: `lit-reviews/` without a destination.",
                "- **Moved: `experiments/` to `archive/`.",
            ]
        )
    ) == (
        LayoutRule("Moved", "baselines", "meetings"),
        LayoutRule("Dropped", "advisor-logs", None),
    )


@pytest.mark.parametrize(
    "document",
    [
        "{",
        "[]",
        {"about": "", "generated": [], "entries": []},
        {"about": "paths", "generated": "bad", "entries": []},
        {"about": "paths", "generated": [], "entries": {}},
        {"about": "paths", "generated": [], "entries": [None]},
        {
            "about": "paths",
            "generated": [],
            "entries": [{"path": "", "kind": "file", "used_by": "test"}],
        },
        {
            "about": "paths",
            "generated": [],
            "entries": [
                {"path": "valid", "kind": "unknown", "used_by": "test"}
            ],
        },
        {
            "about": "paths",
            "generated": [],
            "entries": [{"path": "valid", "kind": "file", "used_by": ""}],
        },
        {
            "about": "paths",
            "generated": [],
            "entries": [
                {"path": "<paper>/", "kind": "dir", "used_by": "test"}
            ],
        },
        {
            "about": "paths",
            "generated": [],
            "entries": [
                {"path": "baselines/", "kind": "dir", "used_by": "one"},
                {
                    "path": "baselines/<paper>/",
                    "kind": "dir",
                    "used_by": "two",
                },
            ],
        },
    ],
    ids=[
        "unreadable-json",
        "not-an-object",
        "empty-about",
        "bad-generated",
        "entries-not-a-list",
        "entry-not-an-object",
        "empty-path",
        "unknown-kind",
        "empty-used-by",
        "empty-normalized-path",
        "duplicate-target",
    ],
)
def test_invalid_workspace_contract_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, document: object
) -> None:
    """Every malformed contract shape is rejected."""
    contract_path = tmp_path / "workspace" / "contract.json"
    contract_path.parent.mkdir()
    contract_path.write_text(
        document if isinstance(document, str) else json.dumps(document),
        encoding="utf-8",
    )
    monkeypatch.setattr(layout, "template_root", lambda: tmp_path)

    with pytest.raises(FoundryError, match="contract"):
        layout._load_contract()


def test_git_file_listing_failure_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed Git file listing raises the public workspace error."""

    def failed_listing(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.CalledProcessError(1, "git")

    monkeypatch.setattr(subprocess, "run", failed_listing)

    with pytest.raises(FoundryError, match="not a Git repository"):
        layout._git_paths(tmp_path)


def test_runtime_contract_path_is_exempt_from_git_presence() -> None:
    """Runtime entries are never required in Git's path listing."""
    assert layout._entry_is_present(
        {"kind": "runtime", "target": ".agent-state"}, set()
    )


def test_cruft_context_requires_cookiecutter_object(
    tmp_path: Path,
) -> None:
    """A non-object cookiecutter context is rejected."""
    (tmp_path / ".cruft.json").write_text(
        json.dumps(
            {"directory": "workspace", "context": {"cookiecutter": []}}
        ),
        encoding="utf-8",
    )

    with pytest.raises(FoundryError, match="invalid answers"):
        layout._require_workspace(tmp_path, [], set())


def _parent_directories(path: str) -> set[str]:
    """List each parent directory in a rendered relative file path."""
    parents: set[str] = set()
    parent = Path(path).parent
    while parent != Path("."):
        parents.add(parent.as_posix())
        parent = parent.parent
    return parents
