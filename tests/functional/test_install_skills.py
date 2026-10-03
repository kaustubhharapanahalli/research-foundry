"""`make install-skills`: install, update, and refuse an edited copy.

Every test installs into a temporary home. The autouse fixture points HOME
and CLAUDE_CONFIG_DIR there, so nothing here can reach a real
~/.claude/skills: installing for real is a person's step.
"""

import json
from pathlib import Path

import pytest
from tools import install_skills as inst


@pytest.fixture(autouse=True)
def _temporary_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "home" / ".claude"))


@pytest.fixture(name="source")
def source_fixture(tmp_path: Path) -> Path:
    src = tmp_path / "skills"
    (src / "publish").mkdir(parents=True)
    (src / "publish" / "SKILL.md").write_text("# Publish\n")
    (src / "release").mkdir()
    (src / "release" / "SKILL.md").write_text("# Release\n")
    (src / "README.md").write_text("Not a skill.\n")
    return src


@pytest.fixture(name="dest")
def dest_fixture(tmp_path: Path) -> Path:
    return tmp_path / "home" / ".claude" / "skills"


@pytest.mark.functional
def test_the_destination_is_the_users_claude_skills(tmp_path: Path) -> None:
    assert inst.destination() == tmp_path / "home" / ".claude" / "skills"
    home_only = {"HOME": "/h"}
    assert inst.destination(home_only) == Path("/h/.claude/skills")
    assert inst.destination({"HOME": "/h", "CLAUDE_CONFIG_DIR": "/c"}) == Path(
        "/c/skills"
    )


@pytest.mark.functional
def test_a_first_install_writes_every_skill_and_a_manifest(
    source: Path, dest: Path
) -> None:
    report = inst.run("install", source, dest)
    assert report.written == ["publish/SKILL.md", "release/SKILL.md"]
    assert (dest / "publish" / "SKILL.md").read_text() == "# Publish\n"
    assert not (dest / "README.md").exists()
    manifest = json.loads((dest / inst.MANIFEST).read_text())
    assert sorted(manifest) == ["publish/SKILL.md", "release/SKILL.md"]


@pytest.mark.functional
def test_installing_twice_changes_nothing(source: Path, dest: Path) -> None:
    inst.run("install", source, dest)
    before = (dest / inst.MANIFEST).read_bytes()
    report = inst.run("install", source, dest)
    assert not report.written and report.ok
    assert (dest / inst.MANIFEST).read_bytes() == before


@pytest.mark.functional
def test_an_untouched_copy_is_updated_from_the_source(
    source: Path, dest: Path
) -> None:
    inst.run("install", source, dest)
    (source / "publish" / "SKILL.md").write_text("# Publish, revised\n")
    report = inst.run("install", source, dest)
    assert report.written == ["publish/SKILL.md"]
    assert (
        dest / "publish" / "SKILL.md"
    ).read_text() == "# Publish, revised\n"


@pytest.mark.functional
def test_guard_an_edited_copy_is_never_overwritten(
    source: Path, dest: Path
) -> None:
    inst.run("install", source, dest)
    (dest / "publish" / "SKILL.md").write_text("# Fixed where installed\n")
    (source / "publish" / "SKILL.md").write_text("# Publish, revised\n")
    report = inst.run("install", source, dest)
    assert report.drifted == ["publish/SKILL.md"]
    assert (dest / "publish" / "SKILL.md").read_text() == (
        "# Fixed where installed\n"
    )


@pytest.mark.functional
def test_adopt_copies_the_edit_back_into_foundry(
    source: Path, dest: Path
) -> None:
    inst.run("install", source, dest)
    (dest / "publish" / "SKILL.md").write_text("# Fixed where installed\n")
    report = inst.run("adopt", source, dest)
    assert report.adopted == ["publish/SKILL.md"]
    assert (source / "publish" / "SKILL.md").read_text() == (
        "# Fixed where installed\n"
    )
    assert inst.run("check", source, dest).ok


@pytest.mark.functional
def test_force_discards_the_edit(source: Path, dest: Path) -> None:
    inst.run("install", source, dest)
    (dest / "publish" / "SKILL.md").write_text("# Fixed where installed\n")
    report = inst.run("force", source, dest)
    assert report.written == ["publish/SKILL.md"]
    assert (dest / "publish" / "SKILL.md").read_text() == "# Publish\n"


@pytest.mark.functional
@pytest.mark.parametrize("mode", ["install", "force"])
def test_guard_a_skill_foundry_did_not_install_is_never_touched(
    source: Path, dest: Path, mode: str
) -> None:
    (dest / "publish").mkdir(parents=True)
    (dest / "publish" / "SKILL.md").write_text("# Someone's own publish\n")
    (dest / "publish" / "notes.md").write_text("theirs\n")
    report = inst.run(mode, source, dest)
    assert report.foreign == ["publish/SKILL.md"]
    assert (dest / "publish" / "SKILL.md").read_text() == (
        "# Someone's own publish\n"
    )
    assert report.written == ["release/SKILL.md"]


@pytest.mark.functional
def test_check_reports_and_writes_nothing(source: Path, dest: Path) -> None:
    report = inst.run("check", source, dest)
    assert report.missing == ["publish/SKILL.md", "release/SKILL.md"]
    assert not report.ok
    assert not dest.exists()


@pytest.mark.functional
def test_check_names_an_out_of_date_copy(source: Path, dest: Path) -> None:
    inst.run("install", source, dest)
    (source / "release" / "SKILL.md").write_text("# Release, revised\n")
    assert inst.run("check", source, dest).stale == ["release/SKILL.md"]


@pytest.mark.functional
def test_an_unknown_mode_is_refused(source: Path, dest: Path) -> None:
    with pytest.raises(ValueError, match="mode"):
        inst.run("overwrite", source, dest)


@pytest.mark.functional
def test_the_command_installs_foundrys_own_skills_into_the_temporary_home(
    dest: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert inst.main(["--check"]) == 1
    assert inst.main([]) == 0
    assert inst.main(["--check"]) == 0
    for skill in inst.SKILLS.iterdir():
        if skill.is_dir():
            assert (dest / skill.name / "SKILL.md").exists(), skill.name
    assert "skills ->" in capsys.readouterr().out
