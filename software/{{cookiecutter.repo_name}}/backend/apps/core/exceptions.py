"""The API's exception handler: DRF's, plus the database's own refusals."""

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback


def exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    """Turn rule violations into client errors instead of server errors.

    A constraint that Postgres enforces raises ``IntegrityError``, which
    becomes 409 Conflict. A Django ``ValidationError``, such as one from
    ``Model.validate_constraints()``, becomes 400 with its messages.
    Everything else goes to DRF's own handler.

    Args:
        exc: The exception a view raised.
        context: DRF's context for the view.

    Returns:
        The response to send, or ``None`` to let Django handle the error.
    """
    if isinstance(exc, IntegrityError):
        # The request's transaction is broken; roll it back, as DRF does
        # for its own exceptions.
        set_rollback()
        return Response(
            {"detail": "The request conflicts with existing data."},
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(
            exc.message_dict if hasattr(exc, "error_dict") else exc.messages
        )
    return drf_exception_handler(exc, context)
