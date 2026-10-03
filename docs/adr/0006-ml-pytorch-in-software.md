---
type: ADR
title: "ADR 0006: The ml-pytorch Component in the Software Template"
description: How the software template serves a PyTorch model inside its Django backend, which methodology modules it shares, why Linux gets CPU wheels, why the inference app departs from the app layout, and what is left out.
resource: /docs/adr/0006-ml-pytorch-in-software.md
tags: [adr, software, pytorch, ml, django, inference]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0006: The ml-pytorch component in the software template

## Context

A hybrid application may serve a deep-learning model inside its web backend.
The deep-learning code therefore needs to be an optional component of the
`software` template, not only part of `methodology`. ADR 0004 listed that
component before it was built.

A served model still needs the methodology template's reproducibility
contract: deterministic seeding, explicit devices, a run record, bounded
threads, locked platforms and safe checkpoint loading. This ADR says which
requirements carry into a web process and how.

## Decision

### The answer

`ml_pytorch` is a software answer, `no` by default. It needs
`backend_django`, because the model is served through the Django API, and the
pre-generation hook refuses `ml_pytorch=yes` without it. With `no`, the
post-generation hook removes `backend/ml/` and `backend/apps/inference/`.

### What it adds

| Path                      | What it holds                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| `backend/ml/`             | `seeding.py`, `device.py`, `threads.py`, `runrecord.py`, a small `Scorer` model and `Predictor`     |
| `backend/ml/tests/`       | the methodology tests of those modules, the determinism test, and the predictor's tests             |
| `backend/apps/inference/` | `POST /api/inference/score/`: validate the rows, score them, or answer 503 when no model is served  |
| settings                  | `ML_WEIGHTS`, `ML_DEVICE`, `ML_THREADS`, read with `os.environ`, and listed in `.env.example`       |
| `compose.yaml`            | the backend passes `ML_*` and holds `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` |

The four modules and their tests are the methodology template's own files,
included from `_shared/ml/`, not copies. A test renders both templates and
requires the files to be identical.

### Reproducibility requirements for a served model

| Requirement                                      | Here                                                                                                                              |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Seeding, `warn_only=False`, cuDNN, cuBLAS config | `ml/seeding.py`, shared                                                                                                           |
| No silent device fallback, MPS fallback refused  | `ml/device.py`, shared; `ML_DEVICE` is the device or an error                                                                     |
| Determinism test on one device, `torch.equal`    | `ml/tests/functional/test_determinism.py`, shared                                                                                 |
| Run record                                       | `ml/runrecord.py`, shared, for the project's own training script                                                                  |
| Checkpoints as `state_dict`, `weights_only=True` | `Predictor.load`                                                                                                                  |
| Threads                                          | adapted: a server has no command line, so `ML_THREADS` sets the budget and compose holds the three thread variables to it (below) |
| Lock supported platforms                         | `required-environments`: linux x86_64, linux aarch64, darwin arm64                                                                |
| Accelerator source                               | adapted: CPU wheels on Linux (below)                                                                                              |
| `torch.compile`                                  | left out (below)                                                                                                                  |
| Foundry run-record sidecars                      | not part of a request-serving process; methodology owns experiment records                                                        |

### CPU wheels on Linux

A plain `torch` on Linux brings CUDA 13. A web container serving a small
model has no GPU. So Linux takes torch from
`https://download.pytorch.org/whl/cpu`, as an explicit index chosen by the
marker `sys_platform == 'linux'`. macOS takes it from PyPI.

Locked on 2026-10-02, a render resolved `torch 2.14.1+cpu` from the CPU index,
with cp314 manylinux_2_28 wheels for x86_64 and aarch64, and `torch 2.14.1`
from PyPI for macOS arm64.

A project that serves on a GPU changes the index; methodology's `cuda_source`
answer shows the two choices.

### Threads held to a budget

Each web worker is a process, and PyTorch would otherwise start one thread per
CPU in each of them. `ML_THREADS` (1 by default) is passed to
`apply_thread_budget`, which refuses more threads than the process has CPUs.
Compose sets `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS`
from the same setting. That is a backstop for libraries that start their own
thread pools before `apply_thread_budget` runs, and it costs nothing when it is
redundant.

### No weights, no answer

Without `ML_WEIGHTS`, or with a path that is not a file, the endpoint answers
503 with the reason. An untrained model never answers in its place. The
predictor is loaded once per process, on first use. A failed load is not
cached, so weights placed later are picked up without a restart.

### The inference app departs from the app layout

Stateful Django apps use `models.py`, `selectors.py`, `permissions.py`,
`admin.py` and `migrations/`. The inference app stores nothing, so it has none
of them. It keeps `serializers.py`, `views.py`, `urls.py`, `services.py` and
`tests/`. Its view is a plain `APIView`, since there is no queryset, and it
keeps the project's default authentication and `IsAuthenticated`.

## Left out

- **`torch.compile`.** The template serves eagerly. A project that compiles
  adds it with `fullgraph=True`,
  `fail_on_recompile`, and a separate determinism test. The conformance test
  lists this in `DEFERRED`.
- **A weights checksum.** The deployment owns the weights file, and
  `weights_only=True` already refuses a
  file that holds code.
- **Batching across requests, and a model server** (TorchServe, Triton). One
  request scores up to 256 rows in the web process. A project that outgrows
  that adds a service; that is a new component, not an answer.

## Consequences

- A web project with a model gets the methodology determinism and device
  rules without copying them, and a change to `_shared/ml/` reaches both
  templates on `cruft update`.
- The backend image is larger by the CPU build of torch.
- The template matrix multiplies `ml_pytorch`, since it changes the files.
