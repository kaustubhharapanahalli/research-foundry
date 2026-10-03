"""The methodology template renders the right files for each answer."""

import tomllib
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest
import yaml
from cookiecutter.exceptions import FailedHookException
from tests.conftest import LEFTOVER

Render = Callable[..., Path]
ML_FILES = [
    "src/my_project/seeding.py",
    "src/my_project/device.py",
    "src/my_project/threads.py",
    "src/my_project/runrecord.py",
    "tests/functional/test_determinism.py",
]


def _pyproject(project: Path) -> dict[str, Any]:
    with (project / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_pytorch_variant_ships_the_reproducibility_modules(
    render: Render,
) -> None:
    project = render("methodology", ml_pytorch="yes")
    for name in ML_FILES:
        assert (project / name).is_file(), name


def test_plain_variant_ships_none_of_them(render: Render) -> None:
    project = render("methodology", ml_pytorch="no")
    for name in ML_FILES:
        assert not (project / name).exists(), name
    assert "torch" not in (project / "pyproject.toml").read_text()


def test_package_is_installable(render: Render) -> None:
    # Without [build-system], `uv sync` does not install the project.
    data = _pyproject(render("methodology"))
    assert data["build-system"] == {
        "requires": ["hatchling"],
        "build-backend": "hatchling.build",
    }


def test_both_platforms_must_lock(render: Render) -> None:
    data = _pyproject(render("methodology", ml_pytorch="yes"))
    environments = data["tool"]["uv"]["required-environments"]
    assert len(environments) == 2


def test_pypi_cuda_source_adds_no_index(render: Render) -> None:
    data = _pyproject(render("methodology", cuda_source="pypi"))
    assert "index" not in data["tool"]["uv"]


def test_cu126_source_applies_to_linux_only(render: Render) -> None:
    data = _pyproject(render("methodology", cuda_source="cu126"))
    uv = data["tool"]["uv"]
    assert uv["index"][0]["explicit"] is True
    assert uv["sources"]["torch"] == [
        {"index": "pytorch-cu126", "marker": "sys_platform == 'linux'"}
    ]


@pytest.mark.parametrize("licence", ["Apache-2.0", "MIT"])
def test_licence_is_written_and_declared(licence: str, render: Render) -> None:
    project = render(
        "methodology", license=licence, author_name="Ada Lovelace"
    )
    text = (project / "LICENSE").read_text()
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert _pyproject(project)["project"]["license"] == licence
    if licence == "MIT":
        assert "Ada Lovelace" in text


def test_no_licence_means_no_licence_file(render: Render) -> None:
    project = render("methodology", license="none")
    assert not (project / "LICENSE").exists()
    assert "license" not in _pyproject(project)["project"]


def test_claude_md_imports_agents_md(render: Render) -> None:
    # A link would need a hook; Claude Code's @-import needs nothing.
    assert (render("methodology") / "CLAUDE.md").read_text() == "@AGENTS.md\n"


def test_agents_md_has_a_local_rules_section(render: Render) -> None:
    assert (
        "\n## Local rules\n"
        in (render("methodology") / "AGENTS.md").read_text()
    )


DOCS_FILES = [
    "docs/index.md",
    "docs/check_reference.py",
    "docs/api/index.md",
    "docs/how-to/index.md",
    "docs/how-to/check-the-install.md",
    "docs_src/check_install.py",
    ".dev-config/check_frontmatter.py",
    "make/docs.mk",
    "mkdocs.yml",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CITATION.cff",
    "tests/functional/test_docs_src.py",
    "tests/functional/test_project_files.py",
]
DOCS_ML_FILES = [
    "docs/how-to/repeat-a-run.md",
    "docs/explanation/reproducibility.md",
    "docs_src/repeat_a_run.py",
]
# Public docs need a typed contact address; it has no default.
PUBLIC = {"public_docs": "yes", "contact_email": "maintainers@example.org"}


def test_public_docs_ship_the_standard_files(render: Render) -> None:
    project = render("methodology", ml_pytorch="yes", **PUBLIC)
    for name in DOCS_FILES + DOCS_ML_FILES:
        assert (project / name).is_file(), name
    assert "include make/docs.mk" in (project / "Makefile").read_text()
    assert "docs" in _pyproject(project)["dependency-groups"]
    assert (
        yaml.safe_load((project / "mkdocs.yml").read_text())["theme"][
            "palette"
        ][0]["primary"]
        == "indigo"
    )


def test_custom_docs_theme_ships_its_assets_and_css(
    render: Render, tmp_path: Path
) -> None:
    custom = render("methodology", docs_theme="custom", **PUBLIC)
    css = custom / "docs" / "stylesheets" / "extra.css"
    config = yaml.safe_load((custom / "mkdocs.yml").read_text())
    assert css.is_file()
    assert (custom / "docs" / "assets" / "logo.svg").is_file()
    assert config["extra_css"] == ["stylesheets/extra.css"]
    assert config["theme"]["logo"] == "assets/logo.svg"
    assert config["theme"]["favicon"] == "assets/logo.svg"
    assert config["theme"]["font"] == {"text": "Roboto", "code": "Roboto Mono"}
    for variable in (
        "--md-primary-fg-color",
        "--md-accent-fg-color",
        "--md-default-bg-color",
        "--md-default-fg-color",
        "--md-typeset-a-color",
        "--md-code-bg-color",
    ):
        assert css.read_text().count(variable) == 2

    generic = render(
        "methodology", out=tmp_path / "generic", docs_theme="generic", **PUBLIC
    )
    assert not (generic / "docs" / "stylesheets" / "extra.css").exists()
    assert not (generic / "docs" / "assets").exists()
    assert "extra_css" not in yaml.safe_load(
        (generic / "mkdocs.yml").read_text()
    )


def test_docs_theme_is_ignored_without_public_docs(render: Render) -> None:
    project = render("methodology", public_docs="no", docs_theme="custom")
    assert not (project / "mkdocs.yml").exists()
    assert not (project / "docs" / "stylesheets").exists()
    assert not (project / "docs" / "assets").exists()


def test_no_public_docs_ships_none_of_them(render: Render) -> None:
    project = render("methodology", public_docs="no", ml_pytorch="yes")
    for name in DOCS_FILES + DOCS_ML_FILES:
        assert not (project / name).exists(), name
    assert not (project / "docs" / "explanation").exists()
    # The ADRs stay: they are internal documents, not public docs.
    assert (project / "docs" / "adr" / "0001-development-setup.md").is_file()
    assert "docs.mk" not in (project / "Makefile").read_text()
    assert "docs" not in _pyproject(project)["dependency-groups"]


def test_plain_public_docs_leave_out_the_pytorch_guides(
    render: Render,
) -> None:
    project = render("methodology", ml_pytorch="no", **PUBLIC)
    for name in DOCS_FILES:
        assert (project / name).is_file(), name
    for name in DOCS_ML_FILES:
        assert not (project / name).exists(), name
    index = (project / "docs" / "index.md").read_text()
    assert "explanation/reproducibility" not in index
    config = yaml.safe_load((project / "mkdocs.yml").read_text())
    assert "Explanation" not in config["nav"]


def test_public_docs_leave_no_template_syntax(render: Render) -> None:
    project = render("methodology", ml_pytorch="yes", **PUBLIC)
    for path in sorted(project.rglob("*")):
        name = str(path.relative_to(project))
        if path.is_file():
            assert not LEFTOVER.search(path.read_text()), name


def test_public_docs_render_no_sphinx_or_read_the_docs(
    render: Render,
) -> None:
    project = render("methodology", **PUBLIC)
    for path in project.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            assert "sphinx" not in text, path.relative_to(project)
            assert "read the docs" not in text, path.relative_to(project)


def test_reference_check_refuses_a_missing_public_module(
    render: Render,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = render("methodology", **PUBLIC)
    module_path = project / "docs" / "check_reference.py"
    spec = spec_from_file_location("check_reference", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    (tmp_path / "src" / "fake_package").mkdir(parents=True)
    (tmp_path / "src" / "fake_package" / "__init__.py").write_text("")
    (tmp_path / "src" / "fake_package" / "missing.py").write_text("")
    (tmp_path / "docs" / "api").mkdir(parents=True)
    (tmp_path / "docs" / "api" / "index.md").write_text("::: fake_package\n")
    monkeypatch.chdir(tmp_path)
    assert module.main(["fake_package"]) == 1
    assert capsys.readouterr().out == (
        "docs/api/index.md: missing ::: fake_package.missing\n"
    )


def test_public_docs_without_a_licence_refuse_to_render(
    render: Render, tmp_path: Path
) -> None:
    # PD14: a public repository has a licence. The hook refuses, and
    # cookiecutter removes the half-made project.
    with pytest.raises(FailedHookException):
        render("methodology", license="none", **PUBLIC)
    assert not (tmp_path / "my-project").exists()


def test_public_docs_without_a_contact_refuse_to_render(
    render: Render, tmp_path: Path
) -> None:
    # Conduct and security reports need an address someone typed.
    with pytest.raises(FailedHookException):
        render("methodology", public_docs="yes")
    assert not (tmp_path / "my-project").exists()


def test_private_project_needs_no_contact(render: Render) -> None:
    project = render("methodology", public_docs="no")
    assert not (project / "SECURITY.md").exists()


@pytest.mark.parametrize(
    ("author", "expected"),
    [
        ("Ada Lovelace", ['given-names: "Ada"', 'family-names: "Lovelace"']),
        ("Plato", ['name: "Plato"']),
    ],
)
def test_citation_names_the_author(
    author: str, expected: list[str], render: Render
) -> None:
    project = render("methodology", author_name=author, **PUBLIC)
    citation = (project / "CITATION.cff").read_text()
    for line in expected:
        assert line in citation


def test_conduct_and_security_reports_reach_the_contact(
    render: Render,
) -> None:
    project = render(
        "methodology", public_docs="yes", contact_email="ada@example.org"
    )
    for name in ("CODE_OF_CONDUCT.md", "SECURITY.md"):
        assert "ada@example.org" in (project / name).read_text(), name


def test_dataset_registry_is_left_out_by_default(render: Render) -> None:
    # A paper project's workspace holds the registry; its methodology
    # repository must not hold a second one.
    assert not (render("methodology") / "datasets").exists()


def test_dataset_registry_is_the_workspaces_own_when_asked(
    render: Render,
) -> None:
    # A lab project's methodology repository is its root, where run launchers,
    # literature tools and data adapters read the registry.
    project = render("methodology", dataset_registry="yes")
    text = (project / "datasets" / "registry.yaml").read_text()
    workspace = render("workspace") / "datasets" / "registry.yaml"
    assert text == workspace.read_text()
    # Empty, and its header says what belongs there and why it is empty.
    assert yaml.safe_load(text) is None
    assert text.startswith("# Dataset registry -- project-local, and EMPTY")
    assert "benchmark_ref" in text
    assert "datasets/registry.yaml" in (project / "README.md").read_text()


RUN_RECORD_FILES = [
    "src/my_project/sidecars.py",
    "tests/unit/test_sidecars.py",
    "tests/functional/test_dispatched_run.py",
]


def test_run_records_are_left_out_by_default(render: Render) -> None:
    # The default project writes no run-record files.
    project = render("methodology")
    assert not any((project / path).exists() for path in RUN_RECORD_FILES)


def test_run_records_are_rendered_when_asked(render: Render) -> None:
    project = render("methodology", run_records="yes")
    assert all((project / path).exists() for path in RUN_RECORD_FILES)
    assert "sidecars.py" in (project / "README.md").read_text()


def test_run_records_without_pytorch_are_refused(render: Render) -> None:
    with pytest.raises(FailedHookException):
        render("methodology", run_records="yes", ml_pytorch="no")
