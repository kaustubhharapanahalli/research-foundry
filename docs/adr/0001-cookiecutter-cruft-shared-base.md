---
type: ADR
title: "ADR 0001: Cookiecutter Templates, Updated with cruft, Sharing One Base"
description: Why the templates use cookiecutter with cruft rather than copier, and how one shared base reaches every template without copies.
resource: /docs/adr/0001-cookiecutter-cruft-shared-base.md
tags: [adr, cookiecutter, cruft, copier, templates]
timestamp: 2026-10-01T00:00:00Z
status: accepted
---

# ADR 0001: Cookiecutter templates, updated with cruft, sharing one base

## Context

Every research project needs several repositories (code, workspace, paper,
and sometimes an application), and they should start from the same standards.
A standard also changes over time, so a project created last year should be
able to take this year's change.

Three tools were compared on 2026-09-30, from their installed versions and
documentation:

- **copier 9.18.2** updates projects itself, but its documentation recommends
  "1 template = 1 Git repository", because "Git tags are shared across the
  whole Git repository".
- **cookiecutter 2.7.1** supports several templates in one repository: its
  `--directory` option is "for advanced repositories with multi templates in
  it", and a top-level `cookiecutter.json` may list them under `templates`. It
  cannot update a project after creating it.
- **cruft 2.16.0** adds `cruft update` and `cruft check` to cookiecutter. It
  records the template's subdirectory in `.cruft.json` and uses it on update.

## Decision

1. **cookiecutter for the templates, cruft to create and update projects.**
   All templates live in this one repository.
2. **One shared base, reached by an include, never copied.** Cookiecutter
   loads Jinja includes from `['.', '../templates']` relative to the template
   folder (`cookiecutter/generate.py`). Each template's `templates/` is a
   link to `_shared/`, and a shared file is one line in the template:
   `{% include "base/<file>" -%}`.

A spike on 2026-10-01 showed both halves:

- the include resolves when cookiecutter clones the repository from git;
- `cruft update` carries a change in `_shared/` into a project generated
  before the change.

`tests/functional/test_cruft_update.py` now repeats that round trip on every
CI run.

## Consequences

- **cruft is a risk.** It has had no release or commit since 2024-12-25. If it
  breaks, projects can still be generated with plain cookiecutter. A changed
  standard then reaches existing projects by hand.
- **One version line for every template.** A release tag versions the whole
  set, which is also the version of the standards they encode.
- **Releases are reproducible references.** Releases follow Semantic
  Versioning and Keep a Changelog 1.1.0. A change that generated projects
  must act on is major, a new template answer or component is minor, and a
  compatible fix is patch. A released tag is never moved: projects update to
  that tag, so changing it would give the same requested version different
  template contents.
- **Generation hooks run without asking.** Cookiecutter runs hooks by default.
  Hooks here therefore only delete what a project did not choose, touch no
  network, and touch nothing outside the generated project.
- **Includes are whole files.** A template that needs extra lines writes them
  after the include, as `paper/.gitignore` does.

## Alternatives not taken

- **copier with one template asking which kind to build.** This was workable,
  but it was set aside once the user preferred cookiecutter's documented
  support for several templates in one repository.
- **A script that assembles each template from `_shared/`**, with a test that
  the committed result is current. This is the fallback if links ever stop
  working.
- **A generation hook that copies `_shared/`.** Rejected because it is the
  least transparent of the three.
