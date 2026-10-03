"""Reads: which notes a user may see, in a stable order."""

from collections.abc import Sequence

from django.db.models import QuerySet
from pgvector.django import CosineDistance

from apps.accounts.models import User
from apps.notes.models import Note


def notes_for(user: User) -> QuerySet[Note]:
    """Return the notes a user owns, newest first.

    List views filter here, because DRF applies object permissions to
    single objects only, never to lists.

    Args:
        user: The signed-in user.

    Returns:
        Their notes, in the model's ordering.
    """
    return Note.objects.filter(owner=user)


def similar_notes(
    user: User, vector: Sequence[float], limit: int = 5
) -> QuerySet[Note]:
    """Return a user's notes nearest to a vector, nearest first.

    Notes without an embedding are left out. Postgres answers through the
    HNSW index on ``Note.embedding``, so the order is approximate on large
    tables.

    Args:
        user: The signed-in user; only their notes are searched.
        vector: A query embedding, ``EMBEDDING_DIMENSIONS`` long.
        limit: How many notes to return at most.

    Returns:
        Up to ``limit`` notes, by increasing cosine distance.
    """
    return (
        notes_for(user)
        .filter(embedding__isnull=False)
        .order_by(CosineDistance("embedding", vector), "id")[:limit]
    )
