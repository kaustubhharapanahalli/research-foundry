"""Refuse an API reference that omits any public Python module."""

import re
import sys
from pathlib import Path

MODULE = re.compile(r"^\s*:::\s+([\w.]+)\s*$", re.MULTILINE)


def public_modules(package: str, source: Path) -> set[str]:
    """Return public importable modules under the package source directory."""
    if not source.is_dir():
        raise FileNotFoundError(
            f"package source directory does not exist: {source}"
        )
    modules: set[str] = set()
    for path in source.rglob("*.py"):
        relative = path.relative_to(source)
        if path.stem != "__init__" and path.stem.startswith("_"):
            continue
        parents = relative.parts[:-1]
        if any(part.startswith("_") for part in parents):
            continue
        suffix = [] if path.stem == "__init__" else [path.stem]
        modules.add(".".join((package, *parents, *suffix)))
    return modules


def main(argv: list[str]) -> int:
    """Check the package's public modules against the API page."""
    if len(argv) != 1:
        print("usage: check_reference.py PACKAGE", file=sys.stderr)
        return 2
    package = argv[0]
    api_page = Path("docs/api/index.md")
    source = Path("src") / package
    documented = set(MODULE.findall(api_page.read_text(encoding="utf-8")))
    missing = sorted(public_modules(package, source) - documented)
    if missing:
        for module in missing:
            print(f"{api_page}: missing ::: {module}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
