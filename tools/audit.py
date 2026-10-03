"""Audit Foundry and generated projects from their locked dependencies.

The lock is exported with ``uv`` before ``pip-audit`` reads it, so the audit
examines the resolution that a project actually installs.

Examples:
--------
Audit Foundry alone::

    uv run python -m tools.audit

Audit Foundry and every project below a generated-project directory::

    uv run python -m tools.audit --generated build/generated
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Run = Callable[..., subprocess.CompletedProcess[str]]


def _projects(root: Path, generated: Path | None) -> list[Path]:
    """Return the project roots whose lock files must be audited."""
    projects = [root]
    if generated is not None:
        locks = sorted(generated.rglob("uv.lock"))
        projects.extend(lock.parent for lock in locks)
    return projects


def _audit(project: Path, requirements: Path, run: Run) -> tuple[bool, str]:
    """Export and audit one project's lock, returning success and output."""
    exported = run(
        [
            "uv",
            "export",
            "--frozen",
            "--format",
            "requirements-txt",
            "--output-file",
            str(requirements),
        ],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    if exported.returncode:
        detail = (exported.stdout + exported.stderr).strip()
        return False, detail or "uv export failed without output"
    audited = run(
        ["pip-audit", "--requirement", str(requirements)],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    detail = (audited.stdout + audited.stderr).strip()
    if audited.returncode:
        return False, detail or "pip-audit failed without output"
    return True, detail


def _write_report(path: Path, reports: list[tuple[Path, bool, str]]) -> None:
    """Write the issue-ready audit report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Weekly dependency audit", ""]
    for project, clean, detail in reports:
        lines.extend(
            [
                f"## `{project}`",
                "",
                (
                    "No known vulnerabilities found."
                    if clean
                    else "The audit failed or found vulnerabilities:"
                ),
                "",
            ]
        )
        if detail:
            lines.extend(["```text", detail, "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None, *, run: Run | None = None) -> int:
    """Audit locked dependencies and return non-zero on any finding.

    Parameters
    ----------
    argv
        Command-line arguments. ``None`` reads :data:`sys.argv`.
    run
        Injectable subprocess boundary, used by the offline unit tests.

    Returns:
    -------
    int
        Zero when every lock is clean; one otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--generated", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    runner = run or subprocess.run
    projects = _projects(args.root.resolve(), args.generated)
    reports: list[tuple[Path, bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="foundry-audit-") as temporary:
        requirements = Path(temporary) / "requirements.txt"
        for project in projects:
            if not (project / "uv.lock").is_file():
                reports.append((project, False, "uv.lock is missing"))
                continue
            clean, detail = _audit(project, requirements, runner)
            reports.append((project, clean, detail))
            if clean:
                print(f"No known vulnerabilities found: {project}")
            else:
                print(f"Dependency audit failed: {project}\n{detail}")
    report = args.report or args.root / "build" / "audit-report.md"
    _write_report(report, reports)
    return int(any(not clean for _, clean, _ in reports))


if __name__ == "__main__":
    sys.exit(main())
