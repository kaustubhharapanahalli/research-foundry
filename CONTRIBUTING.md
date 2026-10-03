# Contributing to research-foundry

Thank you for improving research-foundry. Keep each pull request to one change so
that its design, tests, and generated output can be reviewed together.

## Set up the repository

Install the locked toolchain and Git hook:

```bash
make install
```

The Makefile is the command surface:

- `make ci` runs every static check and the non-heavy test suite with coverage.
- `make test` runs the unit and functional tests without slow or heavy tests.
- `make test-heavy` generates every named project variant and runs that
  project's own `make ci`.
- `make template-matrix` generates, installs, checks, and updates every template
  combination that changes its files. It takes hours.

Pass `PYTHON=3.12` to a target to select another interpreter, for example
`make ci PYTHON=3.12`.

## Documentation

`make docs` builds the strict documentation site. `make typecheck`,
`make docstrings` and `make doctest` run the named typing, docstring and
doctest gates.

Every push to `main` builds the site again and publishes it to GitHub Pages at
<https://research-foundry.kaustubhharapanahalli.me/>. The deploy job refuses to
run unless GitHub reports the repository as public.

## Make a change

Write tests first. Never weaken a test to make a change pass. Follow the rules in
[`standards/`](standards), and record a decision with consequences in
[`docs/adr/`](docs/adr).

Write each commit subject as a sentence saying what is now true. Open one pull
request per change and explain what changed, why it changed, and which tests you
ran.

## Make a release

Move the Unreleased changelog entries under a dated version, set that version in
`pyproject.toml`, and merge both changes through a pull request. After the
release commit's continuous integration and nightly matrix pass, push its new
`vX.Y.Z` tag; never move a tag.

The release workflow builds the distributions, reruns the matrix, publishes to
Test Python Package Index (TestPyPI), and pauses for the maintainer's approval in
the `pypi` environment. Approval publishes to the Python Package Index (PyPI)
and creates the GitHub Release with changelog notes and distributions attached.
A release candidate is published to PyPI as a pre-release; pip and uv skip
pre-release versions unless explicitly asked for one.

## Propose a template

Open a [template request](https://github.com/kaustubhharapanahalli/research-foundry/issues/new?template=template-request.yml).
Describe the repository the template should generate, who needs it, the questions
it should ask, the files or components each answer controls, its test surface,
and the standards and architectural decisions it must follow. A proposal should
also explain why an existing template cannot cover the use case.
