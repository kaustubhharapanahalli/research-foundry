"""The note selectors: whose notes, in what order, and nearest first."""

import pytest

from apps.accounts.models import User
from apps.notes.models import EMBEDDING_DIMENSIONS, Note
from apps.notes.selectors import notes_for, similar_notes

pytestmark = pytest.mark.django_db


def test_only_the_owners_notes_are_returned(
    user: User, other_user: User
) -> None:
    mine = Note.objects.create(owner=user, title="Mine")
    Note.objects.create(owner=other_user, title="Theirs")
    assert list(notes_for(user)) == [mine]


def test_order_is_stable_when_timestamps_tie(user: User) -> None:
    # Inside one transaction, Postgres gives every row the same now(), so
    # only the id can order them; the order must not vary between reads.
    notes = [Note.objects.create(owner=user, title=f"N{i}") for i in range(5)]
    expected = list(reversed(notes))
    for _ in range(3):
        assert list(notes_for(user)) == expected


def _axis(index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[index] = 1.0
    return vector


def test_similar_notes_are_ordered_by_cosine_distance(
    user: User, other_user: User
) -> None:
    near = Note.objects.create(owner=user, title="Near", embedding=_axis(0))
    far = Note.objects.create(owner=user, title="Far", embedding=_axis(1))
    Note.objects.create(owner=user, title="Unembedded")
    Note.objects.create(owner=other_user, title="Theirs", embedding=_axis(0))
    query = [0.9, 0.1] + [0.0] * (EMBEDDING_DIMENSIONS - 2)
    assert list(similar_notes(user, query)) == [near, far]
    assert list(similar_notes(user, query, limit=1)) == [near]
