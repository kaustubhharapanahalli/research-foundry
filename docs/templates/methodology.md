---
type: Guide
title: "Methodology Template Guide"
description: How to generate and update a research code repository, what every template answer controls, and which combinations the template refuses.
resource: /docs/templates/methodology.md
tags: [guide, template, methodology, cookiecutter, cruft]
timestamp: 2026-10-02T00:00:00Z
---

# Methodology template guide

The methodology template creates the repository that holds a research project's
Python package, tests, experiment-facing utilities, and optional public
documentation. PyTorch support, run records, and a dataset registry are separate
choices so a project receives only the infrastructure it uses.

## Generate and update

Create a project with cruft:

```bash
cruft create https://github.com/kaustubhharapanahalli/research-foundry --directory methodology
```

From the generated repository, inspect and apply template changes with:

```bash
cruft check
cruft update
make template-check
```

`cruft check` and `make template-check` report whether the template has moved on;
`cruft update` brings its changes into the generated repository for review.

## Questions and output

The prompt column reproduces `methodology/cookiecutter.json`. Where that file has
no custom prompt, Cookiecutter displays the key shown in backticks. A value in
braces is a rendered default based on an earlier answer.

| Key                | Prompt                                                                                                                             | Choices                     | Default                                                       | What the answer produces                                                                                                                                                                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_name`     | Project name, as people write it                                                                                                   | Text                        | `My Project`                                                  | Human-readable name in the README, package metadata, documentation, tests, and local agent guidance.                                                                                                                                                              |
| `project_slug`     | Project slug (the board label and session names use it)                                                                            | Text                        | `{project_name in lowercase with spaces replaced by hyphens}` | Stable project identifier in generated guidance and metadata.                                                                                                                                                                                                     |
| `repo_base`        | Repository base name (may differ from the slug)                                                                                    | Text                        | `{project_slug}`                                              | Base for the repository name and default package name.                                                                                                                                                                                                            |
| `repo_name`        | `repo_name`                                                                                                                        | Text                        | `{repo_base}`                                                 | Name of the generated root directory and Python distribution.                                                                                                                                                                                                     |
| `package_name`     | Python package name                                                                                                                | Text                        | `{repo_base with hyphens replaced by underscores}`            | Directory under `src/`, imports, tests, and the Hatch wheel package path.                                                                                                                                                                                         |
| `description`      | `description`                                                                                                                      | Text                        | `A research codebase.`                                        | Project description in the README and `pyproject.toml`.                                                                                                                                                                                                           |
| `author_name`      | `author_name`                                                                                                                      | Text                        | `Your Name`                                                   | Author in `pyproject.toml` and, when public documentation is enabled, `CITATION.cff`.                                                                                                                                                                             |
| `github_owner`     | `github_owner`                                                                                                                     | Text                        | `your-github-user`                                            | Repository links and public documentation configuration.                                                                                                                                                                                                          |
| `license`          | Licence                                                                                                                            | `Apache-2.0`, `MIT`, `none` | `Apache-2.0`                                                  | Renders the selected `LICENSE` and package licence. `none` removes `LICENSE` and omits package licence metadata.                                                                                                                                                  |
| `python_version`   | `python_version`                                                                                                                   | Text                        | `3.14`                                                        | Writes `.python-version` and selects the development interpreter; support still begins at Python 3.12.                                                                                                                                                            |
| `ml_pytorch`       | Include PyTorch, with seeding, device checks and run records?                                                                      | `yes`, `no`                 | `yes`                                                         | `yes` adds NumPy and PyTorch, device, seeding, thread, and run-record modules and their tests, plus determinism and repeat-a-run material. `no` removes those files and `docs/explanation/`.                                                                      |
| `cuda_source`      | Where Linux gets torch: PyPI (CUDA 13, driver 580+) or the CUDA 12.6 index                                                         | `pypi`, `cu126`             | `pypi`                                                        | With PyTorch enabled, `cu126` adds the explicit PyTorch CUDA 12.6 index and Linux source mapping to `pyproject.toml`; `pypi` uses the normal package index.                                                                                                       |
| `public_docs`      | Publish documentation (Sphinx reference, how-to guides, Read the Docs, community files)? Turn on later with cruft update           | `no`, `yes`                 | `no`                                                          | `yes` keeps `docs/`, `docs_src/`, `make/docs.mk`, `.readthedocs.yaml`, community and citation files, documentation tests, and a documentation dependency group. `no` removes that public documentation set; the development setup architectural decision remains. |
| `contact_email`    | Email for conduct and security reports (required with public docs; type it, there is no default)                                   | Text                        | Empty                                                         | With public documentation enabled, renders the private reporting contact in the conduct and security files. Otherwise it produces no file change.                                                                                                                 |
| `dataset_registry` | Is this repository the project's root, holding its dataset registry (a lab project; a paper project's workspace holds it instead)? | `no`, `yes`                 | `no`                                                          | `yes` keeps `datasets/registry.yaml`; `no` removes `datasets/`.                                                                                                                                                                                                   |
| `run_records`      | Write a run record (a witness file and a metrics file) for every run? (needs PyTorch)                                              | `no`, `yes`                 | `no`                                                          | `yes` keeps `sidecars.py`, its unit test, and the dispatched-run functional test. `no` removes those files.                                                                                                                                                       |

The remaining keys are internal, not questions: `_python_floor` fixes the supported
floor at `3.12`, and `_template_kind` records `methodology`.

Every valid project also receives the shared editor, Git, pre-commit, continuous
integration, Python quality, Make, publication, and test files; a `src/` package;
and the core package and installation tests. Choice-specific removals above are
performed after that complete tree is rendered.

## Refused combinations

The post-generation hook stops without accepting these combinations:

- A `python_version` below 3.12: `python_version must be 3.12 or newer.`
- `public_docs=yes` with `license=none`:
  `public_docs=yes needs a licence: choose Apache-2.0 or MIT.`
- `public_docs=yes` without an `@` in `contact_email`:
  `public_docs=yes needs contact_email: type the address.`
- `run_records=yes` with `ml_pytorch=no`:
  `run_records=yes needs ml_pytorch=yes.`

## Governing decisions

- [Cookiecutter templates, updated with cruft, sharing one base](../adr/0001-cookiecutter-cruft-shared-base.md)
- [The public export, `make publish`](../adr/0007-public-export.md)
- [Run records](../adr/0008-run-sidecars.md)
- [Python 3.12 support floor](../adr/0010-python-floor.md)
