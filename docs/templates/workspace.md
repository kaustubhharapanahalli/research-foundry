---
type: Guide
title: "Workspace Template Guide"
description: How to generate and update a research workspace, what every template answer controls, and which combinations the template refuses.
resource: /docs/templates/workspace.md
tags: [guide, template, workspace, cookiecutter, cruft]
timestamp: 2026-10-02T00:00:00Z
---

# Workspace template guide

The workspace template creates the private research record around a methodology
repository: theory, literature reviews, baseline notes, experiment
configurations, result placeholders, presentations, advisor logs, and the
project's dataset registry.

## Generate and update

```bash
cruft create https://github.com/kaustubhharapanahalli/research-foundry --directory workspace
```

From the generated repository:

```bash
cruft check
cruft update
make template-check
```

`cruft check` and `make template-check` report whether the template has moved on;
`cruft update` brings its changes into the generated repository for review.

## Questions and output

Where `workspace/cookiecutter.json` has no custom prompt, Cookiecutter displays
the key shown in backticks. A value in braces is rendered from an earlier answer.

| Key              | Prompt                                                  | Choices | Default                                                              | What the answer produces                                                                               |
| ---------------- | ------------------------------------------------------- | ------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `project_name`   | Project name, as people write it                        | Text    | `My Project`                                                         | Human-readable name in the README and local guidance.                                                  |
| `project_slug`   | Project slug (the board label and session names use it) | Text    | `{project_name in lowercase with spaces replaced by hyphens}`        | Stable project identifier in generated guidance and metadata.                                          |
| `repo_base`      | Repository base name (may differ from the slug)         | Text    | `{project_slug}`                                                     | Base used to derive the workspace repository name.                                                     |
| `repo_name`      | `repo_name`                                             | Text    | `{repo_base}-workspace`                                              | Name of the generated root directory and project metadata.                                             |
| `description`    | `description`                                           | Text    | `Research notes, theory, literature reviews and experiment configs.` | Description in the README and `pyproject.toml`.                                                        |
| `python_version` | `python_version`                                        | Text    | `3.14`                                                               | Writes `.python-version` and selects the development interpreter; support still begins at Python 3.12. |
| `github_owner`   | `github_owner`                                          | Text    | `your-github-user`                                                   | Repository ownership references in generated guidance.                                                 |

The internal `_python_floor` key fixes the supported floor at `3.12`, and
`_template_kind` records `workspace`; neither is a question.

Every valid answer set produces the same tree: shared editor, Git, pre-commit,
continuous integration, and Make files; `datasets/registry.yaml`;
`advisor-logs/`, `baselines/`, `experiments/configs/`, `lit-reviews/`,
`methodology/theory/`, `presentations/`, and `results/`; and the workspace layout
architectural decision. The template has no optional directories to remove.
Deck masters in `presentations/` are tracked through Git LFS; install Git LFS,
then run `make install` in the generated workspace to set it up.

## Refused combinations

The pre-generation hook rejects a `python_version` below 3.12 with:
`python_version must be 3.12 or newer.` No other combination is refused.

## Governing decisions

- [Cookiecutter templates, updated with cruft, sharing one base](../adr/0001-cookiecutter-cruft-shared-base.md)
- [The paper and workspace layout](../adr/0009-paper-and-workspace-layout.md)
- [Python 3.12 support floor](../adr/0010-python-floor.md)
