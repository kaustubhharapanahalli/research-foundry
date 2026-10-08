"""Each generated project passes its own `make ci`.

These install real dependencies, PyTorch included, so they are marked
`heavy`: `make test-heavy` and the nightly workflow run them, `make ci`
does not. The variants are `tools.variants.VARIANTS`, which
`make throwaway` generates from too.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter
from tests.conftest import GIT_ENV, ROOT
from tools.variants import VARIANTS


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_ENV}
    # The generated project must use its own environment, not foundry's.
    env.pop("VIRTUAL_ENV", None)
    return subprocess.run(
        args, cwd=cwd, env=env, capture_output=True, text=True, check=False
    )


def _ci_target(kind: str) -> str:
    # A paper builds with this machine's TeX when there is one, and in the
    # pinned TeX Live image otherwise, as a paper's own CI does.
    if kind == "paper" and not shutil.which("latexmk"):
        return "ci-container"
    return "ci"


def _compose_down(project: Path) -> None:
    # A software project's Postgres and its volume go with the test.
    if (project / "compose.yaml").exists():
        # --profile app: a container left from its services would keep a
        # dead network and break the next project's stack.
        _run(
            ["docker", "compose", "--profile", "app", "down", "--volumes"],
            project,
        )


def _generate(kind: str, answers: dict[str, str], tmp_path: Path) -> Path:
    project = Path(
        cookiecutter(
            str(ROOT),
            directory=kind,
            no_input=True,
            output_dir=str(tmp_path),
            extra_context=answers,
        )
    )
    steps = [["git", "init", "-q"], ["make", "install"]]
    if answers.get("venue", "article") != "article":
        steps.append(["make", "venue"])
    for step in steps:
        done = _run(step, project)
        assert done.returncode == 0, done.stdout + done.stderr
    _run(["git", "add", "-A"], project)
    return project


@pytest.mark.heavy
@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_generated_project_passes_its_own_ci(
    variant: str, tmp_path: Path
) -> None:
    kind, answers = VARIANTS[variant]
    project = _generate(kind, answers, tmp_path)
    try:
        done = _run(["make", _ci_target(kind)], project)
    finally:
        _compose_down(project)
    assert done.returncode == 0, done.stdout[-4000:] + done.stderr[-2000:]
    # A formatter that changed anything means the template is not clean.
    diff = _run(["git", "diff", "--stat"], project).stdout
    assert diff == "", f"make ci rewrote files:\n{diff}"
    # A passing project is not needed again, and every PyTorch environment
    # kept until the session ends filled a CI runner's disk.
    shutil.rmtree(project)


@pytest.mark.heavy
def test_methodology_plain_docs_builds_with_mkdocs(
    tmp_path: Path,
) -> None:
    """Build generated docs and check Shape/math rendering and snippet
    refusal.
    """
    kind, answers = VARIANTS["methodology-plain-docs"]
    project = _generate(kind, answers, tmp_path)
    module = project / "src" / "my_project" / "shape_example.py"
    module.write_text(
        '"""Show math and shape metadata in the generated API.\n\n'
        "Shape:\n"
        "    input (*, H_in); output (*, H_out)\n\n"
        "The relation is $y = xA^T + b$.\n"
        '"""\n',
        encoding="utf-8",
    )
    api = project / "docs" / "api" / "index.md"
    api.write_text(
        api.read_text(encoding="utf-8") + "\n\n::: my_project.shape_example\n",
        encoding="utf-8",
    )
    done = _run(["make", "docs"], project)
    assert done.returncode == 0, done.stdout[-4000:] + done.stderr[-2000:]
    assert (project / "site" / "index.html").is_file()
    api_html = (project / "site" / "api" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<details class="shape" open>' in api_html
    assert "<summary>Shape</summary>" in api_html
    assert 'class="arithmatex' in api_html

    guide = project / "docs" / "how-to" / "check-the-install.md"
    guide.write_text(
        guide.read_text(encoding="utf-8").replace(
            '"check_install.py"', '"missing.py"'
        ),
        encoding="utf-8",
    )
    refused = _run(["make", "docs"], project)
    assert refused.returncode != 0
    assert "missing.py" in refused.stdout + refused.stderr


@pytest.mark.heavy
@pytest.mark.parametrize(
    ("line", "reason"),
    [
        (r"See Section~\ref{sec:nowhere}.", "sec:nowhere"),
        (r"As shown by \citet{nobody2026}.", "nobody2026"),
        (r"\noindent\mbox{" + "Unbreakable" * 12 + "}", "Overfull"),
    ],
    ids=["undefined-reference", "undefined-citation", "overfull-line"],
)
def test_paper_check_refuses(line: str, reason: str, tmp_path: Path) -> None:
    project = _generate("paper", {"venue": "article"}, tmp_path)
    target = "check" if shutil.which("latexmk") else "check-container"
    # The clean paper passes first, so a failure below is the guard's and
    # not the machine's (a full disk once made these pass for nothing).
    clean = _run(["make", target], project)
    assert clean.returncode == 0, clean.stdout[-2000:] + clean.stderr[-2000:]
    method = project / "sections" / "method.tex"
    method.write_text(method.read_text() + line + "\n", encoding="utf-8")
    done = _run(["make", target], project)
    assert done.returncode != 0
    assert reason in done.stdout + done.stderr


@pytest.mark.heavy
@pytest.mark.parametrize("venue", ["article", "iclr"])
def test_paper_arxiv_copy_builds_on_its_own(
    venue: str, tmp_path: Path
) -> None:
    project = _generate(
        "paper", {"venue": venue, "venue_year": "2027"}, tmp_path
    )
    export = "arxiv" if shutil.which("latexmk") else "arxiv-container"
    for target in (export, "arxiv-verify"):
        done = _run(["make", target], project)
        assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-2000:]
    if venue == "article":
        return
    # The copy compiled above; without its kit it must not, or the check
    # would pass a folder arXiv cannot build.
    (project / "build" / "arxiv" / "iclr2027_conference.sty").unlink()
    done = _run(["make", "arxiv-verify"], project)
    assert done.returncode != 0
    assert "iclr2027_conference.sty" in done.stdout + done.stderr


