"""GitHub workflows follow GitHub's security hardening guidance."""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.conftest import ROOT

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
# A full-length commit SHA, then the release it stands for as a comment.
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def _load(path: Path) -> dict[Any, Any]:
    data: dict[Any, Any] = yaml.safe_load(path.read_text())
    return data


def _steps(path: Path) -> list[dict[str, Any]]:
    return [s for job in _load(path)["jobs"].values() for s in job["steps"]]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_commit(path: Path) -> None:
    for step in _steps(path):
        if "uses" in step:
            assert PINNED.match(step["uses"]), step["uses"]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_pin_names_its_release(path: Path) -> None:
    for line in path.read_text().splitlines():
        if "uses:" in line:
            version = r"# (?:v\d|TODO pin: [\w./-]+@v\d)"
            assert re.search(version, line), line.strip()


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_token_is_read_only_by_default(path: Path) -> None:
    assert _load(path)["permissions"] == {"contents": "read"}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_job_declares_least_privilege_permissions(path: Path) -> None:
    for job in _load(path)["jobs"].values():
        assert "permissions" in job
        assert job["permissions"]["contents"] == "read"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_job_has_a_timeout(path: Path) -> None:
    # The default is 360 minutes; a hung job should not burn six hours.
    for job in _load(path)["jobs"].values():
        assert "timeout-minutes" in job


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_checkout_does_not_keep_the_token(path: Path) -> None:
    for step in _steps(path):
        if step.get("uses", "").startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_no_pull_request_target(path: Path) -> None:
    # PyYAML reads the bare key `on` as True.
    workflow = _load(path)
    triggers = workflow.get(True) or workflow.get("on")
    assert isinstance(triggers, dict)
    assert "pull_request_target" not in triggers


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_run_steps_only_call_make(path: Path) -> None:
    for step in _steps(path):
        if "run" in step:
            assert step["run"].startswith("make "), step["run"]


def test_ci_checks_every_supported_python_version() -> None:
    check = _load(ROOT / ".github" / "workflows" / "ci.yml")["jobs"]["check"]
    assert check["strategy"] == {
        "fail-fast": False,
        "matrix": {"python": ["3.12", "3.13", "3.14"]},
    }
    assert check["name"] == "Python ${{ matrix.python }}"
    runs = [step["run"] for step in check["steps"] if "run" in step]
    assert runs == [
        "make install PYTHON=${{ matrix.python }}",
        "make ci PYTHON=${{ matrix.python }}",
    ]
