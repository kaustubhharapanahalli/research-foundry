"""Markdown in templates stays stable under Prettier for every answer."""

from pathlib import Path

import pytest
from tests.conftest import PROJECT_DIR, ROOT, template_kinds


def _markdown() -> list[Path]:
    return sorted(
        p
        for kind in template_kinds()
        for p in (ROOT / kind / PROJECT_DIR).rglob("*.md")
    )


@pytest.mark.parametrize(
    "path", _markdown(), ids=lambda p: str(p.relative_to(ROOT))
)
def test_no_table_has_template_logic_or_variables(path: Path) -> None:
    # Prettier pads every column to its longest cell. A row that an answer
    # adds, removes or lengthens changes the padding of the whole table, so
    # a generated file would fail its first `make lint`. Use a list instead.
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith("|"):
            assert "{{" not in line, f"{path.name}:{number} has a variable"
        if line.lstrip().startswith("{%"):
            neighbours = path.read_text().splitlines()[number - 2 : number + 1]
            assert not any(
                n.lstrip().startswith("|") for n in neighbours
            ), f"{path.name}:{number} puts logic inside a table"
