# {{ cookiecutter.project_name }}: agent instructions

{{ cookiecutter.description }} This is the code repository (the methodology
repo) of the research project `{{ cookiecutter.project_slug }}`. Its
workspace and paper are the sibling repositories
`{{ cookiecutter.repo_base }}-workspace` and `{{ cookiecutter.repo_base }}-paper`.

This file stays private. `make publish` leaves it out of any public copy.

## Commands

`make` is the only command surface:

- `make install`: the locked environment and the git hook.
- `make lint`: every static check.
- `make test`: unit and functional tests, without slow or GPU tests.
- `make ci`: exactly what CI runs, including 90% coverage.
- `make template-check`: whether the foundry template has moved on;
  `cruft update` brings the change in. Not part of `make ci`.
{%- if cookiecutter.ml_pytorch == "yes" %}
- `make test-gpu`: GPU tests, on the target machine, before any real run.
- `make run MODULE=... ARGS=...`: a run, with thread and worker counts as
  flags.
{%- endif %}
{%- if cookiecutter.public_docs == "yes" %}
- `make docs`: the documentation, failing on any warning.
- `make docs-coverage`: fails if a public symbol is missing from the API
  reference.
- `make docs-linkcheck`: checks every external link; needs the network.

Public documentation follows foundry's public documentation standard
(`standards/public-documentation.md`, rules PD1 to PD17), applied by the
`public-docs` skill.
{%- endif %}

Add a dependency with `uv add <package>`, never `uv pip install`.

## Rules for research code

1. **Identical code on every device.** Change it here, commit, sync, and
   check the commit on the machine before a run. A run on other code is not a
   valid result.
2. **No silent fallback.** A missing GPU, dataset or compiler stops the run
   with a message. It never continues on something else.
3. **Every run records** its commit and whether the tree was dirty, its
   config, seed, device, library versions, and whether `torch.compile` was on.
4. **Paths come from the registry**, never hardcoded. Thread and worker
   counts are command-line flags.
5. **A vendored baseline is copied for a variant**, never edited in place, and
   is excluded from lint and formatting.
6. **Tests come first.** Each functional block has a unit and a functional
   test, a determinism test, and a test of each guard. A test is never
   weakened to make it pass.

## Local rules

Rules here override the global standards for this repository only. Name the
global rule, the override, and why. A rule that is not written here does not
apply.

_None yet._
