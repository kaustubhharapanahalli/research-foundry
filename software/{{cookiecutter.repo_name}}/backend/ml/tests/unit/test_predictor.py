"""The predictor: weights or an error, the device asked for, no gradients."""

from pathlib import Path

import pytest
import torch

from ml.device import DeviceUnavailableError
from ml.model import FEATURES, Scorer
from ml.predictor import ModelUnavailableError, Predictor
from ml.seeding import seed_everything


@pytest.fixture(name="weights")
def fixture_weights(tmp_path: Path) -> Path:
    """Save a seeded model's weights and return their path."""
    seed_everything(0)
    path = tmp_path / "scorer.pt"
    torch.save(Scorer().state_dict(), path)
    return path


def test_the_loaded_model_scores_each_row(weights: Path) -> None:
    predictor = Predictor.load(str(weights), "cpu", 1)
    scores = predictor.predict([[0.0] * FEATURES, [1.0] * FEATURES])
    assert len(scores) == 2
    assert all(0.0 < score < 1.0 for score in scores)


def test_the_same_rows_score_the_same(weights: Path) -> None:
    rows = [[0.5, -1.0, 2.0, 0.25]]
    first = Predictor.load(str(weights), "cpu", 1).predict(rows)
    assert Predictor.load(str(weights), "cpu", 1).predict(rows) == first


def test_the_model_is_in_evaluation_mode(weights: Path) -> None:
    assert not Predictor.load(str(weights), "cpu", 1).model.training


@pytest.mark.parametrize("given", ["", "missing.pt"])
def test_no_weights_is_an_error_not_an_untrained_model(
    given: str, tmp_path: Path
) -> None:
    weights = str(tmp_path / given) if given else ""
    with pytest.raises(ModelUnavailableError):
        Predictor.load(weights, "cpu", 1)


def test_a_missing_device_is_an_error(weights: Path) -> None:
    with pytest.raises(DeviceUnavailableError):
        Predictor.load(str(weights), "cuda:99", 1)


def test_weights_that_are_not_tensors_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "pickled.pt"
    torch.save({"linear.weight": object()}, path)
    with pytest.raises(Exception):  # noqa: B017 - torch's own unpickling error
        Predictor.load(str(path), "cpu", 1)
