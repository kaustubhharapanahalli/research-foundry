"""The score endpoint: validate, predict, or say the model is unavailable."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inference.serializers import (
    ScoreRequestSerializer,
    ScoreResponseSerializer,
)
from apps.inference.services import score
from ml.predictor import ModelUnavailableError


class ScoreView(APIView):
    """Score rows of features with the served model."""

    @extend_schema(
        request=ScoreRequestSerializer,
        responses={
            200: ScoreResponseSerializer,
            503: OpenApiResponse(description="No model weights are served."),
        },
    )
    def post(self, request: Request) -> Response:
        """Return one score per row, or 503 when no model is served."""
        serializer = ScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            scores = score(serializer.validated_data["rows"])
        except ModelUnavailableError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"scores": scores})
