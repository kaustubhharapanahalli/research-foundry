"""The project's own user model is the one Django uses."""

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import User


def test_the_custom_user_model_is_active() -> None:
    assert get_user_model() is User


@pytest.mark.django_db
def test_a_user_can_be_created_and_signs_in_with_a_password() -> None:
    user = User.objects.create_user(username="ada", password="a long one")
    assert user.check_password("a long one")
    assert not user.is_staff
