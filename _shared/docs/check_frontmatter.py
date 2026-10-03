"""Check that Markdown documents carry the OKF frontmatter fields.

Run by pre-commit with the Markdown files to check as arguments. README,
AGENTS, CHANGELOG and similar repository files are exempt; every other
document needs the six fields, and its ``resource`` must name the file's own
path, so a moved document cannot keep a stale one.
"""

import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

import yaml

REQUIRED = ("type", "title", "description", "resource", "tags", "timestamp")
EXEMPT = frozenset(
    {
        "AGENTS.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "README.md",
        "SECURITY.md",
    }
)
_FENCE = "---\n"


class FrontmatterError(ValueError):
    """The frontmatter block exists but cannot be read."""


def read_frontmatter(text: str) -> dict[str, object] | None:
    r"""Return a document's frontmatter, or None if it has none.

    Args:
        text: The whole Markdown file.

    Returns:
        The YAML mapping between the opening and closing ``---`` lines, or
        None when the file does not start with ``---``.

    Raises:
        FrontmatterError: If the block is not closed, is not valid YAML, or
            is not a mapping.

    Example:
        >>> read_frontmatter("---\ntitle: A\n---\n# A\n")
        {'title': 'A'}
    """
    if not text.startswith(_FENCE):
        return None
    end = text.find("\n" + _FENCE, len(_FENCE) - 1)
    if end == -1:
        raise FrontmatterError("frontmatter is never closed with ---")
    try:
        data = yaml.safe_load(text[len(_FENCE) : end + 1])
    except yaml.YAMLError as error:
        raise FrontmatterError(
            f"frontmatter is not valid YAML: {error}"
        ) from error
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter is not a mapping")
    return {str(key): value for key, value in data.items()}


def _timestamp_problem(value: object) -> str | None:
    if isinstance(value, (datetime, date)):
        return None
    try:
        datetime.fromisoformat(str(value))
    except ValueError:
        return f"timestamp {value!r} is not an ISO 8601 date"
    return None


def problems(path: Path, text: str) -> list[str]:
    """List what is wrong with one document's frontmatter.

    Args:
        path: The document's path, relative to the repository root.
        text: The document's contents.

    Returns:
        One message per problem; empty when the document is fine.
    """
    try:
        data = read_frontmatter(text)
    except FrontmatterError as error:
        return [str(error)]
    if data is None:
        return ["no frontmatter"]
    found = [f"missing {key}" for key in REQUIRED if not data.get(key)]
    if "tags" in data and not isinstance(data["tags"], list):
        found.append("tags must be a list")
    if data.get("timestamp"):
        message = _timestamp_problem(data["timestamp"])
        if message:
            found.append(message)
    expected = "/" + path.as_posix()
    if data.get("resource") and data["resource"] != expected:
        found.append(
            f"resource is {data['resource']!r}, expected {expected!r}"
        )
    return found


def main(argv: Sequence[str]) -> int:
    """Check every non-exempt Markdown file named in ``argv``.

    Args:
        argv: Paths relative to the repository root.

    Returns:
        0 when every document passes, 1 otherwise.
    """
    failed = False
    for name in argv:
        path = Path(name)
        if path.name in EXEMPT or path.suffix != ".md":
            continue
        for message in problems(path, path.read_text(encoding="utf-8")):
            print(f"{name}: {message}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
