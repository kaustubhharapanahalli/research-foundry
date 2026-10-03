"""Every template file reaches GitHub, even one its own .gitignore names.

Git applies a template's .gitignore inside foundry too, so a file the
generated project must not commit is also ignored here. The paper's agent
files were missed that way: rendering from the working tree had them, a
render from GitHub did not.
"""

import subprocess

from tests.conftest import ROOT, template_kinds

# Ignored by their template's .gitignore on purpose, and force-added here.
KNOWN_IGNORED = {
    "paper/{{cookiecutter.repo_name}}/AGENTS.md",
    "paper/{{cookiecutter.repo_name}}/CLAUDE.md",
}


def _git(*args: str, stdin: str = "") -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    ).stdout


def _template_files() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for kind in template_kinds()
        for path in (ROOT / kind).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def test_only_known_template_files_are_ignored() -> None:
    ignored = _git(
        "check-ignore",
        "--no-index",
        "--stdin",
        stdin="\n".join(_template_files()),
    ).split()
    assert set(ignored) == KNOWN_IGNORED


def test_known_ignored_files_are_tracked() -> None:
    tracked = set(_git("ls-files", *sorted(KNOWN_IGNORED)).split("\n"))
    assert KNOWN_IGNORED <= tracked
