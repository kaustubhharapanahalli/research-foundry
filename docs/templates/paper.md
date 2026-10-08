---
type: Guide
title: "Paper Template Guide"
description: How to generate and update a LaTeX paper repository, what every template answer controls, and which combinations the template refuses.
resource: /docs/templates/paper.md
tags: [guide, template, paper, latex, cookiecutter, cruft]
timestamp: 2026-10-02T00:00:00Z
---

# Paper template guide

The paper template creates a LaTeX manuscript with Overleaf as its main source,
fixed paths for generated results and references, venue-aware style selection,
local checks, and an arXiv export.

## Generate and update

```bash
cruft create https://github.com/kaustubhharapanahalli/research-foundry --directory paper
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

Where `paper/cookiecutter.json` has no custom prompt, Cookiecutter displays the
key shown in backticks. A value in braces is rendered from an earlier answer.

| Key              | Prompt                                                           | Choices                              | Default                                                       | What the answer produces                                                                                                                                                                                                                               |
| ---------------- | ---------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `project_name`   | Project name, as people write it                                 | Text                                 | `My Project`                                                  | Human-readable project name in the README and local guidance.                                                                                                                                                                                          |
| `project_slug`   | Project slug (the board label and session names use it)          | Text                                 | `{project_name in lowercase with spaces replaced by hyphens}` | Stable project identifier in generated guidance and metadata.                                                                                                                                                                                          |
| `repo_base`      | Repository base name (may differ from the slug)                  | Text                                 | `{project_slug}`                                              | Base used to derive the paper repository name.                                                                                                                                                                                                         |
| `repo_name`      | `repo_name`                                                      | Text                                 | `{repo_base}-paper`                                           | Name of the generated root directory and project metadata.                                                                                                                                                                                             |
| `paper_title`    | `paper_title`                                                    | Text                                 | `{project_name}`                                              | Title passed to LaTeX in `main.tex`.                                                                                                                                                                                                                   |
| `venue`          | Venue style (article is a plain preprint layout)                 | `iclr`, `neurips`, `icml`, `article` | `iclr`                                                        | Selects the LaTeX package and bibliography style in `main.tex`, the venue-kit path and fetch recipe in `Makefile`, and venue instructions in the README. `article` uses `geometry` and `natbib` and needs no style kit.                                |
| `venue_year`     | Venue year (the style kit is per year)                           | Text                                 | `2027`                                                        | Forms the International Conference on Learning Representations (ICLR), Neural Information Processing Systems (NeurIPS), or International Conference on Machine Learning (ICML) style package, download path, and `venue/<venue><year>` directory name. |
| `github_mirror`  | Also mirror to GitHub, with CI? (Overleaf stays the main source) | `no`, `yes`                          | `no`                                                          | `yes` keeps `.github/dependabot.yml` and `.github/workflows/ci.yml`; `no` removes `.github/`.                                                                                                                                                          |
| `python_version` | `python_version`                                                 | Text                                 | `3.14`                                                        | Writes `.python-version` and selects the tool interpreter; support still begins at Python 3.12.                                                                                                                                                        |

The internal `_python_floor` key fixes the supported floor at `3.12`, and
`_template_kind` records `paper`; neither is a question.

Every valid project also receives `main.tex`, `latexmkrc`, `.chktexrc`,
`references.bib`, `generated/numbers.tex`, section stubs, and `figures/`,
`tables/`, and `venue/` directories, plus shared editor, Git, pre-commit, Make,
and Python-tool metadata. Venue style files are not bundled; `make venue` fetches
them for the chosen venue and year.

For ICML, `make venue` fetches the year-specific style kit from ICML's site.
The 2027 kit was not published when ICML support was added on 2026-10-08, so
the paper matrix variant uses the latest official kit, ICML 2026. To switch an
existing paper, run
`cruft update --variables-to-update '{"venue": "icml", "venue_year": "2026"}'`.

## Refused combinations

The post-generation hook rejects a `python_version` below 3.12 with:
`python_version must be 3.12 or newer.` No other combination is refused.

## Governing decisions

- [Cookiecutter templates, updated with cruft, sharing one base](../adr/0001-cookiecutter-cruft-shared-base.md)
- [The paper and workspace layout](../adr/0009-paper-and-workspace-layout.md)
- [Python 3.12 support floor](../adr/0010-python-floor.md)
