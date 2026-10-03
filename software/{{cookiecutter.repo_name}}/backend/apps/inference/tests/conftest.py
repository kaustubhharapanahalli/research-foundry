"""Weights for the served model, and a fresh predictor for each test."""

from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from pytest_django import Settings

from apps.inference.services import predictor
from ml.model import Scorer
from ml.seeding import seed_everything


@pytest.fixture(autouse=True)
def _fresh_predictor() -> Iterator[None]:
    """Each test loads the model from its own settings."""
    predictor.cache_clear()
    yield
    predictor.cache_clear()


@pytest.fixture(name="weights")
def fixture_weights(tmp_path: Path, settings: Settings) -> Path:
    """Serve a seeded model's weights for this test."""
    seed_everything(0)
    path = tmp_path / "scorer.pt"
    torch.save(Scorer().state_dict(), path)
    settings.ML_WEIGHTS = str(path)
    return path
