"""Every skill in skills/ is installable and says where its rules live."""

import re
from pathlib import Path

import pytest
from tests.conftest import ROOT

SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
#: A skill cites the Foundry document that holds each rule it applies.
CITATION = re.compile(r"ADR \d{4}|PD\d+|docs/[\w./-]+\.md")


def _frontmatter(skill: Path) -> dict[str, str]:
    text = (skill / "SKILL.md").read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"{skill.name} has no frontmatter"
    return dict(
        line.split(": ", 1) for line in match.group(1).splitlines() if line
    )


@pytest.mark.unit
def test_there_are_skills() -> None:
    assert {s.name for s in SKILLS} >= {
        "ci-local", "paper-build", "public-docs", "publish", "release",
        "template-update",
    }  # fmt: skip


@pytest.mark.unit
@pytest.mark.parametrize("skill", SKILLS, ids=[s.name for s in SKILLS])
def test_each_skill_names_itself_and_says_when_to_use_it(skill: Path) -> None:
    meta = _frontmatter(skill)
    assert meta.get("name") == skill.name
    assert re.search(r"\bUse (when|before)\b", meta.get("description", ""))


@pytest.mark.unit
@pytest.mark.parametrize(
    "skill",
    [s for s in SKILLS if s.name != "ci-local"],
    ids=[s.name for s in SKILLS if s.name != "ci-local"],
)
def test_each_skill_cites_where_its_rules_live(skill: Path) -> None:
    # ci-local applies no written rule; it diagnoses the make ci contract.
    assert CITATION.search((skill / "SKILL.md").read_text()), skill.name
