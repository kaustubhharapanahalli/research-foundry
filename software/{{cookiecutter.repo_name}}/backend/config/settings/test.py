"""Settings for pytest: a real Postgres, fast password hashing."""

# pylint: disable-next=wildcard-import,unused-wildcard-import
from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "tests-only-not-a-secret"
ALLOWED_HOSTS = ["testserver", "localhost"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# collectstatic does not run for tests: WhiteNoise looks files up per
# request instead of scanning a missing folder, and no manifest is needed.
WHITENOISE_AUTOREFRESH = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
