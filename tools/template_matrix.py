"""Every template, with every combination of the answers that change its files.

``make template-matrix`` finds, for each template, the choice answers whose
values change which files a project gets, and takes every combination of
them. It does not keep a hand-written list, which would go stale as options
are added. A combination the template's own pre-generation hook refuses is
recorded as refused, with the hook's reason, and not run.

Every other combination is a throwaway project, put through four steps:

1. generate: ``cruft create`` from a snapshot of this working tree;
2. install: the project's ``make install``;
3. ci: the project's ``make ci``, or ``ci-container`` for a paper on a
   machine without TeX, after ``make venue`` for a venue kit;
4. update: a change to the shared base is committed to the snapshot, and
   ``cruft update`` must bring it into the project, after which
   ``make template-check`` passes.

Each project is deleted when its run ends, and so are its containers. The
step logs and a report (``report.md``, ``report.json``) stay in
``build/template-matrix/``. The run exits non-zero if any step failed.

``--list`` only prints the combinations; ``--templates`` narrows the run.
"""

from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from cookiecutter.exceptions import FailedHookException
from cookiecutter.main import cookiecutter
from tools.throwaway import ROOT, TEMPLATES, generate, snapshot

__all__ = [
    "ROOT",
    "Result",
    "Variant",
    "ci_steps",
    "hook_reason",
    "main",
    "prepare_source",
    "render",
    "report",
    "run_variant",
    "tree_options",
    "variants",
]

GIT_ENV = {
    "GIT_AUTHOR_NAME": "foundry-matrix",
    "GIT_AUTHOR_EMAIL": "foundry-matrix@example.org",
    "GIT_COMMITTER_NAME": "foundry-matrix",
    "GIT_COMMITTER_EMAIL": "foundry-matrix@example.org",
}
#: Answers every combination carries, so options that need them can be
#: tried: public documentation refuses to render without a contact.
BASE_ANSWERS: dict[str, dict[str, str]] = {
    "methodology": {"contact_email": "maintainers@example.org"},
}
#: The shared change the update step must carry into each project.
SHARED_FILE = Path("_shared") / "base" / "editorconfig"
SHARED_MARK = "[*.template-matrix]"
OUT = ROOT / "build" / "template-matrix"

Runner = Callable[[Sequence[str], Path], "subprocess.CompletedProcess[str]"]
Generate = Callable[..., Path]


@dataclass(frozen=True)
class Variant:
    """One template and the answers that make one combination."""

    template: str
    answers: tuple[tuple[str, str], ...]

    @property
    def name(self) -> str:
        """The template, then each answer, in the order the options come."""
        return "-".join(
            [self.template, *(f"{k}={v}" for k, v in self.answers)]
        )


@dataclass
class Result:
    """What one variant's run did: each step's outcome, and the first fault."""

    variant: str
    steps: dict[str, str] = field(default_factory=dict)
    failure: str | None = None
    seconds: float = 0.0

    @property
    def passed(self) -> bool:
        """True when every step ran and passed."""
        return self.failure is None


def choice_options(source: Path, template: str) -> dict[str, list[str]]:
    """The template's choice answers and their values, in file order."""
    spec = json.loads((source / template / "cookiecutter.json").read_text())
    return {
        name: [str(v) for v in value]
        for name, value in spec.items()
        if not name.startswith("_") and isinstance(value, list)
    }


@contextlib.contextmanager
def _stderr_to(path: Path) -> Iterator[None]:
    """Send this process's stderr, and its children's, to ``path``.

    A hook runs as a child process and writes its reason to the inherited
    stderr, so only a file-descriptor redirect catches it.
    """
    sys.stderr.flush()
    saved = os.dup(2)
    with path.open("w") as sink:
        os.dup2(sink.fileno(), 2)
        try:
            yield
        finally:
            sys.stderr.flush()
            os.dup2(saved, 2)
            os.close(saved)


def hook_reason(text: str) -> str:
    """The hook's own words: every line before cookiecutter's "Stopping"."""
    said = []
    for line in text.splitlines():
        if line.startswith("Stopping generation"):
            break
        if line.strip():
            said.append(line.strip())
    return " ".join(said) or "refused by a generation hook"


def render(
    source: Path, template: str, answers: Mapping[str, str], into: Path
) -> frozenset[str] | str:
    """The files one combination makes, or the hook's reason for refusal."""
    out = Path(tempfile.mkdtemp(dir=into))
    captured = out / "stderr.txt"
    try:
        with _stderr_to(captured):
            project = cookiecutter(
                str(source),
                directory=template,
                no_input=True,
                output_dir=str(out / "project"),
                extra_context={**BASE_ANSWERS.get(template, {}), **answers},
            )
    except FailedHookException:
        reason = hook_reason(captured.read_text())
        shutil.rmtree(out)
        return reason
    root = Path(project)
    files = frozenset(
        str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
    )
    shutil.rmtree(out)
    return files


