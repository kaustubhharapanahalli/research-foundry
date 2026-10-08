"""Focused tests for each Model Context Protocol tool."""

from pathlib import Path

import pytest
from research_foundry import server
from research_foundry.layout import LayoutFinding, LayoutResult
from research_foundry.templates import FoundryError


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


def test_check_layout_tool_reports_shared_checker_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The read-only tool returns the layout findings without confirmation."""
    result = LayoutResult((LayoutFinding("extra", "archive"),))
    monkeypatch.setattr(server, "_check_layout", lambda _path: result)

    checked = server.check_layout(str(tmp_path))

    assert checked == {
        "ok": True,
        "findings": [{"kind": "extra", "path": "archive"}],
        "report": "extra: archive",
    }


def test_check_layout_tool_returns_a_corrective_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The tool turns a checker refusal into a visible error."""

    def refuse(_path: Path) -> LayoutResult:
        raise FoundryError("not a Git repository")

    monkeypatch.setattr(server, "_check_layout", refuse)

    result = server.check_layout("/not-a-workspace")

    assert result["ok"] is False
    assert "not a Git repository" in str(result["error"])


def test_update_project_requires_confirmation(tmp_path: Path) -> None:
    """The update tool refuses before cruft runs without confirmation."""
    result = server.update_project(str(tmp_path), False)
    assert result["ok"] is False
    assert "confirm=true" in str(result["error"])
