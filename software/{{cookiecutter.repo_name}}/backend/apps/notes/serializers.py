"""Request and response shapes; the rules stay in the model."""

from rest_framework import serializers

from apps.notes.models import Note


class NoteSerializer(serializers.ModelSerializer[Note]):
    """A note, as the API reads and writes it."""

    class Meta:
        model = Note
        fields = ["id", "title", "body", "created_at"]
        read_only_fields = ["id", "created_at"]
