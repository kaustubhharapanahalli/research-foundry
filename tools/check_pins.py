"""Report template pins and deliberately held frontend majors.

The report compares hidden template pins with their newest releases and lists
each frontend major held by the frontend component and pins decision (ADR 0003)
with the npm requirement that currently blocks it.

Examples:
--------
Print a Markdown table for the pins Dependabot cannot parse::

    uv run python -m tools.check_pins
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ("methodology", "workspace", "paper", "software")
PYTHON_PIN = re.compile(
    r'["\'](?P<name>[A-Za-z0-9_.-]+)(?:\[[^]]+\])?>=(?P<version>[0-9][^;"\']*)'
)
IMAGE_PIN = re.compile(
    r"(?:FROM\s+|image:\s*)(?P<image>[^\s:@]+(?:/[^\s:@]+)*):"
    r"(?P<version>[^\s@]+)(?:@sha256:[0-9a-f]+)?",
    re.IGNORECASE,
)
PRE_COMMIT_PIN = re.compile(
    r"repo:\s*https://github\.com/(?P<repo>[^\s]+).*?"
    r"rev:\s*[^\s#]+(?:\s*#\s*frozen:\s*(?P<version>[^\s]+))?",
    re.DOTALL,
)
Fetch = Callable[..., Mapping[str, Any]]


@dataclass(frozen=True)
class Pin:
    """One registry-backed version held in a template file."""

    kind: str
    name: str
    current: str
    file: Path


@dataclass(frozen=True)
class Hold:
    """One frontend major held by the frontend component and pins decision.

    The ``HOLDS`` tuple records that decision (ADR 0003) and must match the
    Dependabot ignore rules.
    """

    held_packages: tuple[str, ...]
    blocker: str
    dependency: str
    lift_condition: str


HOLDS: tuple[Hold, ...] = (
    Hold(
        ("vitest", "@vitest/coverage-v8"),
        "vitest-monocart-coverage",
        "@vitest/coverage-v8",
        "it accepts `@vitest/coverage-v8` 5, and the merged report "
        "matches the printed one",
    ),
    Hold(
        ("typescript",),
        "typescript-eslint",
        "typescript",
        "`typescript-eslint` widens that range",
    ),
    Hold(
        ("eslint",),
        "eslint-plugin-import",
        "eslint",
        "both plugins accept ESLint 10",
    ),
    Hold(
        ("eslint",),
        "eslint-plugin-jsx-a11y",
        "eslint",
        "both plugins accept ESLint 10",
    ),
)


def _template_files(root: Path, name: str) -> list[Path]:
    paths: list[Path] = []
    for template in TEMPLATES:
        project = root / template / "{{cookiecutter.repo_name}}"
        if project.is_dir():
            paths.extend(project.rglob(name))
    return sorted(paths)


def _collect_pypi_pins(root: Path) -> list[Pin]:
    """Find Python Package Index pins in template project files.

    Parameters
    ----------
    root
        Foundry repository root.

    Returns:
    -------
    list[Pin]
        Python Package Index pins.
    """
    pins: list[Pin] = []
    for path in _template_files(root, "pyproject.toml"):
        for match in PYTHON_PIN.finditer(path.read_text(encoding="utf-8")):
            pins.append(
                Pin(
                    "pypi",
                    match.group("name"),
                    match.group("version"),
                    path.relative_to(root),
                )
            )
    return pins


def _collect_docker_pins(root: Path) -> list[Pin]:
    """Find Docker image pins in template container files.

    Parameters
    ----------
    root
        Foundry repository root.

    Returns:
    -------
    list[Pin]
        Docker image pins.
    """
    pins: list[Pin] = []
    for filename in ("compose.yaml", "Dockerfile"):
        for path in _template_files(root, filename):
            for match in IMAGE_PIN.finditer(path.read_text(encoding="utf-8")):
                pins.append(
                    Pin(
                        "docker",
                        match.group("image"),
                        match.group("version"),
                        path.relative_to(root),
                    )
                )
    return pins


def _collect_npm_pins(root: Path) -> list[Pin]:
    """Find Node package manager pins in template package files.

    Parameters
    ----------
    root
        Foundry repository root.

    Returns:
    -------
    list[Pin]
        Node package manager and runtime pins.
    """
    pins: list[Pin] = []
    for path in _template_files(root, "package.json"):
        text = path.read_text(encoding="utf-8")
        if "{{" not in text and "{%" not in text:
            continue
        data = json.loads(text)
        for section in ("dependencies", "devDependencies"):
            for name, version in data.get(section, {}).items():
                pins.append(Pin("npm", name, version, path.relative_to(root)))
        manager = data.get("packageManager")
        if isinstance(manager, str) and "@" in manager:
            name, version = manager.rsplit("@", 1)
            pins.append(Pin("npm", name, version, path.relative_to(root)))
        for engine in data.get("devEngines", {}).values():
            if not isinstance(engine, Mapping):
                continue
            name, version = engine.get("name"), engine.get("version")
            if isinstance(name, str) and isinstance(version, str):
                kind = "docker" if name == "node" else "npm"
                pins.append(Pin(kind, name, version, path.relative_to(root)))
    return pins


def _collect_github_pins(root: Path) -> list[Pin]:
    """Find GitHub release pins in shared pre-commit configuration.

    Parameters
    ----------
    root
        Foundry repository root.

    Returns:
    -------
    list[Pin]
        GitHub release pins.
    """
    pins: list[Pin] = []
    for path in sorted(root.glob("_shared/**/*pre-commit-config.yaml")):
        text = path.read_text(encoding="utf-8")
        for match in PRE_COMMIT_PIN.finditer(text):
            version = (
                match.group("version")
                or match.group(0).split("rev:", 1)[1].split()[0]
            )
            pins.append(
                Pin(
                    "github",
                    match.group("repo").removesuffix(".git"),
                    version,
                    path.relative_to(root),
                )
            )
    return pins


def collect_pins(root: Path = ROOT) -> list[Pin]:
    """Find registry pins in every Jinja-bearing template source.

    Parameters
    ----------
    root
        Foundry repository root.

    Returns:
    -------
    list[Pin]
        Pins in stable file and package order.
    """
    pins = [
        *_collect_pypi_pins(root),
        *_collect_docker_pins(root),
        *_collect_npm_pins(root),
        *_collect_github_pins(root),
    ]
    return sorted(pins, key=lambda pin: (str(pin.file), pin.name, pin.current))


def _fetch_json(
    url: str, headers: Mapping[str, str] | None = None
) -> Mapping[str, Any]:
    """Fetch one registry response as JSON."""
    request: str | Request = (
        Request(url, headers=dict(headers)) if headers else url
    )
    with urlopen(
        request, timeout=30
    ) as response:  # noqa: S310 - fixed registries
        value: Mapping[str, Any] = json.load(response)
    return value


def _version_parts(version: str) -> tuple[int, ...]:
    """Return the numeric portion of a release for stable tag ordering."""
    match = re.match(r"^v?(\d+(?:\.\d+)*)", version)
    if match is None:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def _newest_docker_tag(current_tag: str, names: Sequence[str]) -> str:
    """Choose the newest registry tag sharing the current tag's flavour."""
    current = re.match(r"^(v?\d+(?:\.\d+)*)(.*)$", current_tag)
    if current is None:
        raise ValueError(f"cannot compare Docker tag {current_tag!r}")
    suffix = current.group(2)
    candidates = [
        name
        for name in names
        if re.match(r"^v?\d+(?:\.\d+)*", name)
        and re.sub(r"^v?\d+(?:\.\d+)*", "", name) == suffix
    ]
    if not candidates:
        raise ValueError(f"registry returned no tags with flavour {suffix!r}")
    return max(candidates, key=_version_parts)


