"""A public repository has the files a visitor looks for first."""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROJECT_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CITATION.cff",
]


@pytest.mark.parametrize("name", PROJECT_FILES)
def test_project_file_is_present(name: str) -> None:
    """Each file of the public documentation standard's list exists."""
    assert (ROOT / name).is_file()


def test_citation_version_matches_the_package() -> None:
    """GitHub's citation must name the version people actually install."""
    pyproject = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r"^version: (\S+)$", citation, re.MULTILINE)
    assert match is not None
    assert match.group(1) == pyproject["project"]["version"]
