"""Real template rendering through the Model Context Protocol tools."""

from pathlib import Path

import pytest
from research_foundry import server
from research_foundry.constants import REPOSITORY_ENV, TEMPLATE_NAMES


@pytest.fixture(autouse=True)
def _offline_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep release-tag resolution inside the test workspace."""
    monkeypatch.setenv(REPOSITORY_ENV, str(tmp_path / "offline-repository"))


@pytest.mark.parametrize("template", TEMPLATE_NAMES)
def test_create_project_generates_every_template(
    template: str, tmp_path: Path
) -> None:
    """The confirmed MCP tool generates each default project."""
    result = server.create_project(
        template, {}, str(tmp_path / template), confirm=True
    )
    assert result["ok"] is True
    project = Path(str(result["path"]))
    assert (project / "README.md").is_file()
    assert (project / ".cruft.json").is_file()


@pytest.mark.parametrize("template", TEMPLATE_NAMES)
def test_plan_project_validates_every_template_without_output(
    template: str,
) -> None:
    """The planning tool validates each default and returns its file list."""
    result = server.plan_project(template, {})
    assert result["ok"] is True
    assert "README.md" in result["files"]
