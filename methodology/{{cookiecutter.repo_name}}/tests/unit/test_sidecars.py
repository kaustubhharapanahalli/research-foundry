"""Foundry run records: each field and each refusal."""

import json
from pathlib import Path

import pytest

from {{ cookiecutter.package_name }} import sidecars
from {{ cookiecutter.package_name }}.sidecars import SidecarError

DISPATCHED = {"FOUNDRY_RUN_ID": "42", "OMP_NUM_THREADS": "4"}
CONFIG = {"lr": 0.001, "epochs": 2}
ROW = {"benchmark": "metr-la", "metric": "mae", "horizon": 12, "seed": 0,
       "value": 2.91}  # fmt: skip


def _witness(tmp_path: Path, **env: str) -> dict[str, object]:
    path = sidecars.write_witness(
        tmp_path, CONFIG, 7, "cpu", environ={**DISPATCHED, **env},
        now=lambda: "2026-10-02T00:00:00+00:00",
    )  # fmt: skip
    assert path is not None
    loaded: dict[str, object] = json.loads(path.read_text())
    return loaded


def test_the_experiment_id_is_the_launchers() -> None:
    assert sidecars.experiment_id({"FOUNDRY_RUN_ID": "42"}) == 42


@pytest.mark.parametrize(
    "env", [{}, {"FOUNDRY_RUN_ID": ""}, {"FOUNDRY_RUN_ID": "forty-two"}]
)
def test_guard_a_run_without_its_experiment_id_is_refused(
    env: dict[str, str],
) -> None:
    with pytest.raises(SidecarError, match="FOUNDRY_RUN_ID"):
        sidecars.experiment_id(env)


def test_the_config_hash_uses_the_documented_function() -> None:
    # sha256 of the sorted-key JSON, first 16 hex characters.
    assert sidecars.config_sha(CONFIG) == "da1dca8eecbe78ba"
    assert (
        sidecars.config_sha({"epochs": 2, "lr": 0.001}) == "da1dca8eecbe78ba"
    )


def test_the_witness_has_exactly_the_versioned_fields(tmp_path: Path) -> None:
    witness = _witness(tmp_path)
    assert tuple(sorted(witness)) == sidecars.WITNESS_FIELDS
    assert witness == {
        "attempt": 0,
        "captured_at": "2026-10-02T00:00:00+00:00",
        "config_sha": "da1dca8eecbe78ba",
        "cpu_threads": 4,
        "device": "cpu",
        "device_name": None,
        "experiment_id": 42,
        "peak_vram_mb": None,
        "run_record_format": 1,
        "wall_seconds": 7,
    }


def test_a_restarted_job_writes_its_own_attempt(tmp_path: Path) -> None:
    assert _witness(tmp_path, SLURM_RESTART_COUNT="2")["attempt"] == 2
    assert (tmp_path / "observed.attempt2.json").exists()


@pytest.mark.parametrize("name", ["RANK", "SLURM_PROCID"])
def test_only_rank_0_writes_a_witness(tmp_path: Path, name: str) -> None:
    written = sidecars.write_witness(
        tmp_path, CONFIG, 7, "cpu", environ={**DISPATCHED, name: "1"}
    )
    assert written is None
    assert not list(tmp_path.iterdir())


def test_guard_a_witness_is_never_rewritten(tmp_path: Path) -> None:
    _witness(tmp_path)
    with pytest.raises(SidecarError, match="never rewritten"):
        _witness(tmp_path)


def test_guard_a_witness_needs_the_experiment_id(tmp_path: Path) -> None:
    with pytest.raises(SidecarError):
        sidecars.write_witness(tmp_path, CONFIG, 7, "cpu", environ={})
    assert not list(tmp_path.iterdir())


def test_the_same_run_writes_the_same_bytes(tmp_path: Path) -> None:
    _witness(tmp_path / "a")
    _witness(tmp_path / "b")
    name = "observed.attempt0.json"
    assert (tmp_path / "a" / name).read_bytes() == (
        tmp_path / "b" / name
    ).read_bytes()


def test_metrics_rows_keep_exactly_the_contract_s_fields(
    tmp_path: Path,
) -> None:
    path = sidecars.write_metrics(tmp_path, [ROW, {**ROW, "seed": 1}])
    rows = json.loads(path.read_text())
    assert [tuple(row) for row in rows] == [sidecars.METRIC_FIELDS] * 2


@pytest.mark.parametrize(
    "bad",
    [
        {k: v for k, v in ROW.items() if k != "horizon"},
        {**ROW, "split": "test"},
        {**ROW, "benchmark": " "},
        {**ROW, "horizon": -1},
        {**ROW, "seed": True},
        {**ROW, "seed": 1.5},
        {**ROW, "value": float("nan")},
        {**ROW, "value": "2.91"},
    ],
)
def test_guard_an_invalid_row_writes_nothing(
    tmp_path: Path, bad: dict[str, object]
) -> None:
    with pytest.raises(SidecarError):
        sidecars.write_metrics(tmp_path, [ROW, bad])
    assert not (tmp_path / "metrics.json").exists()


def test_guard_no_rows_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SidecarError, match="at least one"):
        sidecars.write_metrics(tmp_path, [])
