"""Unit tests for the workspace path contract and Local rules."""

import json
from pathlib import Path

import pytest
from research_foundry.layout import parse_local_rules
from research_foundry.templates import plan_project
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
        path = _contract_target(entry["path"])
        if entry["kind"] == "runtime":
            assert path not in files and path not in directories
        elif entry["kind"] == "file":
            assert path in files
        else:
            assert path in directories


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


def _contract_target(path: str) -> str:
    """Return the fixed path prefix represented by a contract path."""
    components = path.strip("/").split("/")
    for index, component in enumerate(components):
        if "<" in component or "*" in component:
            components = components[:index]
            break
    return "/".join(components)


def _parent_directories(path: str) -> set[str]:
    """List each parent directory in a rendered relative file path."""
    parents: set[str] = set()
    parent = Path(path).parent
    while parent != Path("."):
        parents.add(parent.as_posix())
        parent = parent.parent
    return parents
