"""Release validation and publication commands are fail-closed."""

import subprocess
from pathlib import Path

import pytest
from tools import release


def _release_files(
    tmp_path: Path,
    version: str = "1.2.3",
    changelog_version: str = "1.2.3",
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "example"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        f"## [{changelog_version}] - 2026-10-02\n\n"
        "### Added\n\n"
        "- Release pipeline.\n"
        "- Provenance attestations.\n\n"
        "## [1.2.2] - 2026-09-01\n\n"
        "- Earlier release.\n",
        encoding="utf-8",
    )


def test_release_check_accepts_tag_matching_project_version(
    tmp_path: Path,
) -> None:
    _release_files(tmp_path)

    version, notes = release.check_release("v1.2.3", tmp_path)

    assert version == "1.2.3"
    assert notes == (
        "### Added\n\n" "- Release pipeline.\n" "- Provenance attestations."
    )


def test_release_check_refuses_tag_mismatch(tmp_path: Path) -> None:
    _release_files(tmp_path)

    with pytest.raises(release.ReleaseError, match="expected v1.2.3"):
        release.check_release("v1.2.4", tmp_path)


def test_release_check_refuses_missing_changelog_section(
    tmp_path: Path,
) -> None:
    _release_files(tmp_path, version="2.0.0")

    with pytest.raises(release.ReleaseError, match=r"CHANGELOG.*2\.0\.0"):
        release.check_release("v2.0.0", tmp_path)


def test_changelog_section_is_extracted_exactly_to_next_version(
    tmp_path: Path,
) -> None:
    _release_files(tmp_path)

    notes = release.changelog_section(tmp_path / "CHANGELOG.md", "1.2.3")

    assert notes == (
        "### Added\n\n" "- Release pipeline.\n" "- Provenance attestations."
    )


def test_empty_changelog_section_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(
        "## [1.2.3] - 2026-10-02\n\n## [1.2.2] - 2026-09-01\n",
        encoding="utf-8",
    )

    with pytest.raises(release.ReleaseError, match="section.*empty"):
        release.changelog_section(path, "1.2.3")


def test_missing_project_version_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "example"\n', encoding="utf-8")

    with pytest.raises(release.ReleaseError, match="project.version"):
        release.project_version(path)


@pytest.mark.parametrize(
    ("output", "allowed"),
    [
        ("false\n", True),
        ("true\n", False),
        ("", False),
        (" false \n", False),
    ],
)
def test_private_repository_check_only_accepts_exact_false(
    output: str, allowed: bool
) -> None:
    assert release.public_repository_output(output) is allowed


@pytest.mark.parametrize(
    ("output", "expected"),
    [("false\n", 0), ("true\n", 1), ("", 1)],
)
def test_refuse_private_never_runs_real_gh(
    monkeypatch: pytest.MonkeyPatch, output: str, expected: int
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, output, "")

    monkeypatch.setattr(release, "run_command", fake_run)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/project")

    assert release.refuse_private() == expected
    assert calls == [["gh", "api", "repos/owner/project", "--jq", ".private"]]


def test_refuse_private_fails_when_repository_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    assert release.refuse_private() == 1


def test_github_release_uses_validated_notes_and_every_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _release_files(tmp_path)
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "example-1.2.3-py3-none-any.whl"
    source = dist / "example-1.2.3.tar.gz"
    wheel.write_text("wheel", encoding="utf-8")
    source.write_text("source", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(release, "run_command", fake_run)

    assert release.create_github_release("v1.2.3", tmp_path) == 0
    assert calls == [
        [
            "gh",
            "release",
            "create",
            "v1.2.3",
            str(wheel),
            str(source),
            "--title",
            "1.2.3",
            "--notes",
            "### Added\n\n"
            "- Release pipeline.\n"
            "- Provenance attestations.",
        ]
    ]


def test_github_release_marks_release_candidate_as_prerelease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _release_files(tmp_path, version="0.1.0rc1", changelog_version="0.1.0rc1")
    dist = tmp_path / "dist"
    dist.mkdir()
    artifact = dist / "example-0.1.0rc1.tar.gz"
    artifact.write_text("source", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(release, "run_command", fake_run)

    assert release.create_github_release("v0.1.0rc1", tmp_path) == 0
    assert "--prerelease" in calls[0]


def test_github_release_does_not_mark_stable_version_as_prerelease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _release_files(tmp_path, version="0.1.0", changelog_version="0.1.0")
    dist = tmp_path / "dist"
    dist.mkdir()
    artifact = dist / "example-0.1.0.tar.gz"
    artifact.write_text("source", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(release, "run_command", fake_run)

    assert release.create_github_release("v0.1.0", tmp_path) == 0
    assert "--prerelease" not in calls[0]


def test_github_release_refuses_missing_distributions(tmp_path: Path) -> None:
    _release_files(tmp_path)

    with pytest.raises(release.ReleaseError, match="no release artifacts"):
        release.create_github_release("v1.2.3", tmp_path)


@pytest.mark.parametrize(
    ("argv", "target", "expected"),
    [
        (["check", "--tag", "v1.2.3"], "check_release", 0),
        (["github-release", "--tag", "v1.2.3"], "create_github_release", 7),
        (["refuse-private"], "refuse_private", 1),
    ],
)
def test_main_dispatches_commands(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    target: str,
    expected: int,
) -> None:
    if target == "check_release":
        monkeypatch.setattr(
            release, target, lambda tag: (tag.removeprefix("v"), "notes")
        )
    elif target == "create_github_release":
        monkeypatch.setattr(release, target, lambda tag: 7)
    else:
        monkeypatch.setattr(release, target, lambda: 1)

    assert release.main(argv) == expected


def test_main_reports_release_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_tag: str) -> tuple[str, str]:
        raise release.ReleaseError("bad release")

    monkeypatch.setattr(release, "check_release", refuse)

    assert release.main(["check", "--tag", "v1.2.3"]) == 1