@pytest.mark.heavy
def test_paper_icml_kit_builds_and_arxiv_carries_it(
    tmp_path: Path,
) -> None:
    kind, answers = VARIANTS["paper-icml"]
    project = _generate(kind, answers, tmp_path)
    for target in ("pdf", "check", "arxiv"):
        done = _run(["make", target], project)
        assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-2000:]
    assert (project / "build" / "arxiv" / "icml2026.sty").is_file()


@pytest.mark.heavy
def test_software_lint_refuses(tmp_path: Path) -> None:
    project = _generate("software", {"frontend_nextjs": "no"}, tmp_path)
    backend = project / "backend"
    breaks = [
        (
            "migrations-check",
            backend / "apps" / "notes" / "models.py",
            "    title = models.CharField(max_length=200)\n",
            "    title = models.CharField(max_length=200)\n"
            "    pinned = models.BooleanField(default=False)\n",
            "Add field pinned",
        ),
        (
            "deploy-check",
            backend / "config" / "settings" / "prod.py",
            "SECURE_HSTS_SECONDS = 31_536_000",
            "SECURE_HSTS_SECONDS = 0",
            "security.W004",
        ),
        (
            "schema",
            backend / "apps" / "notes" / "views.py",
            '        if getattr(self, "swagger_fake_view", False):',
            "        if False:  # pylint: disable=using-constant-test",
            "could not derive type of path parameter",
        ),
    ]
    try:
        for target, path, old, new, reason in breaks:
            # Clean first, so the failure below is the guard's.
            clean = _run(["make", target], project)
            assert clean.returncode == 0, clean.stdout + clean.stderr
            text = path.read_text()
            assert old in text, (target, old)
            path.write_text(text.replace(old, new))
            done = _run(["make", target], project)
            path.write_text(text)
            assert done.returncode != 0, target
            assert reason in done.stdout + done.stderr, target
    finally:
        _compose_down(project)


@pytest.mark.heavy
def test_software_frontend_guards_refuse(tmp_path: Path) -> None:
    project = _generate("software", {"frontend_nextjs": "yes"}, tmp_path)
    status = project / "frontend" / "features" / "status"
    # The clean project passes both in its own make ci (the variants above).
    breaks = [
        (
            "lint",
            status / "model" / "parent.ts",
            'export { describe } from "../model/describe";\n',
            "Use @/",
        ),
        (
            "lint",
            status / "model" / "fallback.ts",
            'const fallback = "down";\nexport default fallback;\n',
            "import/no-default-export",
        ),
        (
            "typecheck",
            status / "model" / "wrong.ts",
            'export const count: number = "three";\n',
            "TS2322",
        ),
    ]
    for script, path, text, reason in breaks:
        path.write_text(text)
        done = _run(["pnpm", "--dir", "frontend", "run", script], project)
        path.unlink()
        assert done.returncode != 0, script
        assert reason in done.stdout + done.stderr, script
    # Code no test reaches pulls the merged coverage under the floor.
    untested = status / "model" / "untested.ts"
    untested.write_text(
        "".join(
            f"export function branch{i}(flag: boolean): number {{\n"
            f"  return flag ? {i} : -{i};\n}}\n"
            for i in range(40)
        )
    )
    try:
        done = _run(["make", "frontend-coverage"], project)
    finally:
        _compose_down(project)
    assert done.returncode != 0
    assert "Frontend coverage below 90%" in done.stdout + done.stderr
