"""The notes app's admin pages."""

from django.contrib import admin

from apps.notes.models import Note


# ModelAdmin is subscripted at runtime by django_stubs_ext (see
# config/settings/base.py), which pylint cannot see.
@admin.register(Note)
class NoteAdmin(  # pylint: disable=too-few-public-methods
    admin.ModelAdmin[Note]  # pylint: disable=unsubscriptable-object
):
    """Notes, searchable by title."""

    list_display = ["title", "owner", "created_at"]
    search_fields = ["title"]
