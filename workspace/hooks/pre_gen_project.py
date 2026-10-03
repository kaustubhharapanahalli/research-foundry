"""Refuse a Python interpreter older than the supported floor."""

# Each template hook is a standalone entrypoint, so guards cannot be shared.
# pylint: disable=duplicate-code

import sys

PYTHON_VERSION = "{{ cookiecutter.python_version }}"
PYTHON_FLOOR = "{{ cookiecutter._python_floor }}"


def main() -> None:
    """Exit when the chosen interpreter is below the supported floor."""
    if tuple(map(int, PYTHON_VERSION.split("."))) < tuple(
        map(int, PYTHON_FLOOR.split("."))
    ):
        sys.exit("python_version must be 3.12 or newer.")


if __name__ == "__main__":
    main()
