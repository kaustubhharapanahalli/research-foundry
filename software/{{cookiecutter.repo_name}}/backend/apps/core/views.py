"""The health check, the one view open to anyone."""

from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(
    responses=inline_serializer("Health", {"status": serializers.CharField()})
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request: Request) -> Response:  # pylint: disable=unused-argument
    """Answer that the process is up and the database accepts connections.

    Args:
        request: The incoming request; it needs no credentials.

    Returns:
        ``{"status": "ok"}``. A database that is down raises, and the
        server answers 500.
    """
    connection.ensure_connection()
    return Response({"status": "ok"})
