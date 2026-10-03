"""The template matrix and the throwaway fixture (tools/), without real CI.

The orchestration is driven with a fake runner and a fake generator, so
these are fast. The combinations are found by real renders, and the
throwaway fixture runs the real cruft against a snapshot of this tree.
"""

import json
import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from tools import template_matrix as matrix
from tools import throwaway


def _done(code: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], code, "out", "err")


# pylint: disable-next=too-few-public-methods
class FakeRun:
    """Records each command; fails the one whose step name is ``fail``."""

    def __init__(self, fail: str | None = None, left: str = "") -> None:
        self.calls: list[tuple[str, ...]] = []
        self.fail = fail
        #: What `git status --porcelain` reports after CI.
        self.left = left

    def __call__(
        self, argv: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        self.calls.append(tuple(argv))
        if self.fail and self.fail in argv:
            return _done(2)
        if tuple(argv[:2]) == ("git", "status"):
            return subprocess.CompletedProcess([], 0, self.left, "")
        return _done()


def _fake_make(mark: bool = True, compose: bool = False) -> matrix.Generate:
    def make(template: str, answers: dict[str, str], **kw: object) -> Path:
        del template, answers
        project = Path(str(kw["into"])) / "proj"
        project.mkdir()
        text = matrix.SHARED_MARK if mark else ""
        (project / ".editorconfig").write_text(text)
        if compose:
            (project / "compose.yaml").write_text("services: {}\n")
        return project

    return make


VARIANT = matrix.Variant("methodology", (("ml_pytorch", "no"),))


@pytest.mark.unit
def test_a_variant_is_named_by_its_template_and_answers() -> None:
    assert VARIANT.name == "methodology-ml_pytorch=no"
    assert matrix.Variant("workspace", ()).name == "workspace"


@pytest.mark.unit
def test_the_reason_is_the_hooks_own_words() -> None:
    text = (
        "frontend_nextjs needs backend_django: why.\n"
        "Stopping generation because pre_gen_project hook script didn't\n"
        "Traceback (most recent call last):\n  File x\n"
    )
    assert (
        matrix.hook_reason(text)
        == "frontend_nextjs needs backend_django: why."
    )
    assert matrix.hook_reason("") == "refused by a generation hook"


@pytest.mark.unit
def test_a_passing_variant_runs_every_step_and_is_deleted(
    tmp_path: Path,
) -> None:
    run = FakeRun()
    logs = tmp_path / "logs"
    logs.mkdir()
    result = matrix.run_variant(
        VARIANT, tmp_path, tmp_path, logs, run=run, make=_fake_make()
    )
    assert result.passed, result.failure
    assert list(result.steps) == [
        "generate", "install", "ci", "update", "template-check",
    ]  # fmt: skip
    assert ("make", "ci") in run.calls
    assert not list(tmp_path.glob("variant-*")), "the project was kept"
    assert (logs / f"{VARIANT.name}.ci.log").read_text() == "outerr"


@pytest.mark.unit
def test_variant_runner_exports_a_workdir_cookiecutter_config(
    tmp_path: Path,
) -> None:
    configs: list[tuple[Path, dict[str, str]]] = []

    def run(
        argv: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        config = Path(os.environ["COOKIECUTTER_CONFIG"])
        configs.append(
            (config, json.loads(config.read_text(encoding="utf-8")))
        )
        if tuple(argv[:2]) == ("git", "status"):
            return subprocess.CompletedProcess([], 0, "", "")
        return _done()

    result = matrix.run_variant(
        VARIANT,
        tmp_path,
        tmp_path,
        tmp_path,
        run=run,
        make=_fake_make(),
    )
    assert result.passed
    assert configs
    config_paths = {path for path, _ in configs}
    assert len(config_paths) == 1
    config_path = config_paths.pop()
    assert config_path.parent.parent == tmp_path
    config = configs[0][1]
    assert config["cookiecutters_dir"] == str(
        config_path.parent / "cookiecutters"
    )
    assert config["replay_dir"] == str(config_path.parent / "replay")


@pytest.mark.unit
def test_matrix_subprocesses_receive_cookiecutter_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[tuple[Path, dict[str, str]]] = []

    def fake_subprocess_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        config_path = Path(environment["COOKIECUTTER_CONFIG"])
        captured.append(
            (
                config_path,
                json.loads(config_path.read_text(encoding="utf-8")),
            )
        )
        command = args[0]
        if isinstance(command, list) and command[:2] == ["git", "status"]:
            return subprocess.CompletedProcess([], 0, "", "")
        return _done()

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    result = matrix.run_variant(
        VARIANT, tmp_path, tmp_path, tmp_path, make=_fake_make()
    )

    assert result.passed
    assert captured
    config_paths = {path for path, _ in captured}
    assert len(config_paths) == 1
    config_path = config_paths.pop()
    assert config_path.parent.parent == tmp_path
    config = captured[0][1]
    assert config["cookiecutters_dir"] == str(
        config_path.parent / "cookiecutters"
    )
    assert config["replay_dir"] == str(config_path.parent / "replay")


@pytest.mark.unit
def test_a_failing_step_stops_the_variant(tmp_path: Path) -> None:
    run = FakeRun(fail="ci")
    result = matrix.run_variant(
        VARIANT, tmp_path, tmp_path, tmp_path, run=run, make=_fake_make()
    )
    assert result.failure == "ci: exit 2"
    assert "update" not in result.steps
    assert not list(tmp_path.glob("variant-*"))


@pytest.mark.unit
def test_an_update_that_carries_nothing_fails(tmp_path: Path) -> None:
    result = matrix.run_variant(
        VARIANT,
        tmp_path,
        tmp_path,
        tmp_path,
        run=FakeRun(),
        make=_fake_make(mark=False),
    )
    assert result.failure == "update: the shared change did not arrive"


@pytest.mark.unit
def test_a_generation_that_raises_is_a_failed_generate(tmp_path: Path) -> None:
    def broken(*_a: object, **_k: object) -> Path:
        raise RuntimeError("cruft said no")

    result = matrix.run_variant(
        VARIANT, tmp_path, tmp_path, tmp_path, run=FakeRun(), make=broken
    )
    assert result.steps == {"generate": "failed"}
    assert result.failure == "RuntimeError: cruft said no"


@pytest.mark.unit
def test_a_software_variants_containers_go_with_it(tmp_path: Path) -> None:
    run = FakeRun()
    matrix.run_variant(
        matrix.Variant("software", ()),
        tmp_path,
        tmp_path,
        tmp_path,
        run=run,
        make=_fake_make(compose=True),
    )
    downs = [c for c in run.calls if c[:2] == ("docker", "compose")]
    assert downs and "--volumes" in downs[0]


@pytest.mark.unit
def test_a_paper_fetches_its_venue_before_its_ci() -> None:
    steps = [s for s, _ in matrix.ci_steps(matrix.Variant("paper", ()))]
    assert steps == ["install", "venue", "ci"]
    article = matrix.Variant("paper", (("venue", "article"),))
    assert [s for s, _ in matrix.ci_steps(article)] == ["install", "ci"]


@pytest.mark.unit
def test_the_report_names_each_result_and_each_refusal() -> None:
    good = matrix.Result("a", {"generate": "passed"}, None, 1.0)
    bad = matrix.Result("b", {"ci": "failed"}, "ci: exit 2", 2.0)
    text = matrix.report([good, bad], [(VARIANT, "needs a licence")])
    assert "| `a` | generate passed | passed | 1.0 |" in text
    assert "FAILED (ci: exit 2)" in text
    assert f"- `{VARIANT.name}`: needs a licence" in text


@pytest.mark.unit
def test_an_unknown_template_is_refused() -> None:
    with pytest.raises(SystemExit):
        matrix.main(["--list", "--templates", "website"])


@pytest.mark.unit
@pytest.mark.parametrize(
    "argv",
    [
        ["no-such-thing"],
        ["methodology-plain", "ml_pytorch=yes"],
        ["methodology", "not-a-pair"],
    ],
)
def test_the_throwaway_command_refuses_what_it_cannot_make(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        throwaway.main(argv)


@pytest.mark.unit
def test_generate_refuses_an_unknown_template(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="website"):
        throwaway.generate("website", {}, into=tmp_path)


@pytest.mark.unit
def test_files_ci_leaves_behind_fail_the_variant(tmp_path: Path) -> None:
    run = FakeRun(left="?? coverage.xml\n")
    result = matrix.run_variant(
        VARIANT, tmp_path, tmp_path, tmp_path, run=run, make=_fake_make()
    )
    assert result.failure == (
        "ci: left files git does not ignore: coverage.xml"
    )


@pytest.mark.unit
def test_the_first_lock_is_committed_after_install(tmp_path: Path) -> None:
    run = FakeRun()
    matrix.run_variant(
        VARIANT, tmp_path, tmp_path, tmp_path, run=run, make=_fake_make()
    )
    install = run.calls.index(("make", "install"))
    assert run.calls[install + 2] == ("git", "commit", "-qm", "the first lock")


@pytest.mark.unit
def test_the_venue_kit_is_committed_before_the_ci(tmp_path: Path) -> None:
    run = FakeRun()
    paper = matrix.Variant("paper", ())
    matrix.run_variant(
        paper, tmp_path, tmp_path, tmp_path, run=run, make=_fake_make()
    )
    venue = run.calls.index(("make", "venue"))
    assert run.calls[venue + 2] == ("git", "commit", "-qm", "the venue kit")
    ci = next(c for c in run.calls if c[:1] == ("make",) and "ci" in c[1])
    assert run.calls.index(ci) > venue + 2


@pytest.mark.unit
def test_where_keeps_only_the_variants_with_that_answer() -> None:
    yes = matrix.Variant("software", (("ml_pytorch", "yes"),))
    no = matrix.Variant("software", (("ml_pytorch", "no"),))
    found = {"software": ([yes, no], [(no, "a reason")])}
    kept = matrix.where(found, ["ml_pytorch=yes"])
    assert kept == {"software": ([yes], [])}


@pytest.mark.unit
@pytest.mark.parametrize("pair", ["ml_pytorch", "=yes", "ml_pytorch=maybe"])
def test_where_refuses_a_filter_that_matches_nothing(pair: str) -> None:
    found: matrix.Found = {"software": ([matrix.Variant("software", ())], [])}
    with pytest.raises(ValueError):
        matrix.where(found, [pair])