def tree_options(
    source: Path, template: str, into: Path
) -> dict[str, list[str]]:
    """Each option whose values change the files, with one value per tree.

    A value is kept when it gives a file set no earlier value gave, or when
    the hook refuses it with the other answers at their defaults: it may
    render in another combination, so the product tries it.
    """
    out: dict[str, list[str]] = {}
    for name, values in choice_options(source, template).items():
        seen: set[frozenset[str]] = set()
        kept: list[str] = []
        for value in values:
            files = render(source, template, {name: value}, into)
            if isinstance(files, str):
                kept.append(value)
            elif files not in seen:
                seen.add(files)
                kept.append(value)
        if len(kept) > 1:
            out[name] = kept
    return out


def variants(
    source: Path, template: str, into: Path
) -> tuple[list[Variant], list[tuple[Variant, str]]]:
    """Every combination of the tree-changing options: to run, and refused."""
    options = tree_options(source, template, into)
    names = list(options)
    runnable: list[Variant] = []
    refused: list[tuple[Variant, str]] = []
    for values in itertools.product(*(options[n] for n in names)):
        variant = Variant(template, tuple(zip(names, values, strict=True)))
        files = render(source, template, dict(variant.answers), into)
        if isinstance(files, str):
            refused.append((variant, files))
        else:
            runnable.append(variant)
    return runnable, refused


def _run(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_ENV}
    # A project uses its own environment, never foundry's.
    env.pop("VIRTUAL_ENV", None)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def prepare_source(work: Path) -> Path:
    """Snapshot this tree as ``matrix-base``; commit a shared change on top."""
    source = snapshot(ROOT, work / "foundry", GIT_ENV)
    _run(["git", "tag", "matrix-base"], source)
    shared = source / SHARED_FILE
    shared.write_text(
        shared.read_text() + f"\n{SHARED_MARK}\nindent_size = 2\n"
    )
    _run(["git", "commit", "-qam", "a shared change"], source)
    return source


#: Steps whose output a project commits, and the commit message.
COMMITTED_AFTER = {"install": "the first lock", "venue": "the venue kit"}


def ci_steps(variant: Variant) -> list[tuple[str, list[str]]]:
    """Install, the venue kit for a paper that needs one, then the CI."""
    answers = dict(variant.answers)
    steps: list[tuple[str, list[str]]] = [("install", ["make", "install"])]
    if variant.template == "paper":
        if answers.get("venue", "iclr") != "article":
            steps.append(("venue", ["make", "venue"]))
        target = "ci" if shutil.which("latexmk") else "ci-container"
        steps.append(("ci", ["make", target]))
    else:
        steps.append(("ci", ["make", "ci"]))
    return steps


def _cleanup(project: Path, run: Runner) -> None:
    if (project / "compose.yaml").exists():
        run(
            [
                "docker", "compose", "--profile", "app", "--profile",
                "gateway", "down", "--volumes", "--remove-orphans",
            ],
            project,
        )  # fmt: skip
    shutil.rmtree(project.parent, ignore_errors=True)


def _steps(
    variant: Variant, project: Path, logs: Path, run: Runner, result: Result
) -> None:
    """Install, CI, update and template-check, stopping at the first fault."""
    steps = [
        *ci_steps(variant),
        (
            "update",
            ["uvx", "--from", "cruft==2.16.0", "cruft", "update",
             "--skip-apply-ask", "--checkout", "main"],
        ),
        ("template-check", ["make", "template-check"]),
    ]  # fmt: skip
    for step, argv in steps:
        done = run(argv, project)
        (logs / f"{variant.name}.{step}.log").write_text(
            (done.stdout or "") + (done.stderr or "")
        )
        if done.returncode != 0:
            result.steps[step] = "failed"
            result.failure = f"{step}: exit {done.returncode}"
            return
        editorconfig = (project / ".editorconfig").read_text()
        if step == "update" and SHARED_MARK not in editorconfig:
            result.steps[step] = "failed"
            result.failure = "update: the shared change did not arrive"
            return
        if step in COMMITTED_AFTER:
            # The first install writes the lock file, and `make venue` the
            # kit Overleaf needs; the project commits both.
            run(["git", "add", "-A"], project)
            run(["git", "commit", "-qm", COMMITTED_AFTER[step]], project)
        if step == "ci":
            # cruft updates only a clean tree, and so does a person: what CI
            # leaves behind is a file the project's .gitignore misses.
            left = run(["git", "status", "--porcelain"], project).stdout
            if left.strip():
                result.steps[step] = "failed"
                result.failure = "ci: left files git does not ignore: " + (
                    ", ".join(line[3:] for line in left.splitlines())
                )
                return
        result.steps[step] = "passed"


