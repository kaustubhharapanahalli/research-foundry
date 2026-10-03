"""Template pins are discovered and compared without real registry calls."""

from __future__ import annotations

import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
from tools import check_pins


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_each_template_pin_kind_is_found(tmp_path: Path) -> None:
    project = tmp_path / "software" / "{{cookiecutter.repo_name}}"
    pyproject = (
        'name = "{{ cookiecutter.repo_name }}"\n'
        'dependencies = ["django>=6.1.1"]\n'
    )
    _write(
        project / "pyproject.toml",
        pyproject,
    )
    _write(
        project / "compose.yaml",
        "name: {{ cookiecutter.repo_name }}\n"
        "image: caddy:2.11.4-alpine@sha256:abc\n",
    )
    _write(
        project / "frontend/Dockerfile",
        "FROM node:26.10.0-slim@sha256:def\n",
    )
    _write(
        project / "frontend/package.json",
        '{"name":"{{ cookiecutter.repo_name }}",'
        '"dependencies":{"react":"19.3.0"},'
        '"devDependencies":{"vite":"8.0.0"},'
        '"packageManager":"pnpm@11.0.0",'
        '"devEngines":{"runtime":{"name":"node","version":"26.10.0"},'
        '"packageManager":{"name":"pnpm","version":"11.0.0"},'
        '"ignored":"not a mapping"}}',
    )
    _write(project / "static/package.json", '{"name":"plain-json"}')
    _write(
        tmp_path / "_shared/python/pre-commit-config.yaml",
        "repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n"
        "    rev: 3e8a870 # frozen: v6.0.0\n",
    )

    pins = check_pins.collect_pins(tmp_path)

    assert {pin.kind for pin in pins} == {"pypi", "npm", "docker", "github"}
    assert {(pin.name, pin.current) for pin in pins} >= {
        ("django", "6.1.1"),
        ("react", "19.3.0"),
        ("vite", "8.0.0"),
        ("pnpm", "11.0.0"),
        ("caddy", "2.11.4-alpine"),
        ("node", "26.10.0-slim"),
        ("node", "26.10.0"),
        ("pre-commit/pre-commit-hooks", "v6.0.0"),
    }


def test_up_to_date_pin_is_reported(tmp_path: Path) -> None:
    pyproject = (
        'name = "{{ cookiecutter.repo_name }}"\n'
        'dependencies = ["numpy>=2.5.3"]\n'
    )
    _write(
        tmp_path / "methodology/{{cookiecutter.repo_name}}/pyproject.toml",
        pyproject,
    )

    report = check_pins.render_report(
        tmp_path, lambda url: {"info": {"version": "2.5.3"}}
    )

    assert "| `numpy` |" in report
    assert "| 2.5.3 | 2.5.3 |" in report


def test_stale_pin_lists_newest_release(tmp_path: Path) -> None:
    pyproject = (
        'name = "{{ cookiecutter.repo_name }}"\n'
        'dependencies = ["numpy>=2.5.3"]\n'
    )
    _write(
        tmp_path / "methodology/{{cookiecutter.repo_name}}/pyproject.toml",
        pyproject,
    )

    report = check_pins.render_report(
        tmp_path, lambda url: {"info": {"version": "2.6.0"}}
    )

    assert "| 2.5.3 | 2.6.0 |" in report


def test_held_majors_list_each_blockers_version_and_requirement(
    tmp_path: Path,
) -> None:
    responses: dict[str, dict[str, object]] = {
        "vitest-monocart-coverage": {
            "version": "4.0.2",
            "dependencies": {"@vitest/coverage-v8": "^4.1.2"},
        },
        "typescript-eslint": {
            "version": "8.71.0",
            "peerDependencies": {"typescript": ">=4.8.4 <6.1.0"},
        },
        "eslint-plugin-import": {
            "version": "2.32.0",
            "peerDependencies": {
                "eslint": "^2 || ^3 || ^4 || ^5 || ^6 || ^7 || ^8 || ^9"
            },
        },
        "eslint-plugin-jsx-a11y": {
            "version": "6.10.2",
            "peerDependencies": {
                "eslint": "^3 || ^4 || ^5 || ^6 || ^7 || ^8 || ^9"
            },
        },
    }

    def fetch(url: str) -> dict[str, object]:
        blocker = url.removeprefix("https://registry.npmjs.org/").removesuffix(
            "/latest"
        )
        return responses[blocker]

    report = check_pins.render_report(tmp_path, fetch)

    assert "## Held majors (ADR 0003)" in report
    assert report.count("| `vitest`, `@vitest/coverage-v8` |") == 1
    assert (
        "| `vitest-monocart-coverage` | 4.0.2 | "
        "`@vitest/coverage-v8` `^4.1.2` |" in report
    )
    assert (
        "| `typescript-eslint` | 8.71.0 | `typescript` `>=4.8.4 <6.1.0` |"
        in report
    )
    assert (
        "| `eslint-plugin-import` | 2.32.0 | `eslint` "
        "`^2 \\|\\| ^3 \\|\\| ^4 \\|\\| ^5 \\|\\| ^6 "
        "\\|\\| ^7 \\|\\| ^8 \\|\\| ^9` |" in report
    )
    assert (
        "| `eslint-plugin-jsx-a11y` | 6.10.2 | `eslint` "
        "`^3 \\|\\| ^4 \\|\\| ^5 \\|\\| ^6 \\|\\| ^7 "
        "\\|\\| ^8 \\|\\| ^9` |" in report
    )


