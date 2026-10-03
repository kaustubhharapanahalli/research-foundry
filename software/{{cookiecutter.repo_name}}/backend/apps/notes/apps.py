"""The notes app's configuration."""

from django.apps import AppConfig


class NotesConfig(AppConfig):
    """Notes that belong to one user."""

    name = "apps.notes"
    label = "notes"
