---
type: ADR
title: "ADR 0001: The Development Setup"
description: Why this repository uses make as its only command surface, the toolchain under .dev-config, and the test layout it was generated with.
resource: /docs/adr/0001-development-setup.md
tags: [adr, toolchain, testing, setup]
timestamp: {% now 'utc', '%Y-%m-%dT00:00:00Z' %}
status: accepted
---

# ADR 0001: The development setup

## Context

This repository was generated from the foundry `methodology` template. The
template encodes the shared coding, documentation and testing standards, so
every project starts the same way and can take later changes with
`cruft update`.

## Decision

- **`make` is the only command surface.** CI runs `make install` and
  `make ci`, nothing else, so a laptop and CI run the same checks.
- **One source per concern:** dependencies in `pyproject.toml` and `uv.lock`;
  every tool's configuration in `.dev-config/`; every check defined once in
  `.pre-commit-config.yaml`.
- **The toolchain:**
  - black, isort, flake8, pylint and mypy;
  - Ruff for Google-style docstrings only;
  - pytest with doctests, and coverage of at least 90%.
- **Tests:** `tests/unit` and `tests/functional`, with the markers `slow` and
  `gpu`. CI runs everything except `gpu` on CPU. GPU tests run on the target
  machine before any real run.
  {%- if cookiecutter.ml_pytorch == "yes" %}
- **Reproducibility is code, not convention:**
  - `seeding.py` seeds every generator and turns on deterministic algorithms;
  - `device.py` refuses a missing device instead of falling back;
  - `threads.py` refuses a thread budget larger than the CPUs this process may
    use;
  - `runrecord.py` records what each run ran on.
    {%- endif %}

## Consequences

A change to a shared standard arrives through `cruft update`, as a diff to
review. A rule this project must break is written under "Local rules" in
`AGENTS.md`, with the reason.
