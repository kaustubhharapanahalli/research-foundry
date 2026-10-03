"""The served model is loaded once per process, from the settings."""

from pathlib import Path

import pytest
from pytest_django import Settings

from apps.inference.services import predictor, score
from ml.predictor import ModelUnavailableError


def test_the_predictor_is_loaded_once(weights: Path) -> None:
    del weights
    assert predictor() is predictor()


def test_scores_come_from_the_served_model(weights: Path) -> None:
    del weights
    assert len(score([[0.0, 0.0, 0.0, 0.0]])) == 1


def test_no_weights_means_no_model(settings: Settings) -> None:
    settings.ML_WEIGHTS = ""
    with pytest.raises(ModelUnavailableError):
        predictor()
