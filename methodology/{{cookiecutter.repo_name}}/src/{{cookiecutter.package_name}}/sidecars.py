"""Write Foundry run records as documented in ``docs/run-records.md``.

The process receives its run id as ``FOUNDRY_RUN_ID`` and writes two files
next to its results:

* ``observed.attempt<N>.json``, the witness: what this process actually ran
  on. A run reaches ``done`` only with one. Written in a ``finally`` block.
* ``metrics.json``: one row per number, with exactly ``benchmark``,
  ``metric``, ``horizon``, ``seed`` and ``value``.

:data:`WITNESS_FIELDS` and :data:`METRIC_FIELDS` define the version 1
format. A file with a field missing or extra is refused.

Example:
    >>> config_sha({"lr": 0.001, "epochs": 2})
    'da1dca8eecbe78ba'
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import torch

#: Every field of the witness, and nothing else.
WITNESS_FIELDS = (
    "attempt",
    "captured_at",
    "config_sha",
    "cpu_threads",
    "device",
    "device_name",
    "experiment_id",
    "peak_vram_mb",
    "run_record_format",
    "wall_seconds",
)
#: Every field of a metrics row, and nothing else.
METRIC_FIELDS = ("benchmark", "metric", "horizon", "seed", "value")
#: The environment variable set by whatever launches the run.
EXPERIMENT_ENV = "FOUNDRY_RUN_ID"


class SidecarError(RuntimeError):
    """A run-record file cannot be written in the documented format."""


def experiment_id(environ: Mapping[str, str] | None = None) -> int:
    """Return the id supplied by the run's launcher.

    Args:
        environ: The environment; ``os.environ`` by default.

    Returns:
        The run id the launcher set.

    Raises:
        SidecarError: If ``FOUNDRY_RUN_ID`` is unset or not an integer.
            A witness without it can never be matched to its run.
    """
    env = os.environ if environ is None else environ
    raw = env.get(EXPERIMENT_ENV, "")
    if not raw:
        raise SidecarError(
            f"{EXPERIMENT_ENV} is not set: the launcher must give the run"
            " an integer id, and without it the witness matches no run"
        )
    try:
        return int(raw)
    except ValueError:
        raise SidecarError(
            f"{EXPERIMENT_ENV}={raw!r} is not the integer id of a run"
        ) from None


def config_sha(config: Mapping[str, object]) -> str:
    """Hash the configuration as the process loaded it.

    Take sha256 of the JSON with sorted keys and keep the first 16 hex
    characters.

    Args:
        config: The loaded configuration, of JSON values.

    Returns:
        The 16-character hash.
    """
    canonical = json.dumps(config, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _rank(env: Mapping[str, str]) -> int:
    for name in ("RANK", "SLURM_PROCID"):
        if name in env:
            return int(env[name])
    return 0


def _device_info(device: str) -> tuple[str | None, int | None]:
    """Return the accelerator's name and peak memory in MB, or two Nones."""
    # ROCm reports device information through the CUDA API.
    cuda_like = device.startswith("cuda") or device == "rocm"
    if cuda_like and torch.cuda.is_available():
        peak = torch.cuda.max_memory_allocated()
        return torch.cuda.get_device_name(0), peak // (1024 * 1024)
    if device == "mps" and torch.backends.mps.is_available():
        peak = torch.mps.driver_allocated_memory()
        return "Apple MPS", peak // (1024 * 1024)
    return None, None


def _cpu_threads(env: Mapping[str, str]) -> int | None:
    if "OMP_NUM_THREADS" in env:
        return int(env["OMP_NUM_THREADS"])
    return os.cpu_count()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def write_witness(  # pylint: disable=too-many-arguments
    results: Path,
    config: Mapping[str, object],
    wall_seconds: int,
    device: str,
    *,
    environ: Mapping[str, str] | None = None,
    now: Callable[[], str] = _now,
) -> Path | None:
    """Write ``observed.attempt<N>.json`` for this process, on rank 0 only.

    Call it from the run's ``finally`` block, so a failed run is witnessed
    too.

    Args:
        results: The run's results directory.
        config: The configuration as loaded, after every override.
        wall_seconds: Wall-clock seconds the run took.
        device: The device the tensors ran on, such as ``"cuda"``.
        environ: The environment; ``os.environ`` by default.
        now: The clock, for tests.

    Returns:
        The sidecar's path, or ``None`` on any rank but 0.

    Raises:
        SidecarError: If ``FOUNDRY_RUN_ID`` is missing, or the attempt's
            witness already exists: a witness is never rewritten.
    """
    env = os.environ if environ is None else environ
    if _rank(env) != 0:
        return None
    attempt = int(env.get("SLURM_RESTART_COUNT", "0"))
    device_name, peak_vram_mb = _device_info(device)
    witness = {
        "attempt": attempt,
        "captured_at": now(),
        "config_sha": config_sha(config),
        "cpu_threads": _cpu_threads(env),
        "device": device,
        "device_name": device_name,
        "experiment_id": experiment_id(env),
        "peak_vram_mb": peak_vram_mb,
        "run_record_format": 1,
        "wall_seconds": wall_seconds,
    }
    results.mkdir(parents=True, exist_ok=True)
    path = results / f"observed.attempt{attempt}.json"
    if path.exists():
        raise SidecarError(f"{path} exists: a witness is never rewritten")
    path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    return path


def _check_row(index: int, row: Mapping[str, object]) -> None:
    if set(row) != set(METRIC_FIELDS):
        raise SidecarError(
            f"metrics row {index} has {sorted(row)}; it needs exactly"
            f" {', '.join(METRIC_FIELDS)}"
        )
    for name in ("benchmark", "metric"):
        value = row[name]
        if not isinstance(value, str) or not value.strip():
            raise SidecarError(f"metrics row {index}: {name} must be text")
    for name in ("horizon", "seed"):
        value = row[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SidecarError(
                f"metrics row {index}: {name} must be an integer of 0 or more"
            )
    value = row["value"]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise SidecarError(
            f"metrics row {index}: value must be a finite number"
        )


def write_metrics(results: Path, rows: Sequence[Mapping[str, object]]) -> Path:
    """Write ``metrics.json`` only when every row is valid.

    Args:
        results: The run's results directory.
        rows: One mapping per number, with exactly :data:`METRIC_FIELDS`.

    Returns:
        The file's path.

    Raises:
        SidecarError: If there are no rows, or a row has a field missing,
            extra, or of the wrong kind. Nothing is written then.
    """
    if not rows:
        raise SidecarError("metrics.json needs at least one row")
    for index, row in enumerate(rows):
        _check_row(index, row)
    ordered = [{name: row[name] for name in METRIC_FIELDS} for row in rows]
    results.mkdir(parents=True, exist_ok=True)
    path = results / "metrics.json"
    path.write_text(json.dumps(ordered, indent=2) + "\n")
    return path
