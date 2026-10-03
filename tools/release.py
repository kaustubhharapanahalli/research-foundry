"""Validate and publish a research-foundry release.

Release metadata comes from ``pyproject.toml`` and ``CHANGELOG.md``. External
commands use one replaceable boundary so tests never invoke GitHub CLI or Git.

Examples:
    Check release metadata for a tag::

        uv run python -m tools.release check --tag v0.1.0

    Refuse publication when the GitHub repository is private::

        uv run python -m tools.release refuse-private
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent


class ReleaseError(ValueError):
    """Report release metadata or publication that must be refused."""


def run_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one external command and capture its text output.

    Args:
        argv: Command and arguments. GitHub CLI and Git calls must use this
            boundary so unit tests can replace it.

    Returns:
        The completed process without raising for a non-zero status.

    Examples:
        The boundary is available for callers and tests to replace.

        >>> callable(run_command)
        True
    """
    return subprocess.run(  # noqa: S603 - argv is fixed by this module
        argv,
        check=False,
        capture_output=True,
        text=True,
    )


def project_version(path: Path) -> str:
    r"""Read the project version from a ``pyproject.toml`` file.

    Args:
        path: Project metadata file.

    Returns:
        The non-empty project version.

    Raises:
        ReleaseError: If the project version is absent or invalid.

    Examples:
        Versions are returned as text.

        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as directory:
        ...     path = Path(directory) / "pyproject.toml"
        ...     _ = path.write_text('[project]\nversion = "1.2.3"\n')
        ...     project_version(path)
        '1.2.3'
    """
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ReleaseError(f"project.version is missing from {path}")
    return version


def changelog_section(path: Path, version: str) -> str:
    r"""Extract one dated Keep a Changelog version section.

    The version heading is excluded. Markdown below it is preserved exactly,
    apart from boundary whitespace, until the next level-two heading.

    Args:
        path: Keep a Changelog 1.1.0 file.
        version: Version without a leading ``v``.

    Returns:
        Markdown to use as GitHub Release notes.

    Raises:
        ReleaseError: If no dated heading exists or its section is empty.

    Examples:
        The next version heading bounds the returned notes.

        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as directory:
        ...     path = Path(directory) / "CHANGELOG.md"
        ...     _ = path.write_text(
        ...         "## [1.2.3] - 2026-10-02\n\n- New.\n\n## [1.2.2]"
        ...     )
        ...     changelog_section(path, "1.2.3")
        '- New.'
    """
    text = path.read_text(encoding="utf-8")
    heading = re.compile(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}[ \t]*$",
        re.MULTILINE,
    )
    match = heading.search(text)
    if match is None:
        raise ReleaseError(
            f"CHANGELOG.md has no dated section for version {version}"
        )
    next_heading = re.search(r"^## ", text[match.end() :], re.MULTILINE)
    end = (
        len(text)
        if next_heading is None
        else match.end() + next_heading.start()
    )
    notes = text[match.end() : end].strip()
    if not notes:
        raise ReleaseError(
            f"CHANGELOG.md section for version {version} is empty"
        )
    return notes


def check_release(tag: str, root: Path = ROOT) -> tuple[str, str]:
    r"""Validate a tag against the project version and changelog.

    Args:
        tag: Release tag, including its leading ``v``.
        root: Repository root.

    Returns:
        The project version and its release notes.

    Raises:
        ReleaseError: If the tag or changelog does not match the project.

    Examples:
        The validator is available to command-line and library callers.

        >>> callable(check_release)
        True
    """
    version = project_version(root / "pyproject.toml")
    expected = f"v{version}"
    if tag != expected:
        raise ReleaseError(f"release tag is {tag!r}; expected {expected}")
    notes = changelog_section(root / "CHANGELOG.md", version)
    return version, notes


def public_repository_output(output: str) -> bool:
    r"""Return whether GitHub CLI reported exactly a public repository.

    Args:
        output: Standard output from querying the repository's ``private``
            property.

    Returns:
        ``True`` only when the stripped output is exactly ``false``.

    Examples:
        Missing and private results fail closed.

        >>> public_repository_output("false\n")
        True
        >>> public_repository_output("")
        False
        >>> public_repository_output("true\n")
        False
    """
    return output in ("false", "false\n", "false\r\n")


def refuse_private() -> int:
    """Query GitHub and refuse unless the repository is explicitly public.

    Returns:
        Zero only for an exact ``false`` response; one otherwise.

    Examples:
        This command is intended for a GitHub Actions environment.

        >>> callable(refuse_private)
        True
    """
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        print("refused: GITHUB_REPOSITORY is empty", file=sys.stderr)
        return 1
    completed = run_command(
        ["gh", "api", f"repos/{repository}", "--jq", ".private"]
    )
    if completed.returncode != 0 or not public_repository_output(
        completed.stdout
    ):
        detail = (completed.stdout + completed.stderr).strip() or "no output"
        print(
            f"refused: repository public check did not return false: {detail}",
            file=sys.stderr,
        )
        return 1
    return 0


def create_github_release(tag: str, root: Path = ROOT) -> int:
    """Create a GitHub Release from validated metadata and distributions.

    PEP 440 pre-release and development versions create a GitHub pre-release.

    Args:
        tag: Existing immutable release tag.
        root: Repository root containing ``dist/``.

    Returns:
        The GitHub CLI exit status.

    Raises:
        ReleaseError: If metadata is invalid or no distribution exists.

    Examples:
        The function is exposed for the command-line entry point.

        >>> callable(create_github_release)
        True
    """
    version, notes = check_release(tag, root)
    artifacts = sorted(
        path for path in (root / "dist").glob("*") if path.is_file()
    )
    if not artifacts:
        raise ReleaseError("dist/ contains no release artifacts")
    command = [
        "gh",
        "release",
        "create",
        tag,
        *(str(path) for path in artifacts),
        "--title",
        version,
        "--notes",
        notes,
    ]
    if Version(version).is_prerelease:
        command.append("--prerelease")
    completed = run_command(command)
    if completed.returncode:
        detail = (completed.stdout + completed.stderr).strip()
        print(
            detail or "gh release create failed without output",
            file=sys.stderr,
        )
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    """Run one release command.

    Args:
        argv: Command-line arguments, or ``None`` for :data:`sys.argv`.

    Returns:
        Zero on success and one when a release guard refuses.

    Examples:
        The command-line dispatcher is directly testable.

        >>> callable(main)
        True
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "github-release"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--tag", required=True)
    subparsers.add_parser("refuse-private")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            version, _ = check_release(args.tag)
            print(f"release metadata matches v{version}")
            return 0
        if args.command == "github-release":
            return create_github_release(args.tag)
        return refuse_private()
    except (OSError, ReleaseError, tomllib.TOMLDecodeError) as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
