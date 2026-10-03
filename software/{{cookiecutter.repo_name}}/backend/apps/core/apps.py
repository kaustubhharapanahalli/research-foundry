"""The core app's configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Platform pieces every app shares; it owns no models."""

    name = "apps.core"
    label = "core"
