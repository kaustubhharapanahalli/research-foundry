"""Install research-foundry's maintained agent skills for one user.

Examples:
    >>> Report().ok
    True
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST = ".foundry-skills.json"
MODES = ("install", "check", "adopt", "force")


def skills_root() -> Path:
    """Return the installed skills tree or source-checkout fallback.

    Returns:
        A directory containing the maintained skill folders.

    Raises:
        RuntimeError: If neither packaged nor source skills exist.

    Examples:
        >>> (skills_root() / "release" / "SKILL.md").is_file()
        True
    """
    packaged = Path(__file__).resolve().parent / "skills"
    if packaged.is_dir():
        return packaged
    checkout = Path(__file__).resolve().parents[2] / "skills"
    if checkout.is_dir():
        return checkout
    raise RuntimeError(
        "The packaged skills are missing; reinstall research-foundry."
    )


SKILLS = skills_root()


@dataclass
class Report:
    """Describe the files written, adopted, pending, or refused.

    Examples:
        >>> Report(missing=["release/SKILL.md"]).ok
        False
    """

    written: list[str] = field(default_factory=list)
    adopted: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    drifted: list[str] = field(default_factory=list)
    foreign: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether nothing was refused or left to do.

        Returns:
            ``True`` only when the destination matches the source.

        Examples:
            >>> Report().ok
            True
        """
        return not (self.drifted or self.foreign or self.missing or self.stale)


def destination(environ: Mapping[str, str] | None = None) -> Path:
    """Return where skills are installed for this user.

    Args:
        environ: An alternate environment mapping.

    Returns:
        The user's configured skills directory.

    Examples:
        >>> destination({"HOME": "/home/example"})
        PosixPath('/home/example/.claude/skills')
    """
    environment = os.environ if environ is None else environ
    base = environment.get("CLAUDE_CONFIG_DIR") or str(
        Path(environment["HOME"]) / ".claude"
    )
    return Path(base) / "skills"


def _sha(path: Path) -> str:
    """Return one file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(source: Path) -> list[str]:
    """List skill files, excluding top-level documentation."""
    return sorted(
        str(path.relative_to(source))
        for path in source.rglob("*")
        if path.is_file() and path.parent != source
    )


def _load(dest: Path) -> dict[str, str]:
    """Load the ownership manifest, or return an empty one."""
    path = dest / MANIFEST
    if not path.exists():
        return {}
    loaded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in loaded.items()
    ):
        raise ValueError(
            f"{path} is not a string-to-string manifest; repair or remove it."
        )
    return {str(key): str(value) for key, value in loaded.items()}


def _plan(rel: str, source: Path, dest: Path, manifest: dict[str, str]) -> str:
    """Name one file's state: same, new, update, drift, or foreign."""
    target = dest / rel
    if not target.exists():
        skill_dir = dest / Path(rel).parts[0]
        owned = any(
            key.startswith(f"{Path(rel).parts[0]}/") for key in manifest
        )
        return "foreign" if skill_dir.exists() and not owned else "new"
    current = _sha(target)
    if current == _sha(source / rel):
        return "same"
    if rel not in manifest:
        return "foreign"
    return "update" if current == manifest[rel] else "drift"


def run(mode: str, source: Path = SKILLS, dest: Path | None = None) -> Report:
    r"""Install, check, adopt, or force the skills into a destination.

    Args:
        mode: One of :data:`MODES`.
        source: The maintained skill tree.
        dest: The user's skills directory; :func:`destination` by default.

    Returns:
        What was written, adopted, pending, or refused.

    Raises:
        ValueError: If ``mode`` is unknown or the manifest is malformed.

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as temporary:
        ...     root = Path(temporary)
        ...     source = root / "source"
        ...     (source / "demo").mkdir(parents=True)
        ...     _ = (source / "demo" / "SKILL.md").write_text("demo\n")
        ...     run("install", source, root / "dest").ok
        True
    """
    if mode not in MODES:
        raise ValueError(
            f"Unknown install mode {mode!r}; choose one of {', '.join(MODES)}."
        )
    target_root = dest or destination()
    manifest = _load(target_root)
    report = Report()
    for rel in _sources(source):
        state = _plan(rel, source, target_root, manifest)
        target = target_root / rel
        if state == "same":
            manifest[rel] = _sha(target)
            continue
        if state == "foreign":
            report.foreign.append(rel)
            continue
        if state == "drift" and mode == "adopt":
            shutil.copyfile(target, source / rel)
            manifest[rel] = _sha(target)
            report.adopted.append(rel)
            continue
        if state == "drift" and mode != "force":
            report.drifted.append(rel)
            continue
        if mode in ("check", "adopt"):
            (report.missing if state == "new" else report.stale).append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target)
        manifest[rel] = _sha(target)
        report.written.append(rel)
    if mode != "check":
        target_root.mkdir(parents=True, exist_ok=True)
        (target_root / MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def _print(report: Report, dest: Path) -> None:
    """Print a skill installation report and corrective refusals."""
    for label, paths in (
        ("written", report.written),
        ("adopted into foundry", report.adopted),
        ("not installed", report.missing),
        ("out of date", report.stale),
        ("DRIFT: edited where installed", report.drifted),
        ("REFUSED: a skill foundry did not install", report.foreign),
    ):
        for path in paths:
            print(f"  {label}: {path}")
    if report.drifted:
        print(
            "Nothing drifted was overwritten. Compare the installed copy "
            f"with {dest}, then rerun with --adopt to keep the edits or "
            "--force to discard them.",
            file=sys.stderr,
        )
    if report.foreign:
        print(
            "A skill of the same name exists and foundry did not install it. "
            "Rename or remove it by hand; this command never touches it.",
            file=sys.stderr,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the skill installer.

    Args:
        argv: Arguments without the executable name.

    Returns:
        Zero on success, one when check finds drift or installation refuses.

    Examples:
        >>> callable(main)
        True
    """
    parser = argparse.ArgumentParser(
        description="Install research-foundry's maintained skills."
    )
    group = parser.add_mutually_exclusive_group()
    for mode in MODES[1:]:
        group.add_argument(f"--{mode}", action="store_true")
    args = parser.parse_args(argv)
    mode = next((item for item in MODES[1:] if getattr(args, item)), "install")
    dest = destination()
    report = run(mode, SKILLS, dest)
    print(f"skills -> {dest} ({mode})")
    _print(report, dest)
    if mode == "check":
        return 0 if report.ok else 1
    return 0 if not (report.drifted or report.foreign) else 1


__all__ = [
    "MANIFEST",
    "MODES",
    "Report",
    "SKILLS",
    "destination",
    "main",
    "run",
    "skills_root",
]
