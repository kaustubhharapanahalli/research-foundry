"""The package root. It exposes the installed version."""

from importlib.metadata import version

__version__ = version(
    "{{ cookiecutter.repo_name }}",
)
