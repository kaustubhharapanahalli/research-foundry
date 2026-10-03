"""Shared fixtures: the repository root, the template index, and rendering."""

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from cookiecutter import config as cookiecutter_config
from cookiecutter.main import cookiecutter
from tools.throwaway import NO_AUTO_MAINTENANCE

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "_shared"
# A template's project folder is the one directory whose name is a variable.
PROJECT_DIR = "{{cookiecutter.repo_name}}"
# The identity tests commit with, so a runner with no git config still works.
GIT_ENV = {
    "GIT_AUTHOR_NAME": "foundry-test",
    "GIT_AUTHOR_EMAIL": "foundry-test@example.org",
    "GIT_COMMITTER_NAME": "foundry-test",
    "GIT_COMMITTER_EMAIL": "foundry-test@example.org",
    # A background repack can race a clone; see NO_AUTO_MAINTENANCE.
    **NO_AUTO_MAINTENANCE,
}
INCLUDE = re.compile(r"""\{%-?\s*include\s+["']([^"']+)["']""")
# Template syntax a render should never leave behind. JSX's {{ ... }}
# style objects and GitHub's ${{ ... }} are not template syntax.
LEFTOVER = re.compile(r"\{\{\s*cookiecutter|\{%")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark each test unit or functional from the folder it sits in."""
    for item in items:
        for kind in ("unit", "functional"):
            if f"{Path('tests') / kind}" in str(item.path):
                item.add_marker(getattr(pytest.mark, kind))


def template_kinds() -> list[str]:
    """Return the template names listed in the top-level cookiecutter.json."""
    index = json.loads((ROOT / "cookiecutter.json").read_text())
    return sorted(index["templates"])


@pytest.fixture(autouse=True, scope="session")
def isolate_cookiecutter_replays(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    """Keep Cookiecutter's test replay files inside pytest's workspace."""
    original = cookiecutter_config.DEFAULT_CONFIG["replay_dir"]
    replay = tmp_path_factory.mktemp("cookiecutter") / "replay"
    cookiecutter_config.DEFAULT_CONFIG["replay_dir"] = str(replay)
    yield
    cookiecutter_config.DEFAULT_CONFIG["replay_dir"] = original


@pytest.fixture
def render(tmp_path: Path) -> Callable[..., Path]:
    """Render one template from the working tree and return the project."""

    def _render(kind: str, out: Path | None = None, **answers: str) -> Path:
        project = cookiecutter(
            str(ROOT),
            directory=kind,
            no_input=True,
            output_dir=str(out or tmp_path),
            extra_context=answers,
        )
        return Path(project)

    return _render
