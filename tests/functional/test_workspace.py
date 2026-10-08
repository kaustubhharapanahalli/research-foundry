"""The workspace template keeps every path the research tools rely on."""

import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from tests.conftest import SHARED

Render = Callable[..., Path]

# Paths skills and tools read or write; a rename makes the project invisible
# to them. The layout is recorded in ADR 0009.
CONTRACT = [
    "datasets/registry.yaml",
    "methodology/theory",
    "lit-reviews",
    "baselines",
    "experiments/configs",
    "results",
    "advisor-logs",
    "presentations/_base",
    "docs/adr",
    "AGENTS.md",
]


@pytest.mark.parametrize("path", CONTRACT)
def test_contract_path_exists(path: str, render: Render) -> None:
    assert (render("workspace") / path).exists(), path


def test_dataset_registry_starts_empty(render: Render) -> None:
    # Empty is honest; a seeded registry would describe somebody else's data.
    text = (render("workspace") / "datasets/registry.yaml").read_text()
    assert yaml.safe_load(text) is None
    assert "benchmark_ref" in text


def _synthesis_pointers(text: str) -> list[str]:
    """Return each mention of SYNTHESIS.md that is not "no `SYNTHESIS.md`"."""
    return [
        match.group(0)
        for match in re.finditer(
            r"(?:\bno )?`?(?:lit-reviews/)?SYNTHESIS\.md`?",
            " ".join(text.split()),
        )
        if not match.group(0).startswith("no `SYNTHESIS.md`")
    ]


def test_workspace_keeps_no_synthesis_file(render: Render) -> None:
    # The literature synthesis is read across the review records for each
    # paper, so no file may tell a workspace to keep one. Saying there is
    # none is allowed, and is the one way the name may appear.
    project = render("workspace")
    assert not (project / "lit-reviews/SYNTHESIS.md").exists()
    found = {
        str(path.relative_to(project)): _synthesis_pointers(
            path.read_text(errors="replace")
        )
        for path in project.rglob("*")
        if path.is_file()
    }
    assert not {name: hits for name, hits in found.items() if hits}
    agents = " ".join((project / "AGENTS.md").read_text().split())
    assert "There is no `SYNTHESIS.md`" in agents


def test_a_pointer_to_synthesis_is_caught() -> None:
    old = "`lit-reviews/SYNTHESIS.md` once the review is synthesised."
    assert _synthesis_pointers(old) == ["`lit-reviews/SYNTHESIS.md`"]
    assert (
        _synthesis_pointers("There is no `SYNTHESIS.md`: the synthesis") == []
    )
    assert _synthesis_pointers("write SYNTHESIS.md here") == ["SYNTHESIS.md"]


@pytest.mark.parametrize(
    ("path", "ignored"),
    [
        ("results/batch-1/metrics.csv", True),
        ("results/.gitkeep", False),
        ("results/batch-1/ACCEPTED.md", False),
        ("results/batch-1/seed-0/ACCEPTED.md", False),
        ("baselines/paper/runs/log.txt", True),
        (".work/scratch.md", True),
        ("methodology/theory/block.md", False),
    ],
)
def test_ignore_rules(path: str, ignored: bool, render: Render) -> None:
    project = render("workspace")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    done = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=project, check=False
    )
    assert (done.returncode == 0) is ignored


def test_frontmatter_checker_is_the_shared_one(render: Render) -> None:
    shipped = render("workspace") / ".dev-config/check_frontmatter.py"
    shared = SHARED / "docs" / "check_frontmatter.py"
    assert shipped.read_text() == shared.read_text()
