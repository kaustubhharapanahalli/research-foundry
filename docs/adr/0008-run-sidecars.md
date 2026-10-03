---
type: ADR
title: "ADR 0008: Run Records"
description: Why a methodology project can write a versioned witness and metrics file for each run, why the format is optional, and why projects write files instead of calling a service.
resource: /docs/adr/0008-run-sidecars.md
tags: [adr, methodology, runs, records, reproducibility]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0008: Run records

## Context

A result needs a witness of what the process actually ran: the loaded
configuration, attempt, device, CPU allocation, elapsed time and stable run
identifier. Without that record, a result directory cannot show whether it
came from the requested configuration or the hardware and restart attempt
that its launcher assigned. Metrics need a similarly small, predictable shape
so a project can compare runs without parsing training logs.

The project that runs an experiment should not need a network connection,
service credentials or a client library merely to preserve that evidence.
Files beside the results survive a failed process, work under any launcher and
can be read by any later tool. The format therefore belongs to Foundry and is
documented in [`docs/run-records.md`](../run-records.md).

## Decision

`run_records` is a methodology answer, `no` by default. With `yes`, the
project gets `src/<package>/sidecars.py` and tests. The answer needs
`ml_pytorch=yes` because the witness records the PyTorch device and its peak
memory; the post-generation hook refuses the unsupported combination.

The writer emits version 1 of two JSON files:

- `observed.attempt<N>.json` is the witness. The launcher supplies the integer
  run id through `FOUNDRY_RUN_ID`. Only rank 0 writes it, the training entry
  point calls it from a `finally` block, and an existing witness is never
  replaced.
- `metrics.json` contains rows of exactly `benchmark`, `metric`, `horizon`,
  `seed` and `value`. The writer validates every row before writing anything.

The witness carries `run_record_format: 1`. Its configuration hash is the
first 16 hexadecimal characters of the sha256 digest of
`json.dumps(config, sort_keys=True)`. CUDA and ROCm device information comes
through PyTorch's CUDA API; Metal Performance Shaders (MPS) uses its own API;
a CPU run records null device name and memory values.

The project writes files rather than calling a service. This keeps the run
independent of any reader and makes the two documented files the complete
interface.

## Left out

- **Mapping project outputs to metric rows.** The writer accepts rows in the
  documented shape; each project decides which results become rows.
- **The training entry point.** Each project's runner decides where the call
  belongs. The functional test demonstrates the witness in a `finally` block.
- **A particular reader.** Any local or remote tool may consume the files.

## Consequences

- A failed run can still leave a witness, without depending on a service.
- Readers can refuse an unfamiliar `run_record_format` before interpreting
  fields under the wrong contract.
- The field lists in `sidecars.py` and its generated tests must change with a
  future format version.
