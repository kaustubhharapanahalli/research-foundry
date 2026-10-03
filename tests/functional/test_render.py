"""Every template renders cleanly, the same way every time."""

import filecmp
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter
from jinja2.exceptions import TemplateNotFound
from tests.conftest import LEFTOVER, ROOT, SHARED, template_kinds

Render = Callable[..., Path]


def _files(project: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(project)): p.read_bytes()
        for p in sorted(project.rglob("*"))
        if p.is_file()
    }


@pytest.mark.parametrize("kind", template_kinds())
def test_renders_with_defaults(kind: str, render: Render) -> None:
    project = render(kind)
    assert project.is_dir()
    assert _files(project), "nothing was generated"


@pytest.mark.parametrize("kind", template_kinds())
def test_no_template_syntax_left_behind(kind: str, render: Render) -> None:
    for name, data in _files(render(kind)).items():
        assert not LEFTOVER.search(data.decode()), name


# Each template's defaults, plus answers that switch whole file sets on.
VARIANTS: list[tuple[str, dict[str, str]]] = [
    (kind, {}) for kind in template_kinds()
] + [
    (
        "methodology",
        {"public_docs": "yes", "contact_email": "maintainers@example.org"},
    ),
    (
        "methodology",
        {
            "public_docs": "yes",
            "docs_theme": "custom",
            "contact_email": "maintainers@example.org",
        },
    ),
    ("methodology", {"ml_pytorch": "no"}),
    ("methodology", {"dataset_registry": "yes"}),
    ("software", {"frontend_nextjs": "no"}),
    ("software", {"proxy_caddy": "no"}),
    ("software", {"gateway_litellm": "yes"}),
    ("software", {"ml_pytorch": "yes"}),
]


@pytest.mark.parametrize(
    ("kind", "answers"),
    VARIANTS,
    ids=[
        f"{kind}-{'-'.join(answers) or 'defaults'}"
        for kind, answers in VARIANTS
    ],
)
def test_every_file_ends_with_one_newline(
    kind: str, answers: dict[str, str], render: Render
) -> None:
    # end-of-file-fixer rewrites anything else, failing the project's lint;
    # a stray Jinja newline otherwise shows up only in the nightly run.
    for name, data in _files(render(kind, **answers)).items():
        if data:
            assert data.endswith(b"\n"), name
            assert not data.endswith(b"\n\n"), name


@pytest.mark.parametrize("kind", template_kinds())
def test_rendering_is_deterministic(
    kind: str, render: Render, tmp_path: Path
) -> None:
    first = _files(render(kind, out=tmp_path / "a"))
    second = _files(render(kind, out=tmp_path / "b"))
    assert first == second


@pytest.mark.parametrize("kind", template_kinds())
def test_shared_editorconfig_arrives_unchanged(
    kind: str, render: Render
) -> None:
    rendered = render(kind) / ".editorconfig"
    assert filecmp.cmp(
        rendered, SHARED / "base" / "editorconfig", shallow=False
    )


def test_repo_names_follow_the_project(render: Render, tmp_path: Path) -> None:
    names = {
        kind: render(kind, out=tmp_path / kind, project_name="Tidal Flow").name
        for kind in ("methodology", "workspace", "paper")
    }
    assert names == {
        "methodology": "tidal-flow",
        "workspace": "tidal-flow-workspace",
        "paper": "tidal-flow-paper",
    }


def test_repo_base_can_differ_from_the_slug(render: Render) -> None:
    # The project slug is `tidal`; its repository base is `tidal-flow`.
    project = render("paper", project_slug="tidal", repo_base="tidal-flow")
    assert project.name == "tidal-flow-paper"


def test_paper_repo_keeps_agent_files_untracked(render: Render) -> None:
    ignored = (render("paper") / ".gitignore").read_text().splitlines()
    assert {"AGENTS.md", "CLAUDE.md"} <= set(ignored)


@pytest.mark.parametrize("kind", template_kinds())
def test_every_repo_ignores_env_files_but_the_example(
    kind: str, render: Render
) -> None:
    ignored = (render(kind) / ".gitignore").read_text().splitlines()
    assert {".env", ".env.*", "!.env.example", ".work/"} <= set(ignored)


@pytest.mark.parametrize("kind", template_kinds())
def test_every_repo_ignores_what_the_research_tools_write(
    kind: str, render: Render
) -> None:
    # ADR 0009: all five local outputs, in every repository.
    ignored = (render(kind) / ".gitignore").read_text().splitlines()
    assert {
        ".agent-state/", ".work/", "journal.md", "graphify-out/",
        ".venue-check",
    } <= set(ignored)  # fmt: skip


def test_missing_include_refuses_to_render(tmp_path: Path) -> None:
    # Guard: a stub naming a shared file that does not exist must fail the
    # render, never produce an empty file. Works on a copy of the tree.
    copy = tmp_path / "tree"
    shutil.copytree(
        ROOT,
        copy,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git", ".venv"),
    )
    stub = copy / "paper" / "{{cookiecutter.repo_name}}" / "missing.txt"
    stub.write_text('{% include "base/does-not-exist" -%}\n')
    with pytest.raises(TemplateNotFound):
        cookiecutter(
            str(copy),
            directory="paper",
            no_input=True,
            output_dir=str(tmp_path / "out"),
        )
