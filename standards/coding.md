---
type: Standard
title: Coding Standard
description: The numbered rules for Python code in research-foundry and its generated projects, covering documentation, typing, compatibility, static checks, errors and template conformance.
resource: /standards/coding.md
tags: [standard, coding, python, typing, linting]
timestamp: 2026-10-02T00:00:00Z
status: accepted
version: 1.0.0
---

# Coding standard

Version 1.0.0. This standard covers Python in research-foundry's
tools and hooks and in every generated project. Generated code is production
code: rendering it from a template does not lower the bar.

**Sources.** The repository files cited below were opened on 2026-10-02. A
source that was not available locally is marked and must be
opened before this proposal is accepted.

## Rules

### CS1. Public Python has complete Google-style docstrings

- **Rule:** Every public module, class, function and method has a Google-style
  docstring with a summary line, `Args:`, `Returns:` (or `Yields:`), `Raises:`
  and an `Examples:` section whose example runs as a doctest. Sections apply
  where the documented object has that part of the contract. Every private
  helper has at least a one-line summary. Follow the exact form and line limit
  in the public docstring rule (PD4). Docstring coverage for public names is
  100%.
- **Why:** generated API documentation is only complete when every public name
  explains its contract, failures and use in one predictable form.
- **Example:** a function that can refuse an unavailable device documents the
  requested device under `Args:`, the selected device under `Returns:`,
  the refusal under `Raises`, and one deterministic call under `Examples`.
- **Source:** [the public docstring rule (PD4)](public-documentation.md#pd4-docstrings-are-google-style-and-fit-in-79-columns)
  and [Interrogate, "Usage"](https://interrogate.readthedocs.io/en/latest/#usage).
- **Enforced by:** Ruff's pydocstyle `D` rules with
  `convention = "google"`, run by the pre-commit hook named
  `ruff (docstrings, Google convention)`. The 100% public docstring coverage
  gate is not yet enforced; add Interrogate to `make lint`.

### CS2. Every docstring example is a doctest

- **Rule:** Code in every `Examples` section is runnable doctest syntax and
  runs under `make ci`. Output is deterministic and checks an exact value or
  shape rather than an uncontrolled random value.
- **Why:** an example is part of the interface; executing it prevents the
  interface and its documentation from drifting apart.
- **Example:** `>>> seed_everything(7).initial_seed()` followed by `7`.
- **Source:** [Python, "doctest — Test interactive Python examples"](https://docs.python.org/3/library/doctest.html).
- **Enforced by:** Not yet enforced; add `--doctest-modules` to
  [the repository pytest configuration](../.dev-config/pytest.ini) so the root
  `make ci` runs doctests. Generated Python projects already enable
  `--doctest-modules` in their pytest configuration and run it through
  `make coverage` and `make ci`.

### CS3. Python is fully and honestly typed

- **Rule:** Annotate every function and method signature and every variable
  whose type is not obvious. Keep `mypy --strict` clean. Do not use bare `Any`
  without a nearby comment that explains why the boundary cannot be typed.
  Improve annotations instead of adding runtime casts merely to satisfy the
  checker.
- **Why:** static types make data and control boundaries reviewable without
  changing runtime behaviour or concealing uncertainty.
- **Example:** parse an untyped JSON value into a checked domain type at the
  boundary; do not cast the value and assume the payload was valid.
- **Source:** [mypy, "The strict flag"](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict).
- **Enforced by:** Not yet enforced; `make lint` runs strict mypy from
  [the root mypy configuration](../.dev-config/mypy.ini) and the generated
  configuration, but a review or custom lint check must still require the
  explanatory comment on explicit `Any` and reject type-only runtime casts.

### CS4. Python 3.12 is the compatibility floor

- **Rule:** research-foundry and generated projects support Python 3.12 and
  newer. Package metadata requires 3.12 or newer; Black, Ruff, Pylint and mypy
  target 3.12; Continuous Integration (CI) includes Python 3.12. The selected
  development interpreter may be newer without raising the floor.
- **Why:** checking the oldest supported version prevents newer syntax and
  standard-library features from entering code that claims 3.12 support.
- **Source:** [Architecture Decision Record 0010, "Decision"](../docs/adr/0010-python-floor.md#decision).
- **Enforced by:** `make lint` uses the tool configurations, generation guards
  reject an interpreter below the floor, and
  [the CI workflow](../.github/workflows/ci.yml) runs Python 3.12, 3.13 and
  3.14; functional Python-version tests check the rendered projects.

### CS5. Formatting, imports and lint have one checked configuration

- **Rule:** Black formats Python at 79 columns, isort orders imports with its
  Black profile, Flake8 checks style, Pylint checks code quality, and Ruff
  checks docstrings. Do not add an inline ignore without a narrow reason on
  that line.
- **Why:** one automated shape keeps reviews about behaviour, while separate
  configurations make each check and exception visible.
- **Example:** `# noqa: B017 - torch raises its own unpickling error` gives the
  checker and the reason together.
- **Source:** [the pre-commit configuration, "local hooks"](../.pre-commit-config.yaml#L25)
  and [Black, "The Black code style"](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html).
- **Enforced by:** `make fmt` applies Black and isort; `make lint` runs Black,
  isort, Flake8, Pylint and Ruff through `.pre-commit-config.yaml` in the root
  and in generated Python projects.

### CS6. Refusals name the problem and its fix

- **Rule:** Invalid, unavailable or unsafe input is refused with a complete
  sentence that names the problem and the action that fixes it. Do not silently
  choose another device, mode, path, configuration or implementation.
- **Why:** silent fallback makes a run appear valid while changing the
  experiment or deployment underneath it.
- **Example:** a missing `SLURM_CPUS_PER_TASK` value under Slurm is refused and
  tells the user to request `--cpus-per-task`; a missing GPU is not changed to
  CPU.
- **Source:** [Architecture Decision Record 0010, "Consequences"](../docs/adr/0010-python-floor.md#consequences)
  and [Slurm, "--cpus-per-task"](https://slurm.schedmd.com/sbatch.html#OPT_cpus-per-task).
- **Enforced by:** Not yet enforced; existing unit and functional guard tests
  check specific refusals, but code review and a test for every new guard must
  check both the refusal and its corrective message.

### CS7. Generated Python meets the same standard

- **Rule:** Every rendered project passes its own `make ci`. Every template
  answer that changes files appears in the template matrix, including refused
  combinations, and a successful variant also passes its cruft update check.
- **Why:** checking only template source misses invalid rendered syntax,
  conditional omissions and configurations that fail after generation.
- **Example:** the matrix generates a variant, installs it, runs its `make ci`,
  applies a shared-base change with cruft, and runs `make template-check`.
- **Source:** [the template matrix, module contract](../tools/template_matrix.py)
  and [the Makefile, `template-matrix` target](../Makefile#L31).
- **Enforced by:** `make template-matrix`, the functional template-matrix
  tests, and the nightly `make test-heavy-code`, `make test-heavy-software`
  and `make test-heavy-paper` jobs.
