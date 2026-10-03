"""Writes: one unit of work each, checked before the database checks it."""

from apps.accounts.models import User
from apps.notes.models import Note


def create_note(
    *,
    owner: User,
    title: str,
    body: str = "",
) -> Note:
    """Create a note, refusing one that breaks a rule.

    Args:
        owner: The user the note belongs to.
        title: The note's title; not blank, and unique for this owner
            whatever its case.
        body: The note's text.

    Returns:
        The saved note.

    Raises:
        django.core.exceptions.ValidationError: If a rule in
            ``Note.Meta.constraints`` is broken. The API answers 400. A
            concurrent write that slips past is refused by Postgres instead,
            and the API answers 409.
    """
    note = Note(owner=owner, title=title, body=body)
    note.validate_constraints()
    note.save()
    note.refresh_from_db(fields=["created_at"])
    return note
