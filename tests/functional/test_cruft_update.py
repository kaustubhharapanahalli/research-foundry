"""A change to the shared base reaches an existing project via cruft."""

import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.conftest import GIT_ENV, ROOT


def _run(*args: str, cwd: Path) -> str:
    env = {**os.environ, **GIT_ENV}
    done = subprocess.run(
        args, cwd=cwd, env=env, check=True, capture_output=True, text=True
    )
    return done.stdout


def _snapshot(dest: Path) -> Path:
    """Copy the working tree into a fresh git repository, links kept."""
    shutil.copytree(
        ROOT,
        dest,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git", ".venv", "*_cache", "build"),
    )
    _run("git", "init", "-q", "-b", "main", cwd=dest)
    _run("git", "add", "-A", cwd=dest)
    _run("git", "commit", "-qm", "snapshot", cwd=dest)
    return dest


@pytest.mark.slow
def test_shared_change_reaches_existing_project(tmp_path: Path) -> None:
    template = _snapshot(tmp_path / "template")
    out = tmp_path / "projects"
    out.mkdir()
    _run(
        "cruft", "create", f"file://{template}",
        "--directory", "methodology", "--no-input",
        "--output-dir", str(out),
        cwd=tmp_path,
    )  # fmt: skip
    project = next(out.iterdir())
    _run("git", "init", "-q", cwd=project)
    _run("git", "add", "-A", cwd=project)
    _run("git", "commit", "-qm", "generated", cwd=project)

    shared = template / "_shared" / "base" / "editorconfig"
    shared.write_text(shared.read_text() + "\n[*.tex]\nindent_size = 2\n")
    _run("git", "commit", "-qam", "shared change", cwd=template)

    # The project's own `make template-check` sees the change, and passes
    # again once cruft has applied it.
    with pytest.raises(subprocess.CalledProcessError):
        _run("make", "template-check", cwd=project)
    _run("cruft", "update", "--skip-apply-ask", cwd=project)

    assert "[*.tex]" in (project / ".editorconfig").read_text()
    _run("make", "template-check", cwd=project)


def test_template_check_refuses_a_project_cruft_did_not_create(
    render: Callable[..., Path],
) -> None:
    project = render("workspace")
    with pytest.raises(subprocess.CalledProcessError) as raised:
        _run("make", "template-check", cwd=project)
    assert "not created with cruft create" in raised.value.stdout


@pytest.mark.slow
def test_public_docs_can_be_turned_on_later(tmp_path: Path) -> None:
    # A methodology repo goes public at publication, long after it was
    # generated; its docs then arrive through cruft, not by hand.
    template = _snapshot(tmp_path / "template")
    out = tmp_path / "projects"
    out.mkdir()
    _run(
        "cruft", "create", f"file://{template}",
        "--directory", "methodology", "--no-input",
        "--output-dir", str(out),
        cwd=tmp_path,
    )  # fmt: skip
    project = next(out.iterdir())
    assert not (project / "docs" / "conf.py").exists()
    _run("git", "init", "-q", cwd=project)
    _run("git", "add", "-A", cwd=project)
    _run("git", "commit", "-qm", "generated", cwd=project)

    _run(
        "cruft", "update", "--skip-apply-ask",
        "--variables-to-update",
        '{"public_docs": "yes", "contact_email": "maintainers@example.org"}',
        cwd=project,
    )  # fmt: skip

    assert (project / "docs" / "conf.py").is_file()
    assert (project / "CODE_OF_CONDUCT.md").is_file()
    assert "include make/docs.mk" in (project / "Makefile").read_text()
