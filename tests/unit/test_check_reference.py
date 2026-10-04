"""The generated API guard requires a reference block for every module."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from tests.conftest import SHARED


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "api_reference_check", SHARED / "docs" / "api_reference_check.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference = _load()


def test_public_modules_includes_package_and_nested_modules(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src"
    (source / "models").mkdir(parents=True)
    (source / "_private").mkdir()
    for name in (
        "__init__.py",
        "public.py",
        "_hidden.py",
        "models/__init__.py",
        "models/layers.py",
        "_private/secret.py",
    ):
        (source / name).touch()

    assert reference.public_modules("sample", source) == {
        "sample",
        "sample.public",
        "sample.models",
        "sample.models.layers",
    }


def test_public_modules_requires_a_package_directory(tmp_path: Path) -> None:
    with pytest.raises(
        FileNotFoundError, match="package source directory does not exist"
    ):
        reference.public_modules("missing", tmp_path / "missing")


def test_main_requires_one_package_argument(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert reference.main([]) == 2
    assert capsys.readouterr().err == "usage: check_reference.py PACKAGE\n"


def test_main_accepts_a_complete_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    package = Path("src/sample")
    package.mkdir(parents=True)
    (package / "__init__.py").touch()
    (package / "public.py").touch()
    api = Path("docs/api")
    api.mkdir(parents=True)
    (api / "index.md").write_text(
        "::: sample\n\n::: sample.public\n", encoding="utf-8"
    )
    assert reference.main(["sample"]) == 0


def test_main_reports_a_module_missing_from_the_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    package = Path("src/sample")
    package.mkdir(parents=True)
    (package / "__init__.py").touch()
    (package / "public.py").touch()
    api = Path("docs/api")
    api.mkdir(parents=True)
    (api / "index.md").write_text("::: sample\n", encoding="utf-8")
    assert reference.main(["sample"]) == 1
    assert capsys.readouterr().out == (
        "docs/api/index.md: missing ::: sample.public\n"
    )
