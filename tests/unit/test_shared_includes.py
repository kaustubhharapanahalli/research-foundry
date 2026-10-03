"""Every include resolves, and nothing in _shared is left unused."""

from pathlib import Path

import pytest
from tests.conftest import INCLUDE, PROJECT_DIR, ROOT, SHARED, template_kinds


def _template_files(kind: str) -> list[Path]:
    return [p for p in (ROOT / kind / PROJECT_DIR).rglob("*") if p.is_file()]


def _includes() -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for kind in template_kinds():
        for path in _template_files(kind):
            for name in INCLUDE.findall(path.read_text()):
                found.setdefault(name, []).append(path)
    return found


def _expand(name: str) -> list[str]:
    # An include ending in "/" is completed by a variable, such as
    # "licenses/" ~ cookiecutter.license, so it may use any file there.
    if name.endswith("/"):
        return [
            str(p.relative_to(SHARED))
            for p in (SHARED / name).iterdir()
            if p.is_file()
        ]
    return [name]


@pytest.mark.parametrize("name", sorted(_includes()))
def test_include_target_exists(name: str) -> None:
    if name.endswith("/"):
        assert (SHARED / name).is_dir() and _expand(name), name
    else:
        assert (SHARED / name).is_file(), f"{name} is included but missing"


def test_no_shared_file_is_orphaned() -> None:
    used = {target for name in _includes() for target in _expand(name)}
    shared = {
        str(p.relative_to(SHARED))
        for p in SHARED.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert shared - used == set(), "shared files no template includes"


def test_licence_texts_match_the_repository_licence() -> None:
    # The repository's LICENSE is a checked copy, like its .gitignore.
    shared = (SHARED / "licenses" / "Apache-2.0").read_text()
    assert (ROOT / "LICENSE").read_text() == shared


def test_repo_dogfoods_the_shared_editorconfig() -> None:
    # The repository uses the base it ships, through a link, not a copy.
    link = ROOT / ".editorconfig"
    assert link.is_symlink()
    assert link.resolve() == (SHARED / "base" / "editorconfig").resolve()


def test_repo_gitignore_matches_the_shared_one() -> None:
    # Git will not read a .gitignore through a symlink ("Too many levels of
    # symbolic links"), so this one is a checked copy instead of a link.
    shared = (SHARED / "base" / "gitignore").read_text()
    assert "{{" not in shared and "{%" not in shared
    assert (ROOT / ".gitignore").read_text() == shared
