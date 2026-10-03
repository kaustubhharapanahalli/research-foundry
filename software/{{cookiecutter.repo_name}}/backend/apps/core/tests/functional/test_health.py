"""The health check answers anyone, and only when the database does."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_answers_without_credentials() -> None:
    response = APIClient().get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
