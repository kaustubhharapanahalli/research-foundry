"""Publish this repository's public export as one release commit.

A public-facing project is two repositories: this private one, with every
branch and the agent files, and a public one that receives only a curated
export. GitHub sets visibility per repository, not per branch, so the split
is the only way to keep the agent files tracked here and out of public view.

Usage::

    python scripts/publish.py check
    python scripts/publish.py push REMOTE [--branch main] [--message TEXT]

``check`` builds the export from ``HEAD`` and scans it; nothing is pushed.
``push`` does the same, then commits the export on top of the public
branch's tip and pushes that one commit. The private history never travels:
the release commit's only parent is the previous release.

The export is ``git archive HEAD`` without the agent files
(:data:`AGENT_FILES`). It is refused while the working tree has changes, and
when any line matches a private-item rule: the built-in ones
(:data:`BUILT_IN_RULES`) or a pattern in ``.publish-deny``, the project's own
list of hostnames, account groups, organisation names, board numbers,
advisor names and unpublished titles. A refusal names the file, the line and
the rule, never the matched text.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

#: Never published: agent instructions, their state, and the deny list.
AGENT_FILES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        ".agent-state",
        ".work",
        ".claude",
        "journal.md",
        ".publish-deny",
    }
)

#: Private items any project can have, by name.
BUILT_IN_RULES: dict[str, str] = {
    "Overleaf project ID": (
        r"overleaf\.com/(?:project|read)/[0-9a-f]{24}"
        r"|git\.overleaf\.com/[0-9a-f]{24}"
    ),
    "home path": r"/(?:Users|home)/(?!runner/)[A-Za-z][\w.-]*/",
}

#: The project's own patterns, one regular expression per line.
DENY_FILE = ".publish-deny"


class PublishError(Exception):
    """The export cannot be published; nothing was pushed."""


@dataclass(frozen=True)
class Finding:
    """One line of the export that matches a private-item rule."""

    path: str
    line: int
    rule: str

    def __str__(self) -> str:
        """Return ``path:line: rule``, without the matched text."""
        return f"{self.path}:{self.line}: {self.rule}"


def _git(root: Path, *argv: str, data: bytes | None = None) -> bytes:
    done = subprocess.run(
        ["git", *argv], cwd=root, input=data, capture_output=True, check=False
    )
    if done.returncode != 0:
        raise PublishError(
            f"git {' '.join(argv)}: {done.stderr.decode().strip()}"
        )
    return done.stdout


def is_agent_file(path: str) -> bool:
    """Return whether ``path`` is, or sits under, an agent file."""
    return any(part in AGENT_FILES for part in Path(path).parts)


def rules(root: Path) -> dict[str, re.Pattern[str]]:
    """Return the built-in rules and the project's ``.publish-deny`` lines.

    Raises:
        PublishError: If a line in ``.publish-deny`` is not a valid regular
            expression.
    """
    found = {name: re.compile(p) for name, p in BUILT_IN_RULES.items()}
    deny = root / DENY_FILE
    if not deny.exists():
        return found
    lines = deny.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        pattern = line.strip()
        if not pattern or pattern.startswith("#"):
            continue
        try:
            found[f"{DENY_FILE} line {number}"] = re.compile(
                pattern, re.IGNORECASE
            )
        except re.error as error:
            raise PublishError(
                f"{DENY_FILE} line {number} is not a regular expression:"
                f" {error}"
            ) from None
    return found


def export(root: Path, dest: Path) -> list[str]:
    """Write ``HEAD`` without the agent files into ``dest``.

    Returns:
        The exported paths, sorted.

    Raises:
        PublishError: If the working tree has uncommitted changes, which
            would not be in the export.
    """
    if _git(root, "status", "--porcelain").strip():
        raise PublishError(
            "the working tree has changes; commit them first, since the"
            " export is HEAD"
        )
    archive = _git(root, "archive", "--format=tar", "HEAD")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = [m for m in tar.getmembers() if not is_agent_file(m.name)]
        tar.extractall(dest, members=members, filter="data")
    return sorted(m.name for m in members if not m.isdir())


def scan(
    dest: Path, paths: Iterable[str], found_rules: dict[str, re.Pattern[str]]
) -> Iterator[Finding]:
    """Yield every line of ``paths`` under ``dest`` that matches a rule."""
    for path in paths:
        target = dest / path
        if target.is_symlink() or not target.is_file():
            continue
        text = target.read_bytes().decode("utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in found_rules.items():
                if pattern.search(line):
                    yield Finding(path, number, name)


def build(root: Path, dest: Path) -> list[str]:
    """Export ``root`` into ``dest`` and refuse it if anything is private.

    Returns:
        The exported paths.

    Raises:
        PublishError: If the tree is dirty or a line matches a rule.
    """
    paths = export(root, dest)
    findings = list(scan(dest, paths, rules(root)))
    if findings:
        listed = "\n".join(f"  {f}" for f in findings)
        raise PublishError(
            f"the export holds {len(findings)} private item(s):\n{listed}"
        )
    return paths


def _remote_url(root: Path, remote: str) -> str:
    names = _git(root, "remote").decode().split()
    if remote in names:
        return _git(root, "remote", "get-url", remote).decode().strip()
    return remote


def push(root: Path, remote: str, branch: str, message: str) -> str:
    """Commit the export on the public branch's tip and push it.

    Returns:
        The new release commit's hash.

    Raises:
        PublishError: If the export is refused, nothing changed since the
            last release, or git fails.
    """
    url = _remote_url(root, remote)
    with tempfile.TemporaryDirectory(prefix="publish-") as tmp:
        work = Path(tmp)
        build(root, work)
        _git(work, "init", "-q", "-b", branch)
        _git(work, "add", "-A")
        tree = _git(work, "write-tree").decode().strip()
        parents: list[str] = []
        heads = _git(work, "ls-remote", "--heads", url, branch).decode()
        if heads.strip():
            _git(work, "fetch", "-q", url, branch)
            tip = _git(work, "rev-parse", "FETCH_HEAD").decode().strip()
            parent_tree = _git(work, "rev-parse", tip + "^" + "{tree}")
            if parent_tree.decode().strip() == tree:
                raise PublishError(
                    f"nothing to publish: {branch} already holds this export"
                )
            parents = ["-p", tip]
        commit = (
            _git(work, "commit-tree", tree, *parents, "-m", message)
            .decode()
            .strip()
        )
        _git(work, "push", "-q", url, f"{commit}:refs/heads/{branch}")
        shutil.rmtree(work / ".git", ignore_errors=True)
    return commit


def _version(root: Path) -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "unversioned"


def main(argv: Sequence[str] | None = None, root: Path | None = None) -> int:
    """Check or push the public export; exit 1 with the reason if refused."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="build and scan the export; push nothing")
    pusher = sub.add_parser("push", help="push the export as one commit")
    pusher.add_argument("remote", help="a remote name or URL")
    pusher.add_argument("--branch", default="main")
    pusher.add_argument("--message", default=None)
    args = parser.parse_args(argv)
    here = root or Path.cwd()
    try:
        if args.command == "check":
            with tempfile.TemporaryDirectory(prefix="publish-") as tmp:
                paths = build(here, Path(tmp))
            print(
                f"publish: {len(paths)} files, no agent files, nothing private"
            )
            return 0
        message = args.message or f"Release {_version(here)}"
        commit = push(here, args.remote, args.branch, message)
        print(f"publish: {commit[:12]} pushed to {args.branch}")
        return 0
    except PublishError as error:
        print(f"publish refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
