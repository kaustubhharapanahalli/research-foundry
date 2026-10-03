"""Check and update projects created by research-foundry.

Examples:
    >>> callable(check_project) and callable(update_project)
    True
"""

from pathlib import Path

from cruft import check, update
from research_foundry.templates import FoundryError


def _require_project(path: Path) -> None:
    """Refuse a path without research-foundry's cruft metadata."""
    if not (path / ".cruft.json").is_file():
        raise FoundryError(
            f"{path} has no .cruft.json; choose a project created by "
            "research-foundry."
        )


def check_project(path: Path) -> bool:
    """Return whether a project matches the latest template release.

    Args:
        path: The generated project's root directory.

    Returns:
        ``True`` when the project is current, otherwise ``False``.

    Raises:
        FoundryError: If ``path`` is not a generated project.

    Examples:
        >>> callable(check_project)
        True
    """
    _require_project(path)
    return bool(check(project_dir=path))


def update_project(path: Path, *, yes: bool = False) -> bool:
    """Apply the latest template release to a generated project.

    Args:
        path: The generated project's root directory.
        yes: Apply without cruft's confirmation prompt.

    Returns:
        Cruft's success result.

    Raises:
        FoundryError: If ``path`` is not a generated project.

    Examples:
        >>> callable(update_project)
        True
    """
    _require_project(path)
    return bool(update(project_dir=path, skip_apply_ask=yes))


__all__ = ["check_project", "update_project"]
