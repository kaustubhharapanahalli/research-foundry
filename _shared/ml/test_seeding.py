import os
import random

import numpy as np
import pytest
import torch

from {{ ml_package }}.seeding import (
    CUBLAS_WORKSPACE_CONFIG,
    seed_everything,
    seed_worker,
)


def _draws() -> tuple[float, float, torch.Tensor]:
    return random.random(), float(np.random.rand()), torch.rand(3)


def test_same_seed_gives_same_draws() -> None:
    seed_everything(11)
    first = _draws()
    seed_everything(11)
    second = _draws()
    assert first[:2] == second[:2]
    assert torch.equal(first[2], second[2])


def test_different_seeds_give_different_draws() -> None:
    seed_everything(1)
    first = _draws()
    seed_everything(2)
    assert not torch.equal(first[2], _draws()[2])


def test_returned_generator_is_seeded() -> None:
    assert seed_everything(5).initial_seed() == 5


def test_deterministic_mode_is_switched_on() -> None:
    seed_everything(3, deterministic=True)
    assert torch.are_deterministic_algorithms_enabled()
    assert torch.is_deterministic_algorithms_warn_only_enabled() is False
    assert torch.backends.cudnn.benchmark is False
    assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == CUBLAS_WORKSPACE_CONFIG


def test_deterministic_mode_can_be_left_off() -> None:
    torch.use_deterministic_algorithms(False)
    seed_everything(3, deterministic=False)
    assert not torch.are_deterministic_algorithms_enabled()


@pytest.mark.parametrize("seed", [-1, 2**32])
def test_out_of_range_seed_is_refused(seed: int) -> None:
    with pytest.raises(ValueError, match="seed must be"):
        seed_everything(seed)


def test_worker_seed_follows_torch_initial_seed() -> None:
    torch.manual_seed(1234)
    seed_worker(0)
    after_worker = random.random(), float(np.random.rand())
    random.seed(1234)
    np.random.seed(1234)
    assert after_worker == (random.random(), float(np.random.rand()))
