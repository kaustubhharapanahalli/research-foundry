"""The top-level index and each template folder agree with each other."""

import json
import os

import pytest
from tests.conftest import PROJECT_DIR, ROOT, SHARED, template_kinds


def test_index_lists_every_template_folder() -> None:
    on_disk = sorted(
        p.parent.name
        for p in ROOT.glob("*/cookiecutter.json")
        if not p.parent.name.startswith((".", "_"))
    )
    assert on_disk == template_kinds()


@pytest.mark.parametrize("kind", template_kinds())
def test_index_path_points_at_the_template(kind: str) -> None:
    index = json.loads((ROOT / "cookiecutter.json").read_text())
    assert (ROOT / index["templates"][kind]["path"]).resolve() == (
        ROOT / kind
    ).resolve()


@pytest.mark.parametrize("kind", template_kinds())
def test_template_has_one_project_folder(kind: str) -> None:
    assert (ROOT / kind / PROJECT_DIR).is_dir()


@pytest.mark.parametrize("kind", template_kinds())
def test_templates_link_points_at_shared(kind: str) -> None:
    # cookiecutter looks for includes in ../templates (generate.py), so each
    # template reaches the shared base through this one link.
    link = ROOT / kind / "templates"
    assert link.is_symlink()
    assert os.readlink(link) == "../_shared"
    assert link.resolve() == SHARED.resolve()


@pytest.mark.parametrize("kind", template_kinds())
def test_template_kind_is_recorded(kind: str) -> None:
    context = json.loads((ROOT / kind / "cookiecutter.json").read_text())
    assert context["_template_kind"] == kind
