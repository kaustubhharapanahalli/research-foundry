"""Focused tests for package-owned rendering behavior."""

import shutil
from pathlib import Path

import pytest
from research_foundry.templates import (
    FoundryError,
    HookRefusal,
    create_project,
    plan_project,
    template_root,
)


def test_unknown_template_names_the_choices(tmp_path: Path) -> None:
    """An unknown template says how to fix the request."""
    with pytest.raises(FoundryError, match="choose one of.*paper"):
        create_project("unknown", {}, tmp_path)
    assert not list(tmp_path.iterdir())


def test_unasked_answer_is_refused_before_writing(tmp_path: Path) -> None:
    """Cookiecutter cannot silently discard a misspelled answer."""
    with pytest.raises(FoundryError, match="does not ask.*typo.*Remove"):
        create_project("workspace", {"typo": "yes"}, tmp_path)
    assert not list(tmp_path.iterdir())


def test_hook_refusal_keeps_its_reason_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """A pre-generation refusal reaches the caller unchanged."""
    with pytest.raises(HookRefusal, match="needs backend_django"):
        create_project(
            "software",
            {"backend_django": "no", "frontend_nextjs": "yes"},
            tmp_path,
        )
    assert not list(tmp_path.iterdir())


def test_plan_lists_files_without_persistent_output(tmp_path: Path) -> None:
    """Planning renders into a temporary directory and cleans it."""
    files = plan_project("workspace", {})
    assert "README.md" in files
    assert not list(tmp_path.iterdir())


def test_wheel_layout_without_template_links_still_renders(
    tmp_path: Path,
) -> None:
    """The runtime restores links omitted from a built wheel."""
    source = tmp_path / "wheel-templates"
    shutil.copytree(template_root(), source, symlinks=True)
    for name in ("methodology", "workspace", "paper", "software"):
        link = source / name / "templates"
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            shutil.rmtree(link)
    project = create_project(
        "workspace", {}, tmp_path / "out", source=source, write_cruft=False
    )
    assert (project / ".editorconfig").is_file()
