"""Development settings: debug on, for a laptop only."""

import os

# pylint: disable-next=wildcard-import,unused-wildcard-import
from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-development-only-never-deployed"
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
