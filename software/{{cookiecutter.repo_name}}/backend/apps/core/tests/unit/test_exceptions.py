"""The exception handler turns rule violations into client errors."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import NotFound

from apps.core.exceptions import exception_handler


def test_integrity_error_is_a_conflict() -> None:
    response = exception_handler(IntegrityError("duplicate key"), {})
    assert response is not None
    assert response.status_code == 409


def test_field_validation_error_is_a_bad_request() -> None:
    error = DjangoValidationError({"title": ["A note needs a title."]})
    response = exception_handler(error, {})
    assert response is not None
    assert response.status_code == 400
    assert response.data == {"title": ["A note needs a title."]}


def test_plain_validation_error_is_a_bad_request() -> None:
    error = DjangoValidationError("You already have a note with this title.")
    response = exception_handler(error, {})
    assert response is not None
    assert response.status_code == 400
    assert response.data == ["You already have a note with this title."]


def test_drf_exceptions_keep_drf_handling() -> None:
    response = exception_handler(NotFound(), {})
    assert response is not None
    assert response.status_code == 404


def test_unknown_exceptions_are_left_to_django() -> None:
    assert exception_handler(RuntimeError("bug"), {}) is None
