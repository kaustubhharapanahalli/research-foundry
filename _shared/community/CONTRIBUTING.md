# Contributing to {{ cookiecutter.project_name }}

Thank you for helping. This page says how to set up, what a change needs,
and how it is checked.

## Set up

You need [uv](https://docs.astral.sh/uv/) and `make`. Then:

```bash
make install
```

## Before you open a pull request

Run what CI runs, and fix anything it reports:

```bash
make ci
```

`make fmt` applies the formatters. Every check is defined once, in
`.pre-commit-config.yaml`, with its configuration in `.dev-config/`.

## What a change needs

- **Tests.** A new or changed function has a unit test, and a new behaviour
  has a functional test. A test is never weakened to make it pass.
- **Docstrings.** Every public module, class and function has a Google-style
  docstring. Its `Example:` must run, because the tests run it.
- **Docs.** A new public symbol appears in the API reference without any
  extra work. A guide's code lives in `docs_src/`, and a test runs it.
  `make docs` must build with no warnings.
- **Deprecations.** Name the version that deprecates it, the version that
  removes it (at least two releases later), and what to use instead.
- **Changelog.** Add a line under "Unreleased" in `CHANGELOG.md`.

## Conduct and security

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).
Report a vulnerability privately, as [`SECURITY.md`](SECURITY.md) describes,
not in an issue.
