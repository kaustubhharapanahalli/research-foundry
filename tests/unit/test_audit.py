"""Dependency audits export locks and report every vulnerable project."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from tools import audit


def _completed(
    argv: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def test_clean_lock_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "uv.lock").touch()
    calls: list[tuple[list[str], Path]] = []

    def fake_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append((argv, Path(str(kwargs["cwd"]))))
        return _completed(argv)

    result = audit.main(["--root", str(tmp_path)], run=fake_run)

    assert result == 0
    assert [call[0][0] for call in calls] == ["uv", "pip-audit"]
    assert "No known vulnerabilities" in capsys.readouterr().out


def test_finding_fails_and_is_printed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "uv.lock").touch()

    def fake_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        del kwargs
        if argv[0] == "pip-audit":
            finding = "urllib3 1.0 CVE-EXAMPLE fixed in 2.0\n"
            return _completed(argv, 1, finding)
        return _completed(argv)

    result = audit.main(["--root", str(tmp_path)], run=fake_run)

    assert result == 1
    assert "urllib3 1.0 CVE-EXAMPLE fixed in 2.0" in capsys.readouterr().out


def test_generated_projects_are_all_audited(tmp_path: Path) -> None:
    root = tmp_path / "foundry"
    generated = tmp_path / "generated"
    (root / "uv.lock").parent.mkdir(parents=True)
    (root / "uv.lock").touch()
    for name in ("alpha", "nested/beta"):
        lock = generated / name / "uv.lock"
        lock.parent.mkdir(parents=True)
        lock.touch()
    audited: list[Path] = []

    def fake_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if argv[0] == "pip-audit":
            audited.append(Path(str(kwargs["cwd"])))
        return _completed(argv)

    result = audit.main(
        ["--root", str(root), "--generated", str(generated)], run=fake_run
    )

    assert result == 0
    assert audited == [root, generated / "alpha", generated / "nested/beta"]


def test_missing_lock_is_reported_without_running_tools(
    tmp_path: Path,
) -> None:
    report = tmp_path / "reports" / "audit.md"

    def unexpected_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"unexpected subprocess: {argv}, {kwargs}")

    result = audit.main(
        ["--root", str(tmp_path), "--report", str(report)],
        run=unexpected_run,
    )

    assert result == 1
    assert "uv.lock is missing" in report.read_text(encoding="utf-8")


def test_export_failure_is_reported_without_audit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "uv.lock").touch()
    calls: list[str] = []

    def fake_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(argv[0])
        return _completed(argv, 2, stderr="resolution failed\n")

    result = audit.main(["--root", str(tmp_path)], run=fake_run)

    assert result == 1
    assert calls == ["uv"]
    assert "resolution failed" in capsys.readouterr().out
