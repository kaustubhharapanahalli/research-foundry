"""Every script under docs_src/ runs and prints what its guide says."""

import subprocess
import sys
from pathlib import Path

import pytest

import {{ cookiecutter.package_name }}

DOCS_SRC = Path(__file__).resolve().parents[2] / "docs_src"
SCRIPTS = sorted(DOCS_SRC.glob("*.py"))
# What each guide tells the reader the script prints.
EXPECTED = {
    "check_install": {{ cookiecutter.package_name }}.__version__,
{%- if cookiecutter.ml_pytorch == "yes" %}
    "repeat_a_run": "True",
{%- endif %}
}


def test_every_script_has_an_expected_output() -> None:
    """A new guide script cannot be added without saying what it prints."""
    assert sorted(script.stem for script in SCRIPTS) == sorted(EXPECTED)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.stem)
def test_script_prints_what_its_guide_says(script: Path) -> None:
    """Run the script as a reader would, in a fresh interpreter."""
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == EXPECTED[script.stem]
