"""Keep the documentation site aligned with the package and API."""

import tomllib

import pytest
import yaml
from tests.conftest import ROOT


@pytest.mark.unit
def test_api_reference_covers_every_public_module() -> None:
    reference = (ROOT / "docs" / "reference.md").read_text(encoding="utf-8")
    modules = sorted(
        path.stem
        for path in (ROOT / "src" / "research_foundry").glob("*.py")
        if not path.stem.startswith("_")
    )

    for module in modules:
        assert f"::: research_foundry.{module}" in reference


@pytest.mark.unit
def test_site_url_matches_package_documentation_url() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    configuration = yaml.safe_load((ROOT / "mkdocs.yml").read_text())

    assert (
        configuration["site_url"]
        == project["project"]["urls"]["Documentation"]
    )
