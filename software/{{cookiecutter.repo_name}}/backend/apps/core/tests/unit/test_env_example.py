"""Every setting the code reads from the environment is in .env.example.

The file is the one list an operator reads before deploying, so a setting
missing from it is a setting nobody knows to set.
"""

import re
from pathlib import Path

from django.conf import settings

ROOT = Path(settings.BASE_DIR).parent
# os.environ.get("X" ...), required("X"), listed("X"), requiredEnv("X")
READS = re.compile(
    r"(?:environ\.get|required|listed|requiredEnv)"
    r"""\(\s*["']([A-Z][A-Z0-9_]*)"""
)
# ${X}, ${X:-default}, ${X:?message} in compose.yaml
INTERPOLATED = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
# {$X} and {$X:default} in the proxy's Caddyfile
CADDY = re.compile(r"\{\$([A-Z][A-Z0-9_]*)")


def _sources() -> list[Path]:
    settings_dir = ROOT / "backend" / "config" / "settings"
    frontend_server = ROOT / "frontend" / "lib" / "server"
    return [*settings_dir.glob("*.py"), *frontend_server.glob("*.ts")]


def _read_names() -> set[str]:
    names = set()
    for path in _sources():
        names |= set(READS.findall(path.read_text(encoding="utf-8")))
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    names |= set(INTERPOLATED.findall(compose))
    caddyfile = ROOT / "proxy" / "Caddyfile"
    if caddyfile.exists():
        names |= set(CADDY.findall(caddyfile.read_text(encoding="utf-8")))
    return names


def _listed_names() -> set[str]:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    return set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]*)=", text, re.MULTILINE))


def test_the_scan_finds_the_settings_it_must() -> None:
    # Guards the scan itself: a broken pattern would find nothing and pass.
    assert {"DJANGO_SECRET_KEY", "POSTGRES_PASSWORD"} <= _read_names()


def test_every_setting_read_is_listed() -> None:
    missing = _read_names() - _listed_names()
    assert not missing, f"add to .env.example: {sorted(missing)}"


def test_nothing_listed_is_unread() -> None:
    stale = _listed_names() - _read_names()
    assert not stale, f"remove from .env.example: {sorted(stale)}"
