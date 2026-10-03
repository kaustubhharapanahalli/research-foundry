"""Markers by folder, and the users and API clients tests share."""

from pathlib import Path

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests unit or functional from their folder; doctests are unit."""
    for item in items:
        parts = Path(str(item.path)).parts
        if "functional" in parts:
            item.add_marker(pytest.mark.functional)
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture(name="user")
def fixture_user(django_user_model: type[User]) -> User:
    """Return a saved user."""
    return django_user_model.objects.create_user(username="ada")


@pytest.fixture(name="other_user")
def fixture_other_user(django_user_model: type[User]) -> User:
    """Return a second saved user, to check that data stays apart."""
    return django_user_model.objects.create_user(username="grace")


@pytest.fixture(name="api")
def fixture_api(user: User) -> APIClient:
    """Return an API client signed in as ``user``."""
    client = APIClient()
    client.force_authenticate(user)
    return client
