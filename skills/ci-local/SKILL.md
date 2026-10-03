---
name: ci-local
description: Run a foundry-generated project's (or foundry's own) make ci locally and diagnose a run that passes on the machine but fails on the GitHub runner, or the reverse. Use before every push, when CI fails after a local pass, or when asked "why does CI fail" or "run CI locally".
---

# CI, locally

CI calls `make install` and `make ci` and nothing else, so the local run and
the runner's are the same commands. A difference between them is a difference
in what they saw. This skill finds it.

## Steps

1. **Stage new files before `make ci`.** `make lint` runs
   `pre-commit run --all-files`, which reads git's list of files. A new
   file git does not track is not linted, so it passes locally and fails once
   it is committed.
2. **Run `make ci`** and report its exact output, including the final status.
   A hook that rewrites files (black, isort, Prettier) fails the run even
   though it fixed them. Stage what it changed, and run again.
3. **Then check that nothing was left behind:** `git status --porcelain` must
   be empty. CI output git does not ignore is a `.gitignore` gap.

## Passes here, fails on the runner

Check these in order, and say which one it was:

- **A file that was untracked here.** See step 1.
- **pylint's duplicate-code check (R0801).** pre-commit splits files into
  batches by CPU count, and R0801 only compares files in the same batch. The
  runner's batches differ from yours. Run pylint once over every directory to
  see what the runner sees:
  `uv run pylint --rcfile <the project's pylintrc> <every source and test directory>`.
- **The runner's disk.** Images and PyTorch environments fill it. foundry's
  nightly frees the runner's unused toolchains first.
- **Pins.** A tool resolved to a newer release on the runner. `uv lock
--check` and the exact pins in `package.json` should prevent it; find the
  one that did not.

## Fails here, passes on the runner

- **Two installs sharing one uv cache.** Running a second project's install
  at the same time once left an environment missing a module
  (`pygments.formatters.terminal`). Rerun with its own `UV_CACHE_DIR`. The
  cause is suspected, not proven.
- **Ports.** A local service holds a port the tests bind. Name it; do not
  stop a service you did not start.

## Refusals

Never push with `--no-verify`, skip a hook, or mark a test skipped to get CI
green. Report the failure with its output instead.
