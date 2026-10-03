"""Focused tests for each Model Context Protocol tool."""

from pathlib import Path

from research_foundry import server


def test_list_templates_tool() -> None:
    """The catalog tool returns structured template descriptions."""
    result = server.list_templates()
    assert [item["name"] for item in result] == [
        "methodology",
        "workspace",
        "paper",
        "software",
    ]


def test_describe_questions_tool() -> None:
    """The question tool shares the CLI's validation and schema."""
    result = server.describe_questions("paper")
    assert result["ok"] is True
    assert any(item["name"] == "venue" for item in result["questions"])


def test_plan_project_returns_a_hook_refusal() -> None:
    """Planning reports the hook's reason instead of writing a project."""
    result = server.plan_project(
        "software", {"backend_django": "no", "frontend_nextjs": "yes"}
    )
    assert result["ok"] is False
    assert "needs backend_django" in str(result["error"])


def test_create_project_requires_confirmation(tmp_path: Path) -> None:
    """The creation tool refuses before writing without confirmation."""
    result = server.create_project("workspace", {}, str(tmp_path), False)
    assert result["ok"] is False
    assert "confirm=true" in str(result["error"])
    assert not list(tmp_path.iterdir())


def test_check_project_tool_reports_a_corrective_error(tmp_path: Path) -> None:
    """Checking a non-project names the missing setup and its fix."""
    result = server.check_project(str(tmp_path))
    assert result["ok"] is False
    assert ".cruft.json" in str(result["error"])


def test_update_project_requires_confirmation(tmp_path: Path) -> None:
    """The update tool refuses before cruft runs without confirmation."""
    result = server.update_project(str(tmp_path), False)
    assert result["ok"] is False
    assert "confirm=true" in str(result["error"])
