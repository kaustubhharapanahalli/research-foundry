"""Permissions that are about this app's objects."""

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.notes.models import Note


class IsOwner(BasePermission):
    """Allow access to a note only for the user who owns it."""

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        """Return whether the requesting user owns the note.

        Args:
            request: The incoming request.
            view: The view handling it.
            obj: The object the view retrieved.

        Returns:
            ``True`` for the note's owner.
        """
        return isinstance(obj, Note) and obj.owner_id == request.user.pk
