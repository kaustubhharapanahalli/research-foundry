"""Production settings: every secret from the environment, every check on.

``make lint`` runs ``manage.py check --deploy --fail-level WARNING``
against this module. It refuses to start when ``DJANGO_DEBUG`` is set, so a
debug flag cannot reach a deployment unnoticed.
"""

import os

from django.core.exceptions import ImproperlyConfigured

# pylint: disable-next=wildcard-import,unused-wildcard-import
from .base import *  # noqa: F401,F403
from .base import DATABASES, listed, required

if os.environ.get("DJANGO_DEBUG"):
    raise ImproperlyConfigured(
        "DJANGO_DEBUG is set: production never runs in debug mode."
    )

DEBUG = False
SECRET_KEY = required("DJANGO_SECRET_KEY")
# Earlier keys, comma-separated, still accepted while sessions roll over.
SECRET_KEY_FALLBACKS = [
    key
    for key in os.environ.get("DJANGO_SECRET_KEY_FALLBACKS", "").split(",")
    if key
]
ALLOWED_HOSTS = listed("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = listed("DJANGO_CSRF_TRUSTED_ORIGINS")

# A new dictionary, so importing this module never changes base's.
DATABASES = {
    "default": {
        **DATABASES["default"],
        "PASSWORD": required("POSTGRES_PASSWORD"),
        # psycopg's pool; it requires CONN_MAX_AGE = 0, set in base.
        "OPTIONS": {"pool": True},
    },
}

SECURE_SSL_REDIRECT = True
# The container's own health probe speaks plain HTTP from inside.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Trust X-Forwarded-Proto only behind a proxy that removes any value the
# client sent and sets its own; otherwise a client could claim HTTPS.
if os.environ.get("DJANGO_TRUST_FORWARDED_PROTO") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
