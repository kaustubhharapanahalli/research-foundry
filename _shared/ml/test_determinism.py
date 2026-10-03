"""The same seed on the same device trains to bit-identical weights."""

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from {{ ml_package }}.device import (
    resolve_device,
)
from {{ ml_package }}.seeding import (
    seed_everything,
    seed_worker,
)


def _train(seed: int, epochs: int = 2) -> list[torch.Tensor]:
    generator = seed_everything(seed)
    device = resolve_device("cpu")
    # Data and model are both drawn after seeding, as a real run must.
    data = TensorDataset(torch.randn(32, 4), torch.randn(32, 1))
    loader = DataLoader(
        data,
        batch_size=8,
        shuffle=True,
        generator=generator,
        worker_init_fn=seed_worker,
    )
    model = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 1))
    model.to(device)
    optimiser = torch.optim.SGD(model.parameters(), lr=0.1)
    for _ in range(epochs):
        for inputs, targets in loader:
            optimiser.zero_grad()
            loss = nn.functional.mse_loss(model(inputs), targets)
            loss.backward()
            optimiser.step()
    return [p.detach().clone() for p in model.parameters()]


def test_same_seed_trains_to_identical_weights() -> None:
    # Zero tolerance: on one device, a seeded deterministic run repeats
    # bit for bit, so torch.equal rather than allclose.
    first, second = _train(seed=0), _train(seed=0)
    assert all(torch.equal(a, b) for a, b in zip(first, second, strict=True))


def test_different_seeds_train_to_different_weights() -> None:
    first, second = _train(seed=0), _train(seed=1)
    assert not all(
        torch.equal(a, b) for a, b in zip(first, second, strict=True)
    )
