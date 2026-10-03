"""NoteViewSet refuses to act for a request without a user."""

from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotAuthenticated

from apps.notes.views import NoteViewSet


def test_an_anonymous_request_gets_no_queryset() -> None:
    # IsAuthenticated refuses first in practice; this is the second guard.
    view = NoteViewSet()
    view.request = Mock(user=AnonymousUser())
    with pytest.raises(NotAuthenticated):
        view.get_queryset()
