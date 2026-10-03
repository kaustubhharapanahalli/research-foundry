"""Weekly issue targets create or update exactly one GitHub issue."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from tests.conftest import ROOT


@pytest.mark.parametrize(
    ("existing", "action"), (("", "create"), ("212", "edit 212"))
)
def test_pins_issue_is_created_or_updated(
    tmp_path: Path, existing: str, action: str
) -> None:
    executable = tmp_path / "gh"
    executable.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$GH_LOG"\n'
        'if [ "$1 $2" = "issue list" ]; then printf "%s" "$GH_ISSUE"; fi\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)
    log = tmp_path / "gh.log"
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{tmp_path}:{environment['PATH']}",
            "GH_LOG": str(log),
            "GH_ISSUE": existing,
        }
    )

    completed = subprocess.run(
        ["make", "--silent", "pins-issue"],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    calls = log.read_text(encoding="utf-8").splitlines()
    assert calls[0].startswith("issue list --state open --label dependencies")
    assert calls[1].startswith(
        f"issue {action} --title Weekly template pin report"
    )
