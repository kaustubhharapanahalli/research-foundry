"""Tables and every rule about them.

Rules are declared in ``Meta.constraints``, so Postgres enforces them for
every writer, not only this API. Services call ``validate_constraints()``
to refuse early with a clear message; the database still has the last word.
"""

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower, Now
from pgvector.django import HnswIndex, VectorField

# The size of the vectors your embedding model produces. Changing it later
# needs a migration that rebuilds every stored vector.
EMBEDDING_DIMENSIONS = 384


class Note(models.Model):
    """A short note that belongs to one user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="", db_default="")
    created_at = models.DateTimeField(db_default=Now())
    # Filled by whatever embeds the note; empty until then.
    embedding = VectorField(
        dimensions=EMBEDDING_DIMENSIONS, null=True, blank=True
    )

    class Meta:
        # Postgres's now() is the transaction's start, so ties are common;
        # the id breaks them and keeps every listing in the same order.
        ordering = ["-created_at", "-id"]
        indexes = [
            # Approximate nearest neighbours by cosine distance, the
            # measure similar_notes orders by.
            HnswIndex(
                name="note_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(title__regex=r"\S"),
                name="note_title_not_blank",
                violation_error_message="A note needs a title.",
            ),
            models.UniqueConstraint(
                Lower("title"),
                "owner",
                name="note_title_unique_per_owner",
                violation_error_message="You already have a note with "
                "this title.",
            ),
        ]

    def __str__(self) -> str:
        """Return the note's title."""
        return self.title
