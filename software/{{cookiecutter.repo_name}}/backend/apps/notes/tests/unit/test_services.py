"""create_note saves a valid note and refuses one that breaks a rule."""

from datetime import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.notes.models import Note
from apps.notes.services import create_note

pytestmark = pytest.mark.django_db


def test_create_note_saves_it_with_its_database_timestamp(user: User) -> None:
    note = create_note(owner=user, title="Ideas", body="Write them down.")
    assert note.pk is not None
    assert isinstance(note.created_at, datetime)
    assert Note.objects.get(pk=note.pk).body == "Write them down."


def test_create_note_refuses_a_duplicate_and_saves_nothing(
    user: User,
) -> None:
    create_note(owner=user, title="Ideas")
    with pytest.raises(ValidationError):
        create_note(owner=user, title="ideas")
    assert Note.objects.count() == 1
