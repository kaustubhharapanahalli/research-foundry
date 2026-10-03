"""The note's rules, checked early in Python and enforced by Postgres."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.notes.models import Note

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_a_blank_title_is_refused(title: str, user: User) -> None:
    with pytest.raises(ValidationError, match="A note needs a title"):
        Note(owner=user, title=title).validate_constraints()


def test_a_title_repeats_for_no_owner_whatever_its_case(user: User) -> None:
    Note.objects.create(owner=user, title="Ideas")
    with pytest.raises(ValidationError, match="already have a note"):
        Note(owner=user, title="IDEAS").validate_constraints()


def test_two_owners_may_use_one_title(user: User, other_user: User) -> None:
    Note.objects.create(owner=user, title="Ideas")
    Note(owner=other_user, title="Ideas").validate_constraints()


@pytest.mark.parametrize(
    ("first", "second"), [("Ideas", "ideas"), ("", None), (" ", None)]
)
def test_postgres_refuses_what_validation_would(
    first: str, second: str | None, user: User
) -> None:
    # Skipping validate_constraints() must not get a bad row in.
    with pytest.raises(IntegrityError), transaction.atomic():
        Note.objects.create(owner=user, title=first)
        if second is not None:
            Note.objects.create(owner=user, title=second)


def test_a_note_reads_as_its_title(user: User) -> None:
    assert str(Note(owner=user, title="Ideas")) == "Ideas"
