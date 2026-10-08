"""The workspace template keeps every path the research tools rely on."""

import re
import subprocess
import sys
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


def test_deck_files_use_git_lfs(render: Render) -> None:
    attributes = render("workspace") / ".gitattributes"
    assert attributes.read_text() == (
        "# Deck masters can exceed the large-file hook limit; "
        "track them with Git LFS.\n"
        "*.pptx filter=lfs diff=lfs merge=lfs -text\n"
        "*.potx filter=lfs diff=lfs merge=lfs -text\n"
    )


def test_install_configures_git_lfs_when_available(render: Render) -> None:
    makefile = (render("workspace") / "Makefile").read_text()
    assert "if git lfs version >/dev/null 2>&1; then" in makefile
    assert "git lfs install --local;" in makefile
    # Only inside a git repository: outside one, install must still succeed.
    install = makefile.split("install:", 1)[1].split("\n\n", 1)[0]
    assert install.index("git rev-parse --git-dir") < install.index(
        "git lfs install --local"
    )
    assert (
        "Git LFS is not installed; install it from https://git-lfs.com/"
        in makefile
    )


def test_git_lfs_deck_passes_large_file_hook(
    render: Render, tmp_path: Path
) -> None:
    _require_git_lfs()

    _assert_large_file_hook_result(
        render, tmp_path, "master.pptx", succeeds=True
    )


def test_untracked_binary_fails_large_file_hook(
    render: Render, tmp_path: Path
) -> None:
    _require_git_lfs()

    _assert_large_file_hook_result(
        render, tmp_path, "master.bin", succeeds=False
    )


def _require_git_lfs() -> None:
    """Skip Git LFS behavior tests only when the Git LFS command is absent."""
    result = subprocess.run(
        ["git", "lfs", "version"], check=False, capture_output=True
    )
    if result.returncode != 0:
        pytest.skip("Git LFS is required to exercise the deck tracking rule")


def _assert_large_file_hook_result(
    render: Render, tmp_path: Path, filename: str, *, succeeds: bool
) -> None:
    """Check the actual large-file hook result for a staged 600 KB file."""
    project = render("workspace", out=tmp_path / filename.replace(".", "-"))
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(
        ["git", "lfs", "install", "--local"], cwd=project, check=True
    )
    deck = project / "presentations" / "demo" / filename
    deck.parent.mkdir(parents=True)
    deck.write_bytes(b"x" * (600 * 1024))
    subprocess.run(
        ["git", "add", str(deck.relative_to(project))], cwd=project, check=True
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pre_commit_hooks.check_added_large_files",
            str(deck.relative_to(project)),
        ],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) is succeeds, result.stdout + result.stderr
