"""The WSGI and ASGI applications load, and manage.py runs a command."""

import runpy
import sys
from pathlib import Path

import pytest

MANAGE = Path(__file__).resolve().parents[4] / "manage.py"


def test_wsgi_application_loads() -> None:
    # pylint: disable-next=import-outside-toplevel
    from config.wsgi import application

    assert callable(application)


def test_asgi_application_loads() -> None:
    # pylint: disable-next=import-outside-toplevel
    from config.asgi import application

    assert callable(application)


def test_manage_py_runs_the_system_checks(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["manage.py", "check"])
    runpy.run_path(str(MANAGE), run_name="__main__")
    assert "no issues" in capsys.readouterr().out
