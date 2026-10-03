---
type: Standard
title: Testing Standard
description: The numbered rules for tests in research-foundry and its generated projects, covering test levels, functional blocks, determinism, guards, isolation, coverage and the template matrix.
resource: /standards/testing.md
tags: [standard, testing, pytest, coverage, determinism]
timestamp: 2026-10-02T00:00:00Z
status: accepted
version: 1.0.0
---

# Testing standard

Version 1.0.0. This standard covers research-foundry's tests and the
tests delivered by every generated project. A rendered project is tested as a
project, not inferred to work from its template source.

**Sources.** The repository tests, pytest configuration, Makefile, template
matrix and throwaway generator cited below were opened on 2026-10-02. A source
that was not available locally is marked and must be opened
before this proposal is accepted.

## Rules

### TS1. Every test declares its level

- **Rule:** research-foundry tests use the `unit`, `functional` and `heavy`
  markers. Unit tests are fast and isolated; functional tests exercise a whole
  command or pipeline; heavy tests generate a project and run that project's
  checks. Generated Python projects use `unit` and `functional`, with `slow`
  and `gpu` capability markers where those distinctions apply. Unknown markers
  are errors.
- **Why:** explicit levels make the local, CI and nightly test selections
  predictable without hiding tests by filename conventions.
- **Example:** `make test-unit` selects unit tests; `make test-heavy` selects
  generated-project checks that are too large for each push.
- **Source:** [pytest, "Registering markers"](https://docs.pytest.org/en/stable/how-to/mark.html#registering-markers).
- **Enforced by:** `.dev-config/pytest.ini` and generated pytest configurations
  use `--strict-markers`; the Makefile's `test-*` targets select the registered
  marker sets.

### TS2. A functional block has unit and functional tests before it is done

- **Rule:** Each functional block is incomplete until both its focused unit
  tests and its end-to-end functional test exist and pass. Write those tests
  before declaring the block done.
- **Why:** unit tests locate defects; functional tests prove that the pieces
  still compose through the real public boundary.
- **Example:** the public exporter has focused scan and refusal tests plus a
  functional test that publishes to a local bare Git repository.
- **Source:** [the public-export tests, module contract](../tests/functional/test_publish.py)
  and [pytest, "Good Integration Practices"](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
- **Enforced by:** Not yet enforced; add a review checklist that maps every
  functional block to its unit and functional tests, then make the mapping a
  required template-conformance test where the block ships from a template.

### TS3. Determinism and every guard are tested

- **Rule:** Every functional block whose result should repeat has a determinism
  test. Every guard has a test that reaches the rejected condition, checks the
  reason, and checks that the refused operation left no partial output.
- **Why:** reproducibility is behaviour, and an untested guard can silently
  accept invalid work or fail after writing half a result.
- **Example:** generated machine-learning projects compare two same-device
  seeded runs, and sidecar tests assert that invalid rows write no metrics
  file.
- **Source:** [PyTorch, "Reproducibility"](https://docs.pytorch.org/docs/stable/notes/randomness.html) and [the shared determinism test, test contract](../_shared/ml/test_determinism.py).
- **Enforced by:** Not yet enforced; existing shared machine-learning and
  generated-project tests cover their current determinism paths and guards,
  but a review and template-conformance check must require one for each new
  block and guard.

### TS4. A failing test stays strict

- **Rule:** Never delete or weaken an assertion to make a test pass. A real,
  temporarily unresolved defect may be held only as a strict expected failure
  with the defect and reason stated; an unexpected pass fails the suite.
- **Why:** a weakened test converts known missing behaviour into an invisible
  regression and gives a false green result.
- **Example:** use `pytest.mark.xfail(strict=True, reason="issue URL: reason")`,
  not an unconditional skip or a broader assertion.
- **Source:** [pytest, "How to use skip and xfail"](https://docs.pytest.org/en/stable/how-to/skipping.html#xfail-mark-test-functions-as-expected-to-fail).
- **Enforced by:** Not yet enforced; set `xfail_strict = true` in every pytest
  configuration and require review to reject weakened assertions, unreasoned
  skips and expected failures without a tracked defect.

### TS5. Tests do not use the network

- **Rule:** Tests make no network connection. Use local fakes at the subprocess
  boundary: pass a fake runner into unit tests, and use local temporary
  repositories or processes only when a functional test must exercise the real
  command.
- **Why:** network access makes results depend on credentials, availability and
  mutable external state; boundary fakes keep unit tests exact without mocking
  internal implementation.
- **Example:** template-matrix unit tests inject a fake `subprocess.run`, while
  publish functional tests push to a bare repository under `tmp_path`.
- **Source:** [the template-matrix unit tests, fake runner](../tests/unit/test_template_matrix.py)
  and [the publish functional tests, local remote](../tests/functional/test_publish.py).
- **Enforced by:** Not yet enforced; add a pytest network-blocking fixture to
  the root and generated projects. Existing tests use fakes and local resources
  by convention, but no suite-wide check currently refuses a socket.

### TS6. Python branch coverage never falls below 90%

- **Rule:** Run unit and functional tests with branch coverage and fail below
  90% for the Python source under test. Report missing lines; a project may
  raise, but not lower, the threshold.
- **Why:** the gate catches unexercised paths while leaving room for narrow
  platform and defensive branches that need explicit review.
- **Source:** [Coverage.py, "Branch coverage measurement"](https://coverage.readthedocs.io/en/latest/branch.html).
- **Enforced by:** `make coverage` and `make ci`, using `branch = True` and
  `fail_under = 90` in the root and generated coverage configurations.

### TS7. Every variant is built nightly, and the full matrix before a push

- **Rule:** Each heavy variant in `tools/variants.py` is generated, installed
  and run through its own `make ci` every night. Before a change to a template
  is pushed, the full matrix runs: every template and every answer combination
  that changes its files is generated, installed, run through its own
  `make ci` and taken through a cruft update, and each combination the
  template refuses is recorded. Smaller structural and functional checks run
  on every push.
- **Why:** conditional template branches can be correct separately and still
  produce a broken combination after rendering.
- **Example:** nightly jobs split code, software and paper variants so their
  environments fit on separate runners.
- **Source:** [the template matrix, module contract](../tools/template_matrix.py)
  and [the nightly workflow, generated-projects job](../.github/workflows/nightly.yml#L14).
- **Enforced by:** `.github/workflows/nightly.yml` (`make test-heavy-*`) for
  the variants. The full matrix (`make template-matrix`) is run by hand before
  a push and is not yet enforced by a workflow.

### TS8. A test writes only inside its temporary directory

- **Rule:** Tests do not write to the repository, home directory or shared
  system locations. All outputs, fake homes, repositories, caches and generated
  projects live below pytest's `tmp_path` or `tmp_path_factory` directory and
  are removed with it.
- **Why:** an isolated test is repeatable, parallel-safe and cannot corrupt a
  developer's files or leave a later test dependent on residue.
- **Example:** the skill-installer functional tests replace `HOME` with a path
  below `tmp_path`; throwaway projects render beneath their caller-provided
  temporary directory.
- **Source:** [pytest, "How to use temporary directories and files in tests"](https://docs.pytest.org/en/stable/how-to/tmp_path.html).
- **Enforced by:** Not yet enforced; generated pytest marker text states the
  rule for unit tests and current tests use pytest temporary paths, but a
  write-confinement fixture or sandbox check must fail writes outside each
  test's temporary directory.
