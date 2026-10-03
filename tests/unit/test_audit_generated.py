"""Generated projects are locked before their dependencies are audited."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from tools import audit_generated


def test_each_generated_variant_is_locked_then_audited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audit_generated, "ROOT", tmp_path)
    monkeypatch.setattr(
        audit_generated,
        "VARIANTS",
        {"zeta": ("software", {"kind": "z"}), "alpha": ("paper", {})},
    )
    generated: list[tuple[str, dict[str, str], Path, Path]] = []
    locked: list[Path] = []

    def fake_generate(
        template: str,
        answers: dict[str, str],
        *,
        into: Path,
        source: Path,
    ) -> Path:
        generated.append((template, answers, into, source))
        return into / "project"

    def fake_run(
        argv: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        assert argv == ["uv", "lock"]
        assert kwargs["check"] is False
        locked.append(kwargs["cwd"])
        return subprocess.CompletedProcess(argv, 0)

    def fake_audit(argv: list[str]) -> int:
        assert argv[0:2] == ["--root", str(tmp_path)]
        assert argv[2] == "--generated"
        assert Path(argv[3]).name == "generated"
        assert argv[4:] == [
            "--report",
            str(tmp_path / "build" / "audit-report.md"),
        ]
        return 3

    monkeypatch.setattr(audit_generated, "generate", fake_generate)
    monkeypatch.setattr("tools.audit_generated.subprocess.run", fake_run)
    monkeypatch.setattr("tools.audit_generated.audit.main", fake_audit)

    result = audit_generated.main()

    assert result == 3
    assert [item[0] for item in generated] == ["paper", "software"]
    assert all(item[3] == tmp_path for item in generated)
    assert locked == [item[2] / "project" for item in generated]


def test_lock_failure_stops_before_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audit_generated, "ROOT", tmp_path)
    monkeypatch.setattr(
        audit_generated, "VARIANTS", {"only": ("software", {})}
    )
    project = tmp_path / "generated-project"
    monkeypatch.setattr(
        audit_generated, "generate", lambda *args, **kwargs: project
    )
    monkeypatch.setattr(
        "tools.audit_generated.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 7),
    )

    def unexpected_audit(argv: list[str]) -> int:
        raise AssertionError(f"unexpected audit: {argv}")

    monkeypatch.setattr("tools.audit_generated.audit.main", unexpected_audit)

    assert audit_generated.main() == 7
