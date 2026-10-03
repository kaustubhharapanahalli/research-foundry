"""Install foundry's skills for one user, refusing to overwrite an edited copy.

Skills live here rather than in generated projects, so one maintained copy
can be installed for each person::

    make install-skills            # install or update
    make install-skills ARGS=--check

The destination is ``$CLAUDE_CONFIG_DIR/skills``, or ``~/.claude/skills``.

The installed copies are what the tools read, so they are what gets edited
when something is wrong, and the next install would overwrite the fix with
no trace. A manifest, ``.foundry-skills.json`` in the destination, records
the hash of every file this tool wrote:

* an installed file that still matches the manifest is foundry's copy, and is
  updated when the source changes;
* one that differs from both the manifest and the source was edited there:
  that is drift, and it is refused unless ``--adopt`` copies it back into
  this repository or ``--force`` discards it;
* a skill directory this tool never installed, such as a person's own skill
  of the same name, is never touched.
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

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
MANIFEST = ".foundry-skills.json"
MODES = ("install", "check", "adopt", "force")


@dataclass
class Report:
    """What one run did or would do, file by file."""

    written: list[str] = field(default_factory=list)
    adopted: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    drifted: list[str] = field(default_factory=list)
    foreign: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether nothing was refused or left to do."""
        return not (self.drifted or self.foreign or self.missing or self.stale)


def destination(environ: Mapping[str, str] | None = None) -> Path:
    """Return where skills are installed for this user."""
    env = os.environ if environ is None else environ
    base = env.get("CLAUDE_CONFIG_DIR") or str(Path(env["HOME"]) / ".claude")
    return Path(base) / "skills"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(source: Path) -> list[str]:
    return sorted(
        str(p.relative_to(source))
        for p in source.rglob("*")
        if p.is_file() and p.parent != source
    )


def _load(dest: Path) -> dict[str, str]:
    path = dest / MANIFEST
    if not path.exists():
        return {}
    loaded: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _plan(rel: str, source: Path, dest: Path, manifest: dict[str, str]) -> str:
    """Name what one file needs: same, new, update, drift or foreign."""
    target = dest / rel
    if not target.exists():
        skill_dir = dest / Path(rel).parts[0]
        owned = any(k.startswith(f"{Path(rel).parts[0]}/") for k in manifest)
        return "foreign" if skill_dir.exists() and not owned else "new"
    current = _sha(target)
    if current == _sha(source / rel):
        return "same"
    if rel not in manifest:
        return "foreign"
    return "update" if current == manifest[rel] else "drift"


def run(mode: str, source: Path = SKILLS, dest: Path | None = None) -> Report:
    """Install, check, adopt or force the skills in ``source`` into ``dest``.

    Args:
        mode: One of :data:`MODES`.
        source: This repository's ``skills/``.
        dest: The user's skills directory; :func:`destination` by default.

    Returns:
        What was written, adopted, or refused.
    """
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} is not one of {', '.join(MODES)}")
    dest = dest or destination()
    manifest = _load(dest)
    report = Report()
    for rel in _sources(source):
        state = _plan(rel, source, dest, manifest)
        target = dest / rel
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
        dest.mkdir(parents=True, exist_ok=True)
        (dest / MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def _print(report: Report, dest: Path) -> None:
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
            f"\nNothing drifted was overwritten. Compare with diff against"
            f" {dest}, then rerun with --adopt to keep the edits or --force"
            " to discard them.",
            file=sys.stderr,
        )
    if report.foreign:
        print(
            "\nA skill of the same name exists and foundry did not install"
            " it. Rename or remove it by hand; this tool never touches it.",
            file=sys.stderr,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Install the skills; exit 1 if anything was refused or is out of date."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    for mode in MODES[1:]:
        group.add_argument(f"--{mode}", action="store_true")
    args = parser.parse_args(argv)
    mode = next((m for m in MODES[1:] if getattr(args, m)), "install")
    dest = destination()
    report = run(mode, SKILLS, dest)
    print(f"skills -> {dest} ({mode})")
    _print(report, dest)
    if mode == "check":
        return 0 if report.ok else 1
    return 0 if not (report.drifted or report.foreign) else 1


if __name__ == "__main__":
    sys.exit(main())
