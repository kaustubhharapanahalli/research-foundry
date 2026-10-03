import os

import pytest
import torch

from {{ ml_package }}.threads import (
    CpuBudgetError,
    apply_thread_budget,
    available_cpus,
)


@pytest.fixture(autouse=True)
def _not_under_slurm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    monkeypatch.delenv("SLURM_CPUS_PER_TASK", raising=False)


def test_outside_slurm_uses_the_cpus_this_process_may_run_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 64)
    monkeypatch.setattr(
        os, "sched_getaffinity", lambda _pid: {0, 1, 2}, raising=False
    )
    assert available_cpus() == 3


def test_without_an_affinity_mask_uses_the_cpu_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 5)
    assert available_cpus() == 5


def test_slurm_budget_comes_from_cpus_per_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SLURM_JOB_ID", "1")
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "6")
    assert available_cpus() == 6


def test_slurm_job_without_cpus_per_task_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SLURM_JOB_ID", "1")
    with pytest.raises(CpuBudgetError, match="--cpus-per-task"):
        available_cpus()


def test_budget_within_limits_sets_torch_threads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        os, "sched_getaffinity", lambda _pid: set(range(4)), raising=False
    )
    apply_thread_budget(threads=2, num_workers=2)
    assert torch.get_num_threads() == 2


def test_budget_over_the_limit_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        os, "sched_getaffinity", lambda _pid: set(range(4)), raising=False
    )
    with pytest.raises(CpuBudgetError, match="exceed the 4 CPUs"):
        apply_thread_budget(threads=3, num_workers=2)


@pytest.mark.parametrize(("threads", "workers"), [(0, 0), (1, -1)])
def test_impossible_counts_are_refused(threads: int, workers: int) -> None:
    with pytest.raises(ValueError, match="threads must be"):
        apply_thread_budget(threads, workers)
