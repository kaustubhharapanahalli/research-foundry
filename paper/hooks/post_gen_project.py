"""Remove the files of options the paper did not choose.

Cookiecutter runs this inside the generated project, without asking. It
only deletes files inside that project: no network, nothing outside it.
"""

# Each template hook is a standalone entrypoint, so guards cannot be shared.
# pylint: disable=duplicate-code

import shutil
import sys
from pathlib import Path

# Rendered by cookiecutter before it runs; typed as str so a type checker
# reading the unrendered file does not see two unequal literals.
ANSWERS: dict[str, str] = {
    "github_mirror": "{{ cookiecutter.github_mirror }}",
}
PYTHON_VERSION = "{{ cookiecutter.python_version }}"
PYTHON_FLOOR = "{{ cookiecutter._python_floor }}"


def main() -> None:
    """Delete what the answers left out."""
    if tuple(map(int, PYTHON_VERSION.split("."))) < tuple(
        map(int, PYTHON_FLOOR.split("."))
    ):
        sys.exit("python_version must be 3.12 or newer.")
    if ANSWERS["github_mirror"] != "yes":
        # Overleaf is the only remote, so nothing would ever run CI.
        shutil.rmtree(Path(".github"))


if __name__ == "__main__":
    main()
