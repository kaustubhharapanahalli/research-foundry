"""Seed every random number generator a run uses, from one integer.

PyTorch does not promise identical results across releases, platforms, or
CPU and GPU. Within one machine and one environment, a seeded run with
deterministic algorithms on repeats exactly.

Example:
    >>> generator = seed_everything(7)
    >>> generator.initial_seed()
    7
"""

import os
import random

import numpy as np
import torch

# NVIDIA's cuBLAS "Results reproducibility" section: a fixed workspace size
# keeps cuBLAS deterministic when several streams are in use.
CUBLAS_WORKSPACE_CONFIG = ":4096:8"
_MAX_SEED = 2**32


def seed_everything(
    seed: int, *, deterministic: bool = True
) -> torch.Generator:
    """Seed Python, NumPy and PyTorch, and return a generator for loaders.

    Call it once, before the model or any data is created.

    Args:
        seed: The run's seed, from 0 to 2**32 - 1.
        deterministic: Make PyTorch use deterministic algorithms and raise
            on any operation that has none, instead of only warning.

    Returns:
        A ``torch.Generator`` seeded with ``seed``, to pass as a
        ``DataLoader``'s ``generator``.

    Raises:
        ValueError: If ``seed`` is outside 0 to 2**32 - 1, which NumPy's
            global generator cannot accept.
    """
    if not 0 <= seed < _MAX_SEED:
        raise ValueError(f"seed must be in [0, 2**32), got {seed}")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if deterministic:
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = CUBLAS_WORKSPACE_CONFIG
        # warn_only=False: a warning would let fused attention keep its
        # non-deterministic paths.
        torch.use_deterministic_algorithms(True, warn_only=False)
        torch.backends.cudnn.benchmark = False
    generator = torch.Generator()
    generator.manual_seed(seed)
    return generator


def seed_worker(worker_id: int) -> None:  # pylint: disable=unused-argument
    """Seed Python and NumPy inside a ``DataLoader`` worker.

    PyTorch seeds each worker's torch generator, but other libraries' seeds
    may repeat across workers. Pass this as ``worker_init_fn``.

    Args:
        worker_id: The worker's index, which ``DataLoader`` passes in.
    """
    worker_seed = torch.initial_seed() % _MAX_SEED
    random.seed(worker_seed)
    np.random.seed(worker_seed)
