"""Generated projects separate their Python floor from their interpreter."""

import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest
from cookiecutter.exceptions import FailedHookException

Render = Callable[..., Path]


@pytest.mark.parametrize(
    "template", ["methodology", "workspace", "paper", "software"]
)
def test_generated_project_separates_floor_from_interpreter(
    template: str, render: Render
) -> None:
    project = render(template, python_version="3.13")
    with (project / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    assert pyproject["project"]["requires-python"] == ">=3.12"
    assert (project / ".python-version").read_text() == "3.13\n"


@pytest.mark.parametrize("template", ["methodology", "software"])
def test_generated_python_tools_target_the_supported_floor(
    template: str, render: Render
) -> None:
    config = render(template) / ".dev-config"
    assert 'target-version = ["py312"]' in (config / "black.toml").read_text()
    assert 'target-version = "py312"' in (config / "ruff.toml").read_text()
    assert "python_version = 3.12" in (config / "mypy.ini").read_text()
    assert "py-version = 3.12" in (config / "pylintrc").read_text()


@pytest.mark.parametrize(
    "template", ["methodology", "workspace", "paper", "software"]
)
def test_template_refuses_an_interpreter_below_its_floor(
    template: str,
    render: Render,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(FailedHookException):
        render(template, python_version="3.11")
    assert "python_version must be 3.12 or newer." in capfd.readouterr().err
    assert not any(tmp_path.glob("my-project*"))
