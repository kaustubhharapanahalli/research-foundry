---
type: Reference
title: Foundry Run Records
description: Version 1 of the witness and metrics files that a generated methodology project can write for each run.
resource: /docs/run-records.md
tags: [runs, records, reproducibility, json]
timestamp: 2026-10-02T00:00:00Z
---

# Foundry run records

Version 1 records a run in two JavaScript Object Notation (JSON) files beside
its results. A generated methodology project includes the writer when
`run_records=yes`; any tool may read the files.

## Files and write timing

`observed.attempt<N>.json` is the witness for restart attempt `N`. Call
`write_witness()` from the training entry point's `finally` block so a failed
run is witnessed too. Only rank 0 writes it. The writer refuses to replace an
existing witness, so a later process cannot erase what an attempt did.

`metrics.json` is an array with one object per reported number. Call
`write_metrics()` when the run has results. It validates all rows first and
writes nothing unless every row is valid.

## Witness fields

The witness contains exactly these fields:

| Field               | Type            | Meaning                                                                  |
| ------------------- | --------------- | ------------------------------------------------------------------------ |
| `attempt`           | integer         | Restart attempt from `SLURM_RESTART_COUNT`, or 0 when unset.             |
| `captured_at`       | string          | Coordinated Universal Time timestamp produced by `datetime.isoformat()`. |
| `config_sha`        | string          | The 16-character configuration hash described below.                     |
| `cpu_threads`       | integer or null | `OMP_NUM_THREADS` when set; otherwise the CPU count visible to Python.   |
| `device`            | string          | Device requested by the run, such as `cpu`, `cuda` or `mps`.             |
| `device_name`       | string or null  | Accelerator name reported by PyTorch; null for CPU.                      |
| `experiment_id`     | integer         | Run id supplied by the launcher in `FOUNDRY_RUN_ID`.                     |
| `peak_vram_mb`      | integer or null | Peak accelerator allocation in mebibytes; null for CPU.                  |
| `run_record_format` | integer         | Format version; exactly 1 for this document.                             |
| `wall_seconds`      | integer         | Elapsed whole seconds supplied by the training entry point.              |

## Metrics fields

Every metrics row contains exactly these fields:

| Field       | Type    | Meaning                                                                      |
| ----------- | ------- | ---------------------------------------------------------------------------- |
| `benchmark` | string  | Nonblank benchmark or dataset name.                                          |
| `metric`    | string  | Nonblank metric name.                                                        |
| `horizon`   | integer | Forecast horizon, zero or greater.                                           |
| `seed`      | integer | Random seed, zero or greater.                                                |
| `value`     | number  | Finite metric value; booleans, infinity and not-a-number values are invalid. |

No field may be missing or added.

## Configuration hash

The hash identifies the configuration as the process loaded it, after
overrides. Compute sha256 over the UTF-8 bytes of
`json.dumps(config, sort_keys=True)` and keep the first 16 hexadecimal
characters.

For example, `{"lr": 0.001, "epochs": 2}` serializes with sorted keys as
`{"epochs": 2, "lr": 0.001}` and produces `da1dca8eecbe78ba`.

## Environment

The writer reads:

- `FOUNDRY_RUN_ID`: required integer run id;
- `RANK`, then `SLURM_PROCID`: optional integer process rank, with `RANK`
  taking precedence; rank 0 is assumed when neither is set;
- `SLURM_RESTART_COUNT`: optional integer attempt, default 0;
- `OMP_NUM_THREADS`: optional integer CPU thread count;
- the process environment through `os.environ` when no mapping is passed.

## Refusals

The witness is refused when `FOUNDRY_RUN_ID` is unset, blank or not an
integer, or when the witness path already exists. Invalid integer values in
the rank, attempt or CPU-thread variables also stop the write. A nonzero rank
returns without writing; it is not an error.

The metrics file is refused when it has no rows; a row has missing or extra
fields; either text field is blank or not text; a horizon or seed is a
boolean, negative or not an integer; or a value is a boolean, nonnumeric or
nonfinite. Validation happens before the results directory or file is
created.

## Future versions

A version 2 witness will set `"run_record_format": 2`. A reader must inspect
that field before interpreting the rest of the witness and refuse versions it
does not understand. The version 2 document will define whether metrics also
change; version 1 readers must not infer compatibility from the filename.
