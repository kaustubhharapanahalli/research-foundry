"""Generate a throwaway project, offline, from a local clone of foundry.

A setup test needs a real generated project without a network: this makes
one with ``cruft create`` from a local git repository, at a ref, into a
directory, from a named variant (:data:`tools.variants.VARIANTS`) or a
template and its answers::

    make throwaway VARIANT=software-everything
    uv run python -m tools.throwaway software frontend_nextjs=no --ref main

cruft reads the source's commits, not its working tree. ``--working-tree``
snapshots uncommitted changes into a repository inside ``--into`` first.
An answer the template does not ask at that ref is refused, because
cookiecutter would drop it without a word.

It prints the project's path. Nothing is installed or pushed, and nothing
outside ``--into`` is written; deleting that directory removes it all.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from cruft import create
from tools.variants import VARIANTS

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ("methodology", "workspace", "paper", "software")
#: The identity a snapshot commit is made under.
SNAPSHOT_GIT_ENV = {
    "GIT_AUTHOR_NAME": "throwaway",
    "GIT_AUTHOR_EMAIL": "throwaway@example.invalid",
    "GIT_COMMITTER_NAME": "throwaway",
    "GIT_COMMITTER_EMAIL": "throwaway@example.invalid",
}


def snapshot(root: Path, dest: Path, git_env: Mapping[str, str]) -> Path:
    """Copy ``root``'s working tree into a new git repository at ``dest``.

    Uncommitted changes are included, so a change can be tried before it is
    committed. Links are kept: each template's ``templates`` is one.
    """
    shutil.copytree(
        root,
        dest,
        symlinks=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "*_cache", "build", "__pycache__"
        ),
    )
    for argv in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "commit", "-qm", "snapshot"],
    ):
        subprocess.run(
            argv,
            cwd=dest,
            env={**os.environ, **git_env},
            check=True,
            capture_output=True,
        )
    return dest


def show(source: Path, ref: str, path: str) -> str:
    """Return ``path`` as it is at ``ref`` in the git repository ``source``."""
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=source,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def asked(source: Path, template: str, ref: str | None) -> set[str]:
    """Return the answers ``template`` asks at ``ref`` in ``source``."""
    spec = show(source, ref or "HEAD", f"{template}/cookiecutter.json")
    return {name for name in json.loads(spec) if not name.startswith("_")}


def generate(
    template: str,
    answers: Mapping[str, str],
    *,
    into: Path,
    source: Path = ROOT,
    ref: str | None = None,
) -> Path:
    """``cruft create`` one project from ``source`` at ``ref``, into ``into``.

    Args:
        template: one of :data:`TEMPLATES`.
        answers: the template's answers; the rest take their defaults.
        into: the directory the project is created in.
        source: a git repository holding foundry; a local clone works
            offline.
        ref: the branch, tag or commit; ``None`` is the source's HEAD.

    Returns:
        The generated project's directory.

    Raises:
        ValueError: ``template`` is not a foundry template, or an answer
            is not one the template asks at ``ref``.
    """
    if template not in TEMPLATES:
        raise ValueError(f"{template!r} is not one of {', '.join(TEMPLATES)}")
    unknown = sorted(set(answers) - asked(source, template, ref))
    if unknown:
        raise ValueError(
            f"{template} at {ref or 'HEAD'} does not ask"
            f" {', '.join(unknown)}; commit the change, or pass"
            " --working-tree"
        )
    into.mkdir(parents=True, exist_ok=True)
    return Path(
        create(
            str(source),
            output_dir=into,
            directory=template,
            checkout=ref,
            no_input=True,
            extra_context=dict(answers),
            default_config=True,
        )
    )


def _answers(pairs: Sequence[str]) -> dict[str, str]:
    out = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep or not name:
            raise SystemExit(f"answers are name=value, not {pair!r}")
        out[name] = value
    return out


def main(argv: Sequence[str] | None = None) -> int:
    """Generate one throwaway project and print its path."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "what", help="a variant name, or a template followed by name=value"
    )
    parser.add_argument(
        "answers", nargs="*", help="name=value, with a template"
    )
    parser.add_argument("--into", type=Path, help="default: a new temp dir")
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--ref", default=None)
    parser.add_argument(
        "--working-tree",
        action="store_true",
        help="generate from --source's uncommitted state, not its HEAD",
    )
    args = parser.parse_args(argv)
    if args.what not in VARIANTS and args.what not in TEMPLATES:
        parser.error(
            f"{args.what!r} is neither a variant"
            f" ({', '.join(sorted(VARIANTS))})"
            f" nor a template ({', '.join(TEMPLATES)})"
        )
    if args.what in VARIANTS and args.answers:
        parser.error("a named variant takes no answers")
    template, answers = VARIANTS.get(args.what) or (
        args.what,
        _answers(args.answers),
    )
    into = args.into or Path(tempfile.mkdtemp(prefix="foundry-throwaway-"))
    source = args.source
    if args.working_tree:
        source = snapshot(source, into / ".foundry", SNAPSHOT_GIT_ENV)
    try:
        made = generate(
            template, answers, into=into, source=source, ref=args.ref
        )
    except ValueError as error:
        parser.error(str(error))
    print(made)
    return 0


if __name__ == "__main__":
    sys.exit(main())
