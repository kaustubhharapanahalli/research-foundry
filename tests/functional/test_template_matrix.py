"""The template matrix and the throwaway fixture, against real renders.

The combinations are found by rendering every template, and the throwaway
fixture runs the real cruft against a snapshot of this tree. The
orchestration's own tests, with fakes, are in tests/unit.
"""

import json
import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from tests.conftest import GIT_ENV
from tools import template_matrix as matrix
from tools import throwaway
from tools.variants import VARIANTS


@pytest.mark.functional
def test_only_options_that_change_the_files_are_multiplied(
    tmp_path: Path,
) -> None:
    options = matrix.tree_options(matrix.ROOT, "methodology", tmp_path)
    # cuda_source changes pyproject.toml, not which files there are; MIT
    # and Apache-2.0 make the same files, so one of them stands for both.
    assert options == {
        "license": ["Apache-2.0", "none"],
        "ml_pytorch": ["yes", "no"],
        "public_docs": ["no", "yes"],
        "dataset_registry": ["no", "yes"],
        "run_records": ["no", "yes"],
    }


@pytest.mark.functional
def test_combinations_the_hook_refuses_are_recorded_not_run(
    tmp_path: Path,
) -> None:
    runnable, refused = matrix.variants(matrix.ROOT, "software", tmp_path)
    assert runnable and refused
    for variant, reason in refused:
        assert ("backend_django", "no") in variant.answers
        assert "needs backend_django" in reason or "at least one" in reason
    assert all(("backend_django", "yes") in v.answers for v in runnable)


@pytest.mark.functional
def test_the_matrix_lists_without_running(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert matrix.main(["--list", "--templates", "workspace"]) == 0
    assert capsys.readouterr().out.strip() == "workspace"


@pytest.mark.functional
def test_a_throwaway_is_generated_offline_from_a_snapshot(
    tmp_path: Path,
) -> None:
    source = throwaway.snapshot(matrix.ROOT, tmp_path / "foundry", GIT_ENV)
    project = throwaway.generate(
        "workspace", {}, into=tmp_path / "out", source=source, ref="main"
    )
    record = json.loads((project / ".cruft.json").read_text())
    assert record["template"] == str(source)
    assert record["directory"] == "workspace"
    assert (project / "datasets" / "registry.yaml").exists()


@pytest.mark.functional
def test_the_matrix_source_carries_the_shared_change_after_its_base(
    tmp_path: Path,
) -> None:
    source = matrix.prepare_source(tmp_path)
    base = throwaway.show(source, "matrix-base", matrix.SHARED_FILE.as_posix())
    assert matrix.SHARED_MARK not in base
    assert matrix.SHARED_MARK in (source / matrix.SHARED_FILE).read_text()


@pytest.mark.functional
def test_the_throwaway_command_takes_a_variant_or_a_template(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = throwaway.snapshot(matrix.ROOT, tmp_path / "foundry", GIT_ENV)
    assert (
        throwaway.main(
            [
                "workspace",
                "--into",
                str(tmp_path / "a"),
                "--source",
                str(source),
            ]
        )
        == 0
    )
    printed = Path(capsys.readouterr().out.strip())
    assert printed.parent == tmp_path / "a"
    assert "methodology-plain" in VARIANTS


@pytest.mark.functional
def test_variant_generate_and_update_keep_cookiecutter_files_out_of_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    source = matrix.prepare_source(tmp_path / "source-work")

    def run(
        argv: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        command = list(argv)
        if command[:1] == ["git"]:
            return subprocess.run(
                command,
                cwd=cwd,
                env={**os.environ, **GIT_ENV},
                capture_output=True,
                text=True,
                check=False,
            )
        if command[:4] == ["uvx", "--from", "cruft==2.16.0", "cruft"]:
            return subprocess.run(
                ["cruft", *command[4:]],
                cwd=cwd,
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                check=False,
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    result = matrix.run_variant(
        matrix.Variant("workspace", ()),
        source,
        tmp_path,
        tmp_path,
        run=run,
        make=throwaway.generate,
    )

    assert result.passed, result.failure
    assert result.steps["generate"] == "passed"
    assert result.steps["update"] == "passed"
    assert not list(home.iterdir())


@pytest.mark.functional
def test_a_throwaway_leaves_only_the_project_and_nothing_in_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    source = matrix.prepare_source(tmp_path / "source-work")
    out = tmp_path / "out"

    project = throwaway.generate(
        "workspace", {}, into=out, source=source, ref="matrix-base"
    )

    assert list(out.iterdir()) == [project]
    assert not list(home.iterdir())


@pytest.mark.functional
def test_an_answer_the_template_does_not_ask_is_refused(
    tmp_path: Path,
) -> None:
    # cookiecutter drops an unknown answer without a word, so a throwaway
    # made from a commit that predates the answer would test the wrong
    # project.
    source = throwaway.snapshot(matrix.ROOT, tmp_path / "foundry", GIT_ENV)
    with pytest.raises(ValueError, match="no_such_answer"):
        throwaway.generate(
            "workspace",
            {"no_such_answer": "yes"},
            into=tmp_path / "out",
            source=source,
        )
    assert not (tmp_path / "out").exists()


@pytest.mark.functional
def test_the_working_tree_option_includes_uncommitted_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        throwaway.main(
            ["workspace", "--working-tree", "--into", str(tmp_path / "a")]
        )
        == 0
    )
    record = json.loads(
        (Path(capsys.readouterr().out.strip()) / ".cruft.json").read_text()
    )
    assert record["template"] != str(matrix.ROOT)