def run_variant(  # pylint: disable=too-many-arguments
    variant: Variant,
    source: Path,
    work: Path,
    logs: Path,
    *,
    run: Runner = _run,
    make: Generate = generate,
) -> Result:
    """Generate one variant, run its CI, update it, and delete it."""
    result = Result(variant.name)
    started = time.monotonic()
    into = Path(tempfile.mkdtemp(prefix="variant-", dir=work))
    project = into / "unmade"
    try:
        answers = {**BASE_ANSWERS.get(variant.template, {})}
        answers.update(variant.answers)
        project = make(
            variant.template,
            answers,
            into=into,
            source=source,
            ref="matrix-base",
        )
        result.steps["generate"] = "passed"
        for argv in (
            ["git", "init", "-q"],
            ["git", "add", "-A"],
            ["git", "commit", "-qm", "generated"],
        ):
            run(argv, project)
        _steps(variant, project, logs, run, result)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        result.steps.setdefault("generate", "failed")
        result.failure = result.failure or f"{type(exc).__name__}: {exc}"
    finally:
        _cleanup(project, run)
        result.seconds = round(time.monotonic() - started, 1)
    return result


def report(
    results: Iterable[Result], refused: Iterable[tuple[Variant, str]]
) -> str:
    """The run as a Markdown table, refused combinations listed after it."""
    lines = [
        "| Variant | Steps | Result | Seconds |",
        "| ------- | ----- | ------ | ------- |",
    ]
    for result in results:
        steps = ", ".join(f"{k} {v}" for k, v in result.steps.items())
        verdict = "passed" if result.passed else f"FAILED ({result.failure})"
        lines.append(
            f"| `{result.variant}` | {steps} | {verdict} | {result.seconds} |"
        )
    refused = list(refused)
    if refused:
        lines += ["", "Refused by the template's own hook, not run:", ""]
        lines += [f"- `{v.name}`: {reason}" for v, reason in refused]
    return "\n".join(lines) + "\n"


Found = Mapping[str, tuple[list[Variant], list[tuple[Variant, str]]]]


def where(found: Found, pairs: Sequence[str]) -> Found:
    """Keep the variants, runnable or refused, that answer every pair.

    Raises:
        ValueError: A pair is not ``name=value``, or no runnable variant
            answers it.
    """
    wanted = set()
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep or not name:
            raise ValueError(f"--where takes name=value, not {pair!r}")
        wanted.add((name, value))
    kept = {
        template: (
            [v for v in runnable if wanted <= set(v.answers)],
            [(v, r) for v, r in refused if wanted <= set(v.answers)],
        )
        for template, (runnable, refused) in found.items()
    }
    if not any(runnable for runnable, _ in kept.values()):
        raise ValueError(f"no variant answers {', '.join(sorted(pairs))}")
    return kept


def run_all(found: Found, work: Path, out: Path = OUT) -> int:
    """Run every runnable variant, write the report, and return the status."""
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    source = prepare_source(work)
    results: list[Result] = []
    refused: list[tuple[Variant, str]] = []
    for runnable, refusals in found.values():
        refused += refusals
        for variant in runnable:
            result = run_variant(variant, source, work, logs)
            verdict = "passed" if result.passed else "FAILED"
            print(f"{verdict}  {variant.name}  {result.seconds}s", flush=True)
            results.append(result)
    text = report(results, refused)
    (out / "report.md").write_text(text)
    (out / "report.json").write_text(
        json.dumps([r.__dict__ for r in results], indent=2) + "\n"
    )
    print(text)
    return 0 if all(r.passed for r in results) else 1


def main(argv: Sequence[str] | None = None) -> int:
    """List or run the matrix; exit 1 if any variant failed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--templates", default=",".join(TEMPLATES))
    parser.add_argument("--list", action="store_true")
    parser.add_argument(
        "--where",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="only the variants with this answer; repeatable",
    )
    parser.add_argument(
        "--out", type=Path, default=OUT, help="where the report goes"
    )
    args = parser.parse_args(argv)
    chosen = [t for t in args.templates.split(",") if t]
    unknown = sorted(set(chosen) - set(TEMPLATES))
    if unknown:
        parser.error(f"no template {', '.join(unknown)}")
    with tempfile.TemporaryDirectory(prefix="foundry-matrix-") as tmp:
        work = Path(tmp)
        found: Found = {t: variants(ROOT, t, work) for t in chosen}
        if args.where:
            try:
                found = where(found, args.where)
            except ValueError as error:
                parser.error(str(error))
        if not args.list:
            return run_all(found, work, args.out)
        for runnable, refused in found.values():
            for variant in runnable:
                print(variant.name)
            for variant, reason in refused:
                print(f"{variant.name}  (refused: {reason})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
