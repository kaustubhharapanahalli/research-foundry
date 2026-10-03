"""The one served model, loaded on first use from the settings."""

from functools import cache

from django.conf import settings

from ml.predictor import Predictor


@cache
def predictor() -> Predictor:
    """Return the process's predictor, loading it the first time.

    Raises:
        ModelUnavailableError: If ``ML_WEIGHTS`` names no weights file.
    """
    return Predictor.load(
        settings.ML_WEIGHTS, settings.ML_DEVICE, settings.ML_THREADS
    )


def score(rows: list[list[float]]) -> list[float]:
    """Score each row with the served model."""
    return predictor().predict(rows)
