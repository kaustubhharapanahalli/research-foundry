import json
import subprocess
import time
from argparse import Namespace
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from {{ ml_package }} import (
    runrecord,
)
from {{ ml_package }}.runrecord import (
    RunRecordError,
    finish_record,
    git_state,
    start_record,
    write_record,
)

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.org"]


@pytest.fixture(name="repo")
def _repo(tmp_path: Path) -> Path:
    subprocess.run([*GIT, "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("a\n")
    subprocess.run([*GIT, "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run([*GIT, "commit", "-qm", "a"], cwd=tmp_path, check=True)
    return tmp_path


def _start(repo: Path, **config: object) -> runrecord.RunRecord:
    return start_record(
        repo,
        config,  # type: ignore[arg-type]
        seed=7,
        deterministic=True,
        device=torch.device("cpu"),
        compile_model=False,
        sweep_index=2,
    )


def test_clean_tree_is_not_dirty(repo: Path) -> None:
    commit, dirty = git_state(repo)
    assert len(commit) == 40 and not dirty


def test_uncommitted_change_is_dirty(repo: Path) -> None:
    (repo / "a.txt").write_text("changed\n")
    assert git_state(repo)[1]


def test_outside_git_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RunRecordError, match="not a git working tree"):
        git_state(tmp_path)


def test_record_holds_what_the_run_ran_on(repo: Path) -> None:
    record = _start(repo, lr=0.1, layers=2)
    assert record.config == {"lr": 0.1, "layers": 2}
    assert record.seed == 7
    assert record.deterministic and not record.compile
    assert record.device == "cpu" and record.torch == torch.__version__
    assert record.sweep_index == 2 and record.wall_seconds is None


def test_non_primitive_config_is_refused(repo: Path) -> None:
    with pytest.raises(RunRecordError, match="Namespace"):
        _start(repo, args=Namespace(lr=0.1))


def test_finish_fills_time_and_memory(repo: Path) -> None:
    record = finish_record(_start(repo), time.monotonic() - 1.0)
    assert record.wall_seconds is not None and record.wall_seconds >= 1.0
    assert record.peak_memory_bytes is not None
    assert record.peak_memory_bytes > 0


def test_cuda_peak_memory_comes_from_the_allocator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda _: 4096)
    assert runrecord.peak_memory_bytes(torch.device("cuda")) == 4096


def test_record_round_trips_as_json(repo: Path, tmp_path: Path) -> None:
    record = _start(repo, lr=0.1)
    path = tmp_path / "run.json"
    write_record(record, path)
    assert json.loads(path.read_text()) == asdict(record)


def test_existing_record_is_never_overwritten(
    repo: Path, tmp_path: Path
) -> None:
    path = tmp_path / "run.json"
    path.write_text("{}\n")
    with pytest.raises(RunRecordError, match="already exists"):
        write_record(_start(repo), path)
    assert path.read_text() == "{}\n"
