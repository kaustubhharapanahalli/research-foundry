"""Settings every environment shares.

``dev``, ``prod`` and ``test`` import this module and set what differs:
``DEBUG``, ``SECRET_KEY``, ``ALLOWED_HOSTS`` and the security settings.
Values come from plain environment variables.
"""

import os
from pathlib import Path
from typing import Any

import django_stubs_ext
from django.core.exceptions import ImproperlyConfigured

# Lets Django's generic classes, such as ModelAdmin[Note], be subscripted
# at runtime as the type checker requires. DRF's classes already can be.
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def required(name: str) -> str:
    """Return an environment variable, refusing to start without it.

    Args:
        name: The variable's name.

    Returns:
        Its value.

    Raises:
        ImproperlyConfigured: If the variable is unset or empty.
    """
    value = os.environ.get(name, "")
    if not value:
        raise ImproperlyConfigured(f"{name} must be set in the environment.")
    return value


def listed(name: str) -> list[str]:
    """Return a required, comma-separated environment variable as a list.

    Args:
        name: The variable's name.

    Returns:
        Its items, without surrounding spaces or empty items.
    """
    return [item.strip() for item in required(name).split(",") if item]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Postgres-only fields, indexes and constraints (HnswIndex needs it).
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.notes",
{%- if cookiecutter.ml_pytorch == "yes" %}
    "apps.inference",
{%- endif %}
]
# A custom user model from the first migration: Django cannot switch to one
# later without rewriting every table that points at users.
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Postgres only, including for tests: SQLite ignores select_for_update()
# and enforces constraints differently.
DATABASES: dict[str, dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "{{ cookiecutter.db_port }}"),
        "NAME": os.environ.get("POSTGRES_DB", "app"),
        "USER": os.environ.get("POSTGRES_USER", "app"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "dev-only-password"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 0,
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"django.contrib.auth.password_validation.{name}"}
    for name in (
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    )
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # DRF's own default is AllowAny. Every view is closed unless it opens
    # itself, as the health check does.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Off by default in DRF; an unpaginated list grows without bound.
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.exception_handler",
    # The number of proxies in front of the app, so throttling and logs see
    # the client's address rather than the proxy's.
    "NUM_PROXIES": int(os.environ.get("DJANGO_NUM_PROXIES", "0")),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "{{ cookiecutter.project_name }}",
    "DESCRIPTION": "{{ cookiecutter.description }}",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
{%- if cookiecutter.ml_pytorch == "yes" %}

# The served model (apps.inference). With no weights file the score API
# answers 503: an untrained model is never served in its place.
ML_WEIGHTS = os.environ.get("ML_WEIGHTS", "")
ML_DEVICE = os.environ.get("ML_DEVICE", "cpu")
# PyTorch threads per web worker; each worker would otherwise take every CPU.
ML_THREADS = int(os.environ.get("ML_THREADS", "1"))
{%- endif %}
