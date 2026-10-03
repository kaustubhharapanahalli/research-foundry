"""A dispatched run, end to end: train, then leave both sidecars."""

import json
import time
from pathlib import Path

import pytest
import torch
from torch import nn

from {{ cookiecutter.package_name }} import sidecars
from {{ cookiecutter.package_name }}.seeding import seed_everything


def _run(results: Path, environ: dict[str, str]) -> float:
    """Train a tiny model, witnessing the run even if it fails."""
    config = {"lr": 0.1, "epochs": 3, "seed": 0}
    started = time.monotonic()
    try:
        seed_everything(0)
        model = nn.Linear(2, 1)
        optimiser = torch.optim.SGD(model.parameters(), lr=config["lr"])
        rows = torch.tensor([[0.0, 1.0], [1.0, 0.0]])
        target = torch.tensor([[1.0], [0.0]])
        loss = torch.tensor(0.0)
        for _ in range(int(config["epochs"])):
            optimiser.zero_grad()
            loss = nn.functional.mse_loss(model(rows), target)
            loss.backward()
            optimiser.step()
        sidecars.write_metrics(
            results,
            [{"benchmark": "toy", "metric": "mse", "horizon": 0, "seed": 0,
              "value": float(loss)}],
        )  # fmt: skip
        return float(loss)
    finally:
        sidecars.write_witness(
            results, config, int(time.monotonic() - started), "cpu",
            environ=environ,
        )  # fmt: skip


def test_a_launched_run_leaves_both_sidecars(tmp_path: Path) -> None:
    loss = _run(tmp_path, {"FOUNDRY_RUN_ID": "7"})
    witness = json.loads((tmp_path / "observed.attempt0.json").read_text())
    assert witness["experiment_id"] == 7
    assert witness["device"] == "cpu"
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    assert metrics == [{"benchmark": "toy", "metric": "mse", "horizon": 0,
                        "seed": 0, "value": loss}]  # fmt: skip


def test_guard_a_run_without_an_id_is_not_witnessed(tmp_path: Path) -> None:
    # The training ran; the witness refuses, so the run cannot reach `done`.
    with pytest.raises(sidecars.SidecarError):
        _run(tmp_path, {})
    assert not (tmp_path / "observed.attempt0.json").exists()