def _docker_tag(pin: Pin, fetch: Fetch) -> str:
    """Return the newest Docker tag with the current tag's flavour."""
    if pin.name.startswith("ghcr.io/"):
        repository = pin.name.removeprefix("ghcr.io/")
        token_response = fetch(
            f"https://ghcr.io/token?scope=repository:{repository}:pull"
        )
        token = str(token_response["token"])
        response = fetch(
            f"https://ghcr.io/v2/{repository}/tags/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        tags = response.get("tags")
        if not isinstance(tags, list):
            raise ValueError("registry returned no tag list")
        return _newest_docker_tag(
            pin.current, [str(tag) for tag in tags if isinstance(tag, str)]
        )
    repository = pin.name if "/" in pin.name else f"library/{pin.name}"
    response = fetch(
        f"https://hub.docker.com/v2/repositories/{repository}/tags"
        "?page_size=100&ordering=last_updated"
    )
    names = [
        str(item["name"])
        for item in response.get("results", [])
        if isinstance(item, Mapping) and "name" in item
    ]
    return _newest_docker_tag(pin.current, names)


def _newest(pin: Pin, fetch: Fetch) -> str:
    """Ask the registry appropriate for ``pin`` for its latest release."""
    if pin.kind == "pypi":
        name = quote(pin.name, safe="")
        response = fetch(f"https://pypi.org/pypi/{name}/json")
        return str(response["info"]["version"])
    if pin.kind == "npm":
        response = fetch(
            f"https://registry.npmjs.org/{quote(pin.name, safe='')}/latest"
        )
        return str(response["version"])
    if pin.kind == "github":
        url = f"https://api.github.com/repos/{pin.name}/releases/latest"
        response = fetch(url)
        return str(response["tag_name"])
    if pin.kind == "docker":
        return _docker_tag(pin, fetch)
    raise ValueError(f"unknown pin kind {pin.kind!r}")


def _hold_requirement(hold: Hold, response: Mapping[str, Any]) -> str:
    """Return the blocker range constraining the held dependency."""
    for section in ("peerDependencies", "dependencies"):
        requirements = response.get(section)
        if (
            isinstance(requirements, Mapping)
            and hold.dependency in requirements
        ):
            return str(requirements[hold.dependency])
    return "not declared"


def _markdown_cell(value: str) -> str:
    """Escape text that would otherwise split a Markdown table cell."""
    return value.replace("|", r"\|")


def render_report(root: Path = ROOT, fetch: Fetch | None = None) -> str:
    """Return Markdown tables for template pins and held frontend majors.

    Registry failures are rendered in the affected row so one unavailable
    service cannot hide the results from the other registries or blockers.
    """
    get = fetch or _fetch_json
    rows = [
        "# Weekly template pin report",
        "",
        "| Pin | File | Current | Newest |",
        "| --- | --- | --- | --- |",
    ]
    for pin in collect_pins(root):
        try:
            newest = _newest(pin, get)
        except (
            URLError,
            HTTPError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
        ) as error:  # Registries fail independently.
            newest = f"ERROR: {error}"
        row = f"| `{pin.name}` | `{pin.file}` | {pin.current} | {newest} |"
        rows.append(row)
    rows.extend(
        (
            "",
            "## Held majors (ADR 0003)",
            "",
            "| Held | Blocked by | Blocker latest | "
            "Blocker requires | Lifts when |",
            "| --- | --- | --- | --- | --- |",
        )
    )
    for hold in HOLDS:
        try:
            response = get(
                "https://registry.npmjs.org/"
                f"{quote(hold.blocker, safe='')}/latest"
            )
            latest = str(response["version"])
            requirement = _hold_requirement(hold, response)
        except (
            URLError,
            HTTPError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
        ) as error:  # Registries fail independently.
            latest = f"ERROR: {error}"
            requirement = latest
        held = ", ".join(f"`{package}`" for package in hold.held_packages)
        blocker = f"`{hold.blocker}`"
        requires = f"`{hold.dependency}` `{_markdown_cell(requirement)}`"
        rows.append(
            f"| {held} | {blocker} | {_markdown_cell(latest)} | "
            f"{requires} | {hold.lift_condition} |"
        )
    return "\n".join(rows) + "\n"


def main(
    argv: Sequence[str] | None = None, *, fetch: Fetch | None = None
) -> int:
    """Print the weekly pin report, returning zero even when pins are stale."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = render_report(args.root, fetch)
    print(report, end="")
    destination = args.report or args.root / "build" / "pins-report.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
