"""GitHub workflows follow GitHub's security hardening guidance."""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.conftest import ROOT

WORKFLOW_DIRECTORY = ROOT / ".github" / "workflows"
WORKFLOWS = sorted(
    [*WORKFLOW_DIRECTORY.glob("*.yml"), *WORKFLOW_DIRECTORY.glob("*.yaml")]
)
# A full-length commit SHA, then the release it stands for as a comment.
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_UV_SHA = "c18668ad3cf93ea998bef934396af7bb5c839dc7"


def _load(path: Path) -> dict[Any, Any]:
    data: dict[Any, Any] = yaml.safe_load(path.read_text())
    return data


def _steps(path: Path) -> list[dict[str, Any]]:
    return [
        step
        for job in _load(path)["jobs"].values()
        for step in job.get("steps", [])
    ]


def _publishes(job: dict[str, Any]) -> bool:
    return any(
        step.get("uses", "").startswith(
            ("pypa/gh-action-pypi-publish@", "actions/deploy-pages@")
        )
        or step.get("run", "").startswith("make github-release")
        for step in job.get("steps", [])
    )


def _assert_publish_guards(workflow: dict[Any, Any]) -> None:
    expected = "format('{0}', github.event.repository.private) == 'false'"
    for job in workflow["jobs"].values():
        if not _publishes(job):
            continue
        assert job.get("if") == expected
        first_guarded_step: dict[str, Any] = next(
            (
                step
                for step in job.get("steps", [])
                if not step.get("uses", "").startswith(
                    ("actions/checkout@", "astral-sh/setup-uv@")
                )
            ),
            {},
        )
        assert first_guarded_step.get("run") == "make refuse-private"
        assert first_guarded_step.get("env") == {
            "GH_TOKEN": "${{ github.token }}",
            "GITHUB_REPOSITORY": "${{ github.repository }}",
        }


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_commit(path: Path) -> None:
    for step in _steps(path):
        if "uses" in step:
            assert PINNED.match(step["uses"]), step["uses"]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_pin_names_its_release(path: Path) -> None:
    for line in path.read_text().splitlines():
        if "uses:" in line:
            # A repository-local reusable workflow is source, not an action
            # release, so there is no external revision to pin or name.
            if "uses: ./" in line:
                continue
            version = r"# (?:v\d|TODO pin: [\w./-]+@v\d)"
            assert re.search(version, line), line.strip()


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_token_is_read_only_by_default(path: Path) -> None:
    assert _load(path)["permissions"] == {"contents": "read"}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_job_declares_least_privilege_permissions(path: Path) -> None:
    for job in _load(path)["jobs"].values():
        # A job-level `uses` delegates its steps and permissions to the called
        # reusable workflow; it is not a normal job with its own steps.
        if "uses" in job:
            continue
        assert "permissions" in job
        writes_release = any(
            step.get("run", "").startswith("make github-release")
            for step in job["steps"]
        )
        expected = "write" if writes_release else "read"
        assert job["permissions"]["contents"] == expected


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_job_has_a_timeout(path: Path) -> None:
    # The default is 360 minutes; a hung job should not burn six hours.
    for job in _load(path)["jobs"].values():
        # GitHub does not allow timeout-minutes on a job that calls a reusable
        # workflow; the called workflow owns the timeout for its actual jobs.
        if "uses" in job:
            continue
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


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_run_steps_do_not_interpolate_github_expressions(path: Path) -> None:
    for step in _steps(path):
        if "run" in step:
            assert "${{" not in step["run"], step["run"]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_publishing_job_has_both_public_repository_guards(
    path: Path,
) -> None:
    _assert_publish_guards(_load(path))


def test_publishing_guard_allows_checkout_and_setup_uv_before_guard() -> None:
    job: dict[str, Any] = {
        "if": "format('{0}', github.event.repository.private) == 'false'",
        "steps": [
            {"uses": "actions/checkout@" + "a" * 40},
            {"uses": "astral-sh/setup-uv@" + "b" * 40},
            {
                "run": "make refuse-private",
                "env": {
                    "GH_TOKEN": "${{ github.token }}",
                    "GITHUB_REPOSITORY": "${{ github.repository }}",
                },
            },
            {"uses": "pypa/gh-action-pypi-publish@" + "c" * 40},
        ],
    }

    _assert_publish_guards({"jobs": {"publish": job}})