def test_held_major_without_a_declared_range_is_reported(
    tmp_path: Path,
) -> None:
    def fetch(url: str) -> dict[str, object]:
        response: dict[str, object] = {
            "version": "1.2.3",
            "peerDependencies": {"typescript": "<7", "eslint": "^9"},
            "dependencies": {"@vitest/coverage-v8": "^4"},
        }
        if "typescript-eslint" in url:
            response.pop("peerDependencies")
        return response

    report = check_pins.render_report(tmp_path, fetch)

    assert (
        "| `typescript` | `typescript-eslint` | 1.2.3 | "
        "`typescript` `not declared` |" in report
    )


def test_held_major_fetch_error_does_not_hide_other_holds(
    tmp_path: Path,
) -> None:
    def fetch(url: str) -> dict[str, object]:
        if "eslint-plugin-import" in url:
            raise OSError("registry unavailable")
        return {
            "version": "1.2.3",
            "peerDependencies": {"typescript": "<7", "eslint": "^9"},
            "dependencies": {"@vitest/coverage-v8": "^4"},
        }

    report = check_pins.render_report(tmp_path, fetch)

    import_row = next(
        line
        for line in report.splitlines()
        if "`eslint-plugin-import`" in line
    )
    assert import_row.count("ERROR: registry unavailable") == 2
    assert "| `eslint-plugin-jsx-a11y` | 1.2.3 | `eslint` `^9` |" in report


def test_registry_error_is_reported_instead_of_crashing(
    tmp_path: Path,
) -> None:
    pyproject = (
        'name = "{{ cookiecutter.repo_name }}"\n'
        'dependencies = ["numpy>=2.5.3"]\n'
    )
    _write(
        tmp_path / "methodology/{{cookiecutter.repo_name}}/pyproject.toml",
        pyproject,
    )

    def unavailable(url: str) -> dict[str, object]:
        raise OSError(f"registry unavailable: {url}")

    report = check_pins.render_report(tmp_path, unavailable)

    assert "ERROR: registry unavailable" in report


def test_registry_responses_are_fetched_and_rendered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "software" / "{{cookiecutter.repo_name}}"
    _write(
        project / "pyproject.toml",
        'dependencies = ["demo.package>=1.0.0"]\n',
    )
    _write(
        project / "package.json",
        '{"name":"{{ cookiecutter.repo_name }}",'
        '"dependencies":{"@scope/pkg":"2.0.0"}}',
    )
    _write(
        project / "compose.yaml",
        "image: caddy:2.9-alpine\nimage: ghcr.io/example/tool:v3.0.0\n",
    )
    _write(
        tmp_path / "_shared/python/pre-commit-config.yaml",
        "repos:\n  - repo: https://github.com/example/hooks.git\n"
        "    rev: v4.0.0\n",
    )
    responses = {
        "pypi.org": {"info": {"version": "1.1.0"}},
        "registry.npmjs.org": {"version": "2.1.0"},
        "hub.docker.com": {
            "results": [
                {"name": "latest"},
                {"name": "2.10-alpine"},
                {"name": "2.11"},
                {"other": "ignored"},
                "ignored",
            ]
        },
        "api.github.com/repos/example/tool": {"tag_name": "v3.1.0"},
        "api.github.com/repos/example/hooks": {"tag_name": "v4.1.0"},
    }
    requested: list[str] = []

    def fake_urlopen(url: str, timeout: int) -> io.BytesIO:
        assert timeout == 30
        requested.append(url)
        payload = next(value for key, value in responses.items() if key in url)
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(check_pins, "urlopen", fake_urlopen)

    report = check_pins.render_report(tmp_path)

    assert "| 1.0.0 | 1.1.0 |" in report
    assert "| 2.0.0 | 2.1.0 |" in report
    assert "| 2.9-alpine | 2.10-alpine |" in report
    assert "| v3.0.0 | v3.1.0 |" in report
    assert "| v4.0.0 | v4.1.0 |" in report
    assert any("%40scope%2Fpkg" in url for url in requested)


def test_http_error_from_registry_is_written_in_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(
        tmp_path
        / "methodology"
        / "{{cookiecutter.repo_name}}"
        / "pyproject.toml",
        'dependencies = ["numpy>=2.5.3"]\n',
    )

    def unavailable(url: str, timeout: int) -> io.BytesIO:
        raise HTTPError(url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(check_pins, "urlopen", unavailable)

    report = check_pins.render_report(tmp_path)

    assert "ERROR: HTTP Error 503: unavailable" in report


def test_main_prints_and_writes_the_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(
        tmp_path / "paper" / "{{cookiecutter.repo_name}}" / "pyproject.toml",
        'dependencies = ["numpy>=2.5.3"]\n',
    )
    destination = tmp_path / "reports" / "pins.md"

    result = check_pins.main(
        ["--root", str(tmp_path), "--report", str(destination)],
        fetch=lambda url: {"info": {"version": "2.6.0"}},
    )

    assert result == 0
    assert destination.read_text(encoding="utf-8") == capsys.readouterr().out
    assert "| 2.5.3 | 2.6.0 |" in destination.read_text(encoding="utf-8")
