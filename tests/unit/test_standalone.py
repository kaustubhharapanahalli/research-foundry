"""The published repository contains no references to private systems."""

import re
import subprocess
from pathlib import Path

import pytest
from tests.conftest import ROOT

FORBIDDEN = (
    re.compile("research" + r"[-_]" + "os", re.IGNORECASE),
    re.compile("research" + "-org", re.IGNORECASE),
    re.compile(r"\b" + "ROS" + r"_[A-Za-z0-9_]*"),
    re.compile("spin" + "odal", re.IGNORECASE),
    re.compile("az" + "ti", re.IGNORECASE),
    re.compile(r"\b" + "SI" + "GN" + r"\b"),
    re.compile("sign" + "-workspace", re.IGNORECASE),
    re.compile("sign" + "-paper", re.IGNORECASE),
    re.compile("/Users/" + "kaustubh", re.IGNORECASE),
    re.compile(r"~/code/" + "research", re.IGNORECASE),
    # Another tracker's cards and decision codes: "#180" here would link to
    # this repository's own issue 180.
    re.compile(r"\b" + "card" + r" #\d+", re.IGNORECASE),
    re.compile(r"\b" + "decision" + r" [A-Z]\d+\b"),
)

EXAMPLES = (
    "research" + "-os",
    "research" + "_os",
    "research" + "-org",
    "ROS" + "_RUN_ID",
    "spin" + "odal",
    "az" + "ti",
    "SI" + "GN",
    "sign" + "-workspace",
    "sign" + "-paper",
    "/Users/" + "kaustubh",
    "~/code/" + "research",
    "card" + " #183",
    "decision" + " D1",
)


def _violations(text: str) -> list[tuple[int, str]]:
    return [
        (line_number, line)
        for line_number, line in enumerate(text.splitlines(), start=1)
        if any(pattern.search(line) for pattern in FORBIDDEN)
    ]


def _tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [ROOT / name.decode() for name in output.split(b"\0") if name]


@pytest.mark.unit
def test_tracked_files_are_standalone() -> None:
    failures = [
        f"{path.relative_to(ROOT)}:{line_number}: {line}"
        for path in _tracked_files()
        if path.is_file()
        for line_number, line in _violations(
            path.read_text(encoding="utf-8", errors="replace")
        )
    ]
    assert not failures, "private references remain:\n" + "\n".join(failures)


@pytest.mark.unit
@pytest.mark.parametrize("example", EXAMPLES)
def test_standalone_guard_catches_each_forbidden_pattern(example: str) -> None:
    assert _violations(f"allowed\n{example}\n") == [(2, example)]
