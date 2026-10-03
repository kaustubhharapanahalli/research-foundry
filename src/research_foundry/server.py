"""Model Context Protocol server for research-foundry.

Examples:
    >>> server.name
    'research-foundry'
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

# mcp 2.x renamed FastMCP to MCPServer.  This alias preserves the requested
# FastMCP programming model while using the locked, typed SDK API.
from mcp.server.mcpserver import MCPServer as FastMCP
from research_foundry import __version__
from research_foundry.cruft import check_project as _check_project
from research_foundry.cruft import update_project as _update_project
from research_foundry.templates import (
    FoundryError,
    HookRefusal,
)
from research_foundry.templates import create_project as _create_project
from research_foundry.templates import (
    describe_questions as _describe_questions,
)
from research_foundry.templates import list_templates as _list_templates
from research_foundry.templates import plan_project as _plan_project


class ToolResult(TypedDict, total=False):
    """A JSON-compatible success or refusal from an MCP tool.

    Examples:
        >>> ToolResult(ok=False, error="Fix the request.")["ok"]
        False
    """

    ok: bool
    error: str
    questions: list[dict[str, str | list[str]]]
    files: list[str]
    path: str
    up_to_date: bool
    updated: bool


server = FastMCP("research-foundry", version=__version__)


@server.tool()
def list_templates() -> list[dict[str, str]]:
    """List available templates with their titles and descriptions.

    Returns:
        JSON-compatible template descriptions in catalog order.

    Examples:
        >>> list_templates()[0]["name"]
        'methodology'
    """
    return [item.as_dict() for item in _list_templates()]


@server.tool()
def describe_questions(template: str) -> ToolResult:
    """Describe a template's public answers, defaults, and choices.

    Args:
        template: A template name returned by :func:`list_templates`.

    Returns:
        Questions on success, or a corrective refusal.

    Examples:
        >>> describe_questions("paper")["ok"]
        True
    """
    try:
        questions = [item.as_dict() for item in _describe_questions(template)]
    except FoundryError as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, "questions": questions}


@server.tool()
def plan_project(template: str, answers: dict[str, str]) -> ToolResult:
    """Validate answers by rendering temporarily, then list the files.

    Args:
        template: A template name returned by :func:`list_templates`.
        answers: Explicit Cookiecutter context overrides.

    Returns:
        The generated file list or the hook's corrective refusal reason.

    Examples:
        >>> plan_project("workspace", {})["ok"]
        True
    """
    try:
        files = _plan_project(template, answers)
    except (FoundryError, HookRefusal) as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, "files": files}


@server.tool()
def create_project(
    template: str,
    answers: dict[str, str],
    output_dir: str,
    confirm: bool,
) -> ToolResult:
    """Create a project after explicit confirmation.

    Args:
        template: A template name returned by :func:`list_templates`.
        answers: Explicit Cookiecutter context overrides.
        output_dir: Parent directory for the generated project.
        confirm: Must be ``True`` before anything is written.

    Returns:
        The created path or a corrective refusal.

    Examples:
        >>> create_project("workspace", {}, "/tmp/example", False)["ok"]
        False
    """
    if not confirm:
        return {
            "ok": False,
            "error": (
                "Project creation is not confirmed; review the plan and call "
                "create_project again with confirm=true."
            ),
        }
    try:
        project = _create_project(template, answers, Path(output_dir))
    except (FoundryError, HookRefusal) as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, "path": str(project)}


@server.tool()
def check_project(path: str) -> ToolResult:
    """Check whether a generated project is behind its template.

    Args:
        path: The generated project's root directory.

    Returns:
        The current/behind result or a corrective refusal.

    Examples:
        >>> check_project("/path/that/does/not/exist")["ok"]
        False
    """
    project = Path(path)
    if not (project / ".cruft.json").is_file():
        return {
            "ok": False,
            "error": (
                f"{project} has no .cruft.json; run this command in a project "
                "created by research-foundry."
            ),
        }
    try:
        current = _check_project(project)
    except (OSError, RuntimeError, ValueError) as error:
        return {
            "ok": False,
            "error": (
                f"The project could not be checked: {error}; repair "
                ".cruft.json and retry."
            ),
        }
    return {"ok": True, "up_to_date": current}


@server.tool()
def update_project(path: str, confirm: bool) -> ToolResult:
    """Update a generated project after explicit confirmation.

    Args:
        path: The generated project's root directory.
        confirm: Must be ``True`` before cruft applies changes.

    Returns:
        The update result or a corrective refusal.

    Examples:
        >>> update_project("/tmp/example", False)["ok"]
        False
    """
    if not confirm:
        return {
            "ok": False,
            "error": (
                "Project update is not confirmed; review the pending update "
                "and call update_project again with confirm=true."
            ),
        }
    project = Path(path)
    if not (project / ".cruft.json").is_file():
        return {
            "ok": False,
            "error": (
                f"{project} has no .cruft.json; choose a project created by "
                "research-foundry."
            ),
        }
    try:
        updated = _update_project(project, yes=True)
    except (OSError, RuntimeError, ValueError) as error:
        return {
            "ok": False,
            "error": (
                f"The project could not be updated: {error}; repair "
                ".cruft.json and retry."
            ),
        }
    return {"ok": updated, "updated": updated}


def run() -> None:
    """Run the server over standard input and output.

    Examples:
        >>> callable(run)
        True
    """
    server.run(transport="stdio")


__all__ = [
    "ToolResult",
    "check_project",
    "create_project",
    "describe_questions",
    "list_templates",
    "plan_project",
    "run",
    "server",
    "update_project",
]
