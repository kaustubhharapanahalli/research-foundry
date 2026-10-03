"""The inference app: the served model, behind the API."""

from django.apps import AppConfig


class InferenceConfig(AppConfig):
    """Configuration for the inference app."""

    name = "apps.inference"
