"""The shared OKF frontmatter checker, tested where it is defined."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from tests.conftest import SHARED


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_frontmatter", SHARED / "docs" / "check_frontmatter.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cf = _load()
GOOD = """---
type: ADR
title: "ADR 0001: A"
description: Why.
resource: /docs/adr/0001-a.md
tags: [adr]
timestamp: 2026-10-01T00:00:00Z
---

# ADR 0001: A
"""


def _problems(text: str, path: str = "docs/adr/0001-a.md") -> list[str]:
    result: list[str] = cf.problems(Path(path), text)
    return result


def test_complete_frontmatter_passes() -> None:
    assert not _problems(GOOD)


def test_no_frontmatter_is_reported() -> None:
    assert _problems("# Title\n") == ["no frontmatter"]


@pytest.mark.parametrize("key", list(cf.REQUIRED))
def test_each_missing_field_is_reported(key: str) -> None:
    text = "\n".join(
        line for line in GOOD.splitlines() if not line.startswith(f"{key}:")
    )
    assert f"missing {key}" in _problems(text + "\n")


def test_tags_must_be_a_list() -> None:
    assert "tags must be a list" in _problems(
        GOOD.replace("tags: [adr]", "tags: adr")
    )


def test_timestamp_as_text_must_be_iso() -> None:
    text = GOOD.replace("2026-10-01T00:00:00Z", '"last tuesday"')
    assert any("ISO 8601" in p for p in _problems(text))


def test_timestamp_as_iso_text_passes() -> None:
    assert not _problems(GOOD.replace("2026-10-01T00:00:00Z", '"2026-10-01"'))


def test_resource_must_name_the_file_itself() -> None:
    found = _problems(GOOD, path="docs/adr/0002-moved.md")
    assert found == [
        "resource is '/docs/adr/0001-a.md', expected '/docs/adr/0002-moved.md'"
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("---\ntitle: A\n# never closed\n", "never closed"),
        ("---\ntitle: [unclosed\n---\n", "not valid YAML"),
        ("---\n- a list\n---\n", "not a mapping"),
    ],
)
def test_unreadable_frontmatter_is_reported(text: str, message: str) -> None:
    (found,) = _problems(text)
    assert message in found


def test_main_skips_exempt_files_and_reports_the_rest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("README.md").write_text("# Readme\n", encoding="utf-8")
    Path("notes.txt").write_text("not markdown\n", encoding="utf-8")
    Path("note.md").write_text("# A note\n", encoding="utf-8")
    assert cf.main(["README.md", "notes.txt", "note.md"]) == 1
    assert capsys.readouterr().out == "note.md: no frontmatter\n"


def test_main_passes_good_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("docs/adr").mkdir(parents=True)
    Path("docs/adr/0001-a.md").write_text(GOOD, encoding="utf-8")
    assert cf.main(["docs/adr/0001-a.md"]) == 0


def test_public_page_frontmatter_accepts_title_and_description_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    docs = Path("docs")
    docs.mkdir()
    (docs / "index.md").write_text(
        "---\ntitle: Home\ndescription: Start here.\n---\n", encoding="utf-8"
    )
    (docs / "adr").mkdir()
    (docs / "adr" / "0001-a.md").write_text(GOOD, encoding="utf-8")
    assert cf.main(["--public-pages", "docs"]) == 0


def test_public_page_frontmatter_refuses_extra_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("docs").mkdir()
    Path("docs/index.md").write_text(
        "---\ntitle: Home\ndescription: Start here.\ntags: [public]\n---\n",
        encoding="utf-8",
    )
    assert cf.main(["--public-pages", "docs"]) == 1
    assert (
        capsys.readouterr().out == "docs/index.md: unexpected fields: tags\n"
    )
