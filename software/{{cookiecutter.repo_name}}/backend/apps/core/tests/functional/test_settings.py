"""Production settings refuse to start without their secrets."""

import importlib
import sys
from collections.abc import Callable, Iterator
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured

PROD = "config.settings.prod"
PROD_ENV = {
    "DJANGO_SECRET_KEY": "x" * 60,
    "DJANGO_ALLOWED_HOSTS": "example.org, api.example.org",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://example.org",
    "POSTGRES_PASSWORD": "from-the-environment",
}


Loader = Callable[[], ModuleType]


@pytest.fixture(name="load_prod")
def fixture_load_prod(monkeypatch: pytest.MonkeyPatch) -> Iterator[Loader]:
    """Yield a loader for prod.py under a complete production environment.

    Each call imports the module afresh, so a test can change the
    environment first. The module is removed again afterwards.
    """
    for name, value in PROD_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.delenv("DJANGO_TRUST_FORWARDED_PROTO", raising=False)

    def load() -> ModuleType:
        sys.modules.pop(PROD, None)
        return importlib.import_module(PROD)

    yield load
    sys.modules.pop(PROD, None)


def test_production_reads_its_settings_from_the_environment(
    load_prod: Loader,
) -> None:
    prod = load_prod()
    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["example.org", "api.example.org"]
    assert prod.DATABASES["default"]["PASSWORD"] == "from-the-environment"
    assert prod.SECURE_HSTS_SECONDS >= 31_536_000
    assert not hasattr(prod, "SECURE_PROXY_SSL_HEADER")


@pytest.mark.parametrize("name", sorted(PROD_ENV))
def test_production_refuses_a_missing_secret(
    name: str, load_prod: Loader, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(name)
    with pytest.raises(ImproperlyConfigured, match=name):
        load_prod()


def test_production_refuses_debug(
    load_prod: Loader, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DJANGO_DEBUG", "1")
    with pytest.raises(ImproperlyConfigured, match="DJANGO_DEBUG"):
        load_prod()


def test_forwarded_proto_is_trusted_only_when_asked(
    load_prod: Loader, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DJANGO_TRUST_FORWARDED_PROTO", "1")
    prod = load_prod()
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_production_leaves_the_shared_settings_alone(
    load_prod: Loader,
) -> None:
    base = importlib.import_module("config.settings.base")
    prod = load_prod()
    assert prod.DATABASES["default"] is not base.DATABASES["default"]
    assert "pool" not in base.DATABASES["default"].get("OPTIONS", {})


def test_development_settings_load() -> None:
    dev = importlib.import_module("config.settings.dev")
    assert dev.DEBUG is True