@pytest.mark.parametrize(
    "unsafe_step",
    [
        {"uses": "actions/download-artifact@" + "c" * 40},
        {"uses": "pypa/gh-action-pypi-publish@" + "d" * 40},
    ],
    ids=["download-artifact", "publish"],
)
def test_publishing_guard_refuses_artifact_or_publish_before_guard(
    unsafe_step: dict[str, str],
) -> None:
    job: dict[str, Any] = {
        "if": "format('{0}', github.event.repository.private) == 'false'",
        "steps": [
            {"uses": "actions/checkout@" + "a" * 40},
            {"uses": "astral-sh/setup-uv@" + "b" * 40},
            unsafe_step,
            {
                "run": "make refuse-private",
                "env": {
                    "GH_TOKEN": "${{ github.token }}",
                    "GITHUB_REPOSITORY": "${{ github.repository }}",
                },
            },
            {"uses": "pypa/gh-action-pypi-publish@" + "e" * 40},
        ],
    }

    with pytest.raises(AssertionError):
        _assert_publish_guards({"jobs": {"publish": job}})


@pytest.mark.parametrize("missing", ["condition", "guard-step"])
def test_publishing_guard_refuses_a_job_missing_either_layer(
    missing: str,
) -> None:
    job: dict[str, Any] = {
        "if": "format('{0}', github.event.repository.private) == 'false'",
        "steps": [
            {
                "run": "make refuse-private",
                "env": {
                    "GH_TOKEN": "${{ github.token }}",
                    "GITHUB_REPOSITORY": "${{ github.repository }}",
                },
            },
            {"uses": "pypa/gh-action-pypi-publish@" + "a" * 40},
        ],
    }
    if missing == "condition":
        del job["if"]
    else:
        job["steps"] = job["steps"][1:]

    with pytest.raises(AssertionError):
        _assert_publish_guards({"jobs": {"publish": job}})


@pytest.mark.parametrize(
    ("workflow", "job_name"),
    [
        ("release.yml", "testpypi"),
        ("release.yml", "pypi"),
        ("release.yml", "github-release"),
        ("docs.yml", "deploy"),
    ],
)
def test_publishing_jobs_bootstrap_before_running_guard(
    workflow: str, job_name: str
) -> None:
    job = _load(ROOT / ".github" / "workflows" / workflow)["jobs"][job_name]

    assert job["steps"][:3] == [
        {
            "uses": f"actions/checkout@{CHECKOUT_SHA}",
            "with": {"persist-credentials": False},
        },
        {
            "uses": f"astral-sh/setup-uv@{SETUP_UV_SHA}",
            "with": {"enable-cache": True},
        },
        {
            "run": "make refuse-private",
            "env": {
                "GH_TOKEN": "${{ github.token }}",
                "GITHUB_REPOSITORY": "${{ github.repository }}",
            },
        },
    ]


def test_docs_build_strictly_and_only_the_deploy_job_may_write_pages() -> None:
    docs = _load(ROOT / ".github" / "workflows" / "docs.yml")
    assert docs[True] == {
        "push": {"branches": ["main"]},
        "workflow_dispatch": None,
    }
    build, deploy = docs["jobs"]["build"], docs["jobs"]["deploy"]
    assert [step.get("run") for step in build["steps"] if "run" in step] == [
        "make install",
        "make docs",
    ]
    assert build["steps"][-1]["with"] == {"path": "site/"}
    assert build["permissions"] == {"contents": "read"}
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["steps"][-1]["uses"].startswith("actions/deploy-pages@")


def test_ci_checks_every_supported_python_version() -> None:
    check = _load(ROOT / ".github" / "workflows" / "ci.yml")["jobs"]["check"]
    assert check["strategy"] == {
        "fail-fast": False,
        "matrix": {"python": ["3.12", "3.13", "3.14"]},
    }
    assert check["name"] == "Python ${{ matrix.python }}"
    runs = [step["run"] for step in check["steps"] if "run" in step]
    assert runs == [
        'make install PYTHON="$PYTHON"',
        'make ci PYTHON="$PYTHON"',
    ]
