"""Routing, authentication and permissions; writes go through services."""

from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from apps.accounts.models import User
from apps.notes.models import Note
from apps.notes.permissions import IsOwner
from apps.notes.selectors import notes_for
from apps.notes.serializers import NoteSerializer
from apps.notes.services import create_note


class NoteViewSet(  # pylint: disable=too-many-ancestors
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet[Note],
):
    """List, create, read and delete the signed-in user's notes."""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def _user(self) -> User:
        user = self.request.user
        if not isinstance(user, User):
            raise NotAuthenticated()
        return user

    def get_queryset(self) -> QuerySet[Note]:
        """Return only the user's own notes, for lists and lookups alike."""
        if getattr(self, "swagger_fake_view", False):
            # Schema generation runs without a user.
            return Note.objects.none()
        return notes_for(self._user())

    def perform_create(self, serializer: BaseSerializer[Note]) -> None:
        """Create the note through its service, for the signed-in user."""
        serializer.instance = create_note(
            owner=self._user(), **serializer.validated_data
        )
