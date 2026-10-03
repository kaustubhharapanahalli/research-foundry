"""Record what a run ran on, so its result can be traced and repeated.

A record holds the commit and whether the tree was dirty, the config, the
seed, the device, the library versions, whether ``torch.compile`` was on,
and, once the run ends, its wall time and peak memory.
"""

import json
import platform
import resource
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import torch

Config = dict[str, str | int | float | bool | None]
_PRIMITIVES = (str, int, float, bool, type(None))


class RunRecordError(RuntimeError):
    """The run cannot be recorded faithfully, so it must not start."""


@dataclass(frozen=True)
class RunRecord:  # pylint: disable=too-many-instance-attributes
    """What one run ran on. Every field is JSON-serialisable."""

    commit: str
    dirty: bool
    config: Config
    seed: int
    deterministic: bool
    device: str
    hostname: str
    python: str
    torch: str
    cuda: str | None
    compile: bool
    started_at: str
    sweep_index: int | None = None
    wall_seconds: float | None = None
    peak_memory_bytes: int | None = None


def git_state(repo: Path) -> tuple[str, bool]:
    """Return the commit checked out in ``repo`` and whether it is dirty.

    Args:
        repo: A directory inside a git working tree.

    Returns:
        The full commit hash, and True if there are uncommitted changes.

    Raises:
        RunRecordError: If ``repo`` is not inside a git working tree.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        raise RunRecordError(f"{repo} is not a git working tree") from error
    return commit, bool(status.strip())


def _check_config(config: Config) -> None:
    # torch.load defaults to weights_only=True, which cannot load a config
    # holding objects such as an argparse Namespace or NumPy scalars.
    for key, value in config.items():
        if not isinstance(value, _PRIMITIVES):
            raise RunRecordError(
                f"config[{key!r}] is {type(value).__name__}; a run record "
                "holds only str, int, float, bool or None"
            )


def start_record(  # pylint: disable=too-many-arguments
    repo: Path,
    config: Config,
    *,
    seed: int,
    deterministic: bool,
    device: torch.device,
    compile_model: bool,
    sweep_index: int | None = None,
) -> RunRecord:
    """Build the record for a run that is about to start.

    Args:
        repo: The repository the run's code comes from.
        config: The run's settings, primitive values only.
        seed: The seed passed to ``seed_everything``.
        deterministic: Whether deterministic algorithms are on.
        device: The device from ``resolve_device``.
        compile_model: Whether the model runs under ``torch.compile``.
        sweep_index: The run's position in its seed sweep, if any.

    Returns:
        The record, without the fields only the run's end can fill.

    Raises:
        RunRecordError: If ``repo`` is not a git working tree, or the config
            holds a value that is not a primitive.
    """
    _check_config(config)
    commit, dirty = git_state(repo)
    return RunRecord(
        commit=commit,
        dirty=dirty,
        config=dict(config),
        seed=seed,
        deterministic=deterministic,
        device=str(device),
        hostname=socket.gethostname(),
        python=platform.python_version(),
        torch=torch.__version__,
        cuda=torch.version.cuda,
        compile=compile_model,
        started_at=datetime.now(UTC).isoformat(),
        sweep_index=sweep_index,
    )


def peak_memory_bytes(device: torch.device) -> int:
    """Return the run's peak memory on ``device``, in bytes.

    Args:
        device: The device the run used.

    Returns:
        Peak allocated CUDA memory for a CUDA device; otherwise the
        process's peak resident memory.
    """
    if device.type == "cuda":
        return int(torch.cuda.max_memory_allocated(device))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is in bytes on macOS and kilobytes on Linux.
    return int(peak if sys.platform == "darwin" else peak * 1024)


def finish_record(record: RunRecord, started: float) -> RunRecord:
    """Return ``record`` with its wall time and peak memory filled in.

    Args:
        record: The record from ``start_record``.
        started: ``time.monotonic()`` taken when the run started.

    Returns:
        A new record; the original is unchanged.
    """
    return replace(
        record,
        wall_seconds=time.monotonic() - started,
        peak_memory_bytes=peak_memory_bytes(torch.device(record.device)),
    )


def write_record(record: RunRecord, path: Path) -> None:
    """Write ``record`` to ``path`` as JSON, refusing to overwrite.

    Args:
        record: The record to write.
        path: The file to create.

    Raises:
        RunRecordError: If ``path`` already exists, which would mean two
            runs sharing one output.
    """
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(asdict(record), handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as error:
        raise RunRecordError(f"{path} already exists") from error
