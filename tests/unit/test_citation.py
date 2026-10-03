"""The README citation stays in step with ``CITATION.cff``."""

import datetime
import re
from collections.abc import Mapping
from typing import cast

import pytest
import yaml
from tests.conftest import ROOT

BIBTEX_BLOCK = re.compile(
    r"^```bibtex[ \t]*\n(?P<body>.*?)\n```[ \t]*$", re.MULTILINE | re.DOTALL
)
SOFTWARE_ENTRY = re.compile(
    r"^@software\{research_foundry,\s*\n(?P<fields>.*?)\n\}$", re.DOTALL
)
BIBTEX_FIELD = re.compile(
    r"^[ \t]*([A-Za-z][A-Za-z0-9_-]*)[ \t]*=[ \t]*\{([^{}]*)\},?[ \t]*$"
)


def _load_citation() -> Mapping[str, object]:
    metadata = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert isinstance(metadata, dict)
    return cast(dict[str, object], metadata)


def _required_string(metadata: Mapping[str, object], field: str) -> str:
    value = metadata[field]
    assert isinstance(value, str), f"CITATION.cff {field} must be a string"
    return value


def _authors(metadata: Mapping[str, object]) -> str:
    authors = metadata["authors"]
    assert isinstance(authors, list)
    names: list[str] = []
    for raw_author in authors:
        assert isinstance(raw_author, dict)
        author = cast(dict[str, object], raw_author)
        family_names = author["family-names"]
        given_names = author["given-names"]
        assert isinstance(family_names, str)
        assert isinstance(given_names, str)
        names.append(f"{family_names}, {given_names}")
    return " and ".join(names)


def _release_year(metadata: Mapping[str, object]) -> str | None:
    released = metadata.get("date-released")
    if released is None:
        return None
    if isinstance(released, datetime.date):
        return str(released.year)
    assert isinstance(released, str)
    match = re.fullmatch(r"(\d{4})-\d{2}-\d{2}", released)
    assert match is not None
    return match.group(1)


def _parse_bibtex(readme_text: str) -> dict[str, str]:
    blocks = [
        match.group("body") for match in BIBTEX_BLOCK.finditer(readme_text)
    ]
    assert len(blocks) == 1, "README must contain exactly one bibtex block"

    entry = SOFTWARE_ENTRY.fullmatch(blocks[0])
    assert entry is not None, (
        "bibtex block must contain exactly one "
        "@software{research_foundry, ...} entry"
    )

    fields: dict[str, str] = {}
    for line in entry.group("fields").splitlines():
        match = BIBTEX_FIELD.fullmatch(line)
        assert match is not None, f"invalid BibTeX field: {line}"
        name, value = match.groups()
        assert name not in fields, f"duplicate BibTeX field: {name}"
        fields[name] = value
    return fields


def _assert_citation_matches(readme_text: str) -> None:
    metadata = _load_citation()
    expected = {
        "author": _authors(metadata),
        "title": _required_string(metadata, "title"),
        "version": _required_string(metadata, "version"),
        "url": _required_string(metadata, "repository-code"),
        "license": _required_string(metadata, "license"),
    }

    year = _release_year(metadata)
    if year is not None:
        expected["year"] = year
    doi = metadata.get("doi")
    if doi is not None:
        assert isinstance(doi, str)
        expected["doi"] = doi

    assert _parse_bibtex(readme_text) == expected


@pytest.mark.unit
def test_readme_citation_matches_citation_file_format() -> None:
    """The documented BibTeX entry matches every citation metadata field."""
    _assert_citation_matches((ROOT / "README.md").read_text(encoding="utf-8"))


@pytest.mark.unit
def test_citation_guard_refuses_wrong_version() -> None:
    """The comparison refuses a version that differs from the metadata."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changed = readme.replace("version = {0.1.0}", "version = {9.9.9}")
    assert changed != readme

    with pytest.raises(AssertionError):
        _assert_citation_matches(changed)


@pytest.mark.unit
def test_citation_guard_refuses_wrong_url() -> None:
    """The comparison refuses a URL that differs from the metadata."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changed = readme.replace(
        "url = {https://github.com/kaustubhharapanahalli/research-foundry}",
        "url = {https://example.com/research-foundry}",
    )
    assert changed != readme

    with pytest.raises(AssertionError):
        _assert_citation_matches(changed)


@pytest.mark.unit
def test_citation_guard_refuses_missing_bibtex_block() -> None:
    """The comparison refuses README text without a BibTeX block."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changed, replacements = BIBTEX_BLOCK.subn("", readme)
    assert replacements == 1

    with pytest.raises(AssertionError, match="exactly one bibtex block"):
        _assert_citation_matches(changed)
