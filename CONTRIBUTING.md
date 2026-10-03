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

## Make a change

Write tests first. Never weaken a test to make a change pass. Follow the rules in
[`standards/`](standards), and record a decision with consequences in
[`docs/adr/`](docs/adr).

Write each commit subject as a sentence saying what is now true. Open one pull
request per change and explain what changed, why it changed, and which tests you
ran.

## Propose a template

Open a [template request](https://github.com/kaustubhharapanahalli/research-foundry/issues/new?template=template-request.yml).
Describe the repository the template should generate, who needs it, the questions
it should ask, the files or components each answer controls, its test surface,
and the standards and architectural decisions it must follow. A proposal should
also explain why an existing template cannot cover the use case.
