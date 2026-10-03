"""The score API end to end: sign-in, validation, the model, its absence."""

from pathlib import Path

import pytest
from pytest_django import Settings
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
SCORE = "/api/inference/score/"


def test_anonymous_requests_are_refused() -> None:
    response = APIClient().post(SCORE, {"rows": [[0, 0, 0, 0]]}, format="json")
    assert response.status_code == 403


def test_rows_are_scored_in_order(api: APIClient, weights: Path) -> None:
    del weights
    rows = [[0, 0, 0, 0], [1, 2, 3, 4]]
    response = api.post(SCORE, {"rows": rows}, format="json")
    assert response.status_code == 200
    scores = response.json()["scores"]
    assert len(scores) == 2
    again = api.post(SCORE, {"rows": rows}, format="json").json()["scores"]
    assert again == scores


@pytest.mark.parametrize(
    "rows", [[], [[1, 2, 3]], [[1, 2, 3, 4, 5]], [["a", 1, 2, 3]]]
)
def test_rows_of_the_wrong_shape_are_a_bad_request(
    api: APIClient, weights: Path, rows: list[list[object]]
) -> None:
    del weights
    assert api.post(SCORE, {"rows": rows}, format="json").status_code == 400


def test_without_weights_the_api_says_so(
    api: APIClient, settings: Settings
) -> None:
    settings.ML_WEIGHTS = ""
    response = api.post(SCORE, {"rows": [[0, 0, 0, 0]]}, format="json")
    assert response.status_code == 503
    assert "ML_WEIGHTS" in response.json()["detail"]
