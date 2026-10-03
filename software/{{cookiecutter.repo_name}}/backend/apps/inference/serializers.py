"""The score request and its answer."""

from rest_framework import serializers

from ml.model import FEATURES

#: The most rows one request may score.
MAX_ROWS = 256

# These only validate and describe; nothing is saved, so DRF's abstract
# create and update are never called.
# pylint: disable=abstract-method


class ScoreRequestSerializer(serializers.Serializer[dict[str, object]]):
    """Rows of exactly :data:`ml.model.FEATURES` numbers each."""

    rows = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField(),
            min_length=FEATURES,
            max_length=FEATURES,
        ),
        min_length=1,
        max_length=MAX_ROWS,
    )


class ScoreResponseSerializer(serializers.Serializer[dict[str, object]]):
    """One score per row, in the order the rows came."""

    scores = serializers.ListField(child=serializers.FloatField())
