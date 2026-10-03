"""Hold a run to the CPUs it was given, and refuse to exceed them."""

import os

import torch


def _process_cpus() -> int:
    """Return how many CPUs this process may run on.

    As Python 3.13's ``os.process_cpu_count()`` does: the affinity mask where
    the platform has one, which a scheduler or ``taskset`` can narrow below
    the machine's count.
    """
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0)) or 1
    return os.cpu_count() or 1


class CpuBudgetError(RuntimeError):
    """A run asked for more CPUs than this process may use."""


def available_cpus() -> int:
    """Return how many CPUs this process may use.

    Under SLURM, a job given ``--cpus-per-task`` runs on that many CPUs, and
    the scheduler sets ``SLURM_CPUS_PER_TASK`` only when that flag was given.

    Returns:
        The number of CPUs, at least 1.

    Raises:
        CpuBudgetError: If this is a SLURM job without
            ``SLURM_CPUS_PER_TASK``, so the budget would be a guess.
    """
    if "SLURM_JOB_ID" in os.environ:
        if "SLURM_CPUS_PER_TASK" not in os.environ:
            raise CpuBudgetError(
                "SLURM job without SLURM_CPUS_PER_TASK: submit it with "
                "--cpus-per-task"
            )
        return int(os.environ["SLURM_CPUS_PER_TASK"])
    return _process_cpus()


def apply_thread_budget(threads: int, num_workers: int) -> None:
    """Set PyTorch's thread count after checking the CPU budget.

    Args:
        threads: Threads for PyTorch's own operations, at least 1.
        num_workers: ``DataLoader`` worker processes, 0 or more.

    Raises:
        ValueError: If ``threads`` is below 1 or ``num_workers`` below 0.
        CpuBudgetError: If ``threads + num_workers`` exceeds the CPUs this
            process may use.
    """
    if threads < 1 or num_workers < 0:
        raise ValueError(
            f"threads must be >= 1 and num_workers >= 0, got {threads} "
            f"and {num_workers}"
        )
    budget = available_cpus()
    if threads + num_workers > budget:
        raise CpuBudgetError(
            f"{threads} threads + {num_workers} workers exceed the {budget} "
            "CPUs this process may use"
        )
    torch.set_num_threads(threads)
