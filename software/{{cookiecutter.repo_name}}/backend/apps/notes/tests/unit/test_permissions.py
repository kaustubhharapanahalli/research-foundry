"""IsOwner admits a note's owner and nobody else."""

from unittest.mock import Mock

import pytest

from apps.accounts.models import User
from apps.notes.models import Note
from apps.notes.permissions import IsOwner

pytestmark = pytest.mark.django_db


def _allowed(user: User, obj: object) -> bool:
    return IsOwner().has_object_permission(Mock(user=user), Mock(), obj)


def test_the_owner_is_allowed(user: User) -> None:
    assert _allowed(user, Note.objects.create(owner=user, title="Mine"))


def test_another_user_is_refused(user: User, other_user: User) -> None:
    note = Note.objects.create(owner=user, title="Mine")
    assert not _allowed(other_user, note)


def test_an_object_that_is_not_a_note_is_refused(user: User) -> None:
    assert not _allowed(user, object())
