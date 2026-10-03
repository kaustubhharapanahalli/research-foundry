---
type: ADR
title: "ADR 0011: MkDocs for Generated Methodology Documentation"
description: Why generated methodology projects use MkDocs Material and mkdocstrings, and how the optional theme is selected.
resource: /docs/adr/0011-methodology-mkdocs.md
tags: [adr, methodology, documentation, mkdocs, templates]
timestamp: 2026-10-03T00:00:00Z
status: accepted
---

# ADR 0011: MkDocs for generated methodology documentation

## Context

The public documentation standard already specifies MkDocs, Material and
mkdocstrings, while the methodology template still generated a Sphinx
toolchain. That mismatch gave generated projects a different page syntax,
reference system and publishing configuration from the standard they were
expected to follow.

## Decision

Generated methodology projects use MkDocs Material for the site and
mkdocstrings for the Python API reference. Markdown is the syntax for pages
and docstrings. Material supplies search, a light-and-dark palette toggle and
admonitions; strict MkDocs builds make warnings fail. How-to pages include
their tested `docs_src/` examples with snippets. The `docs_theme` answer
selects the default Material styling or a custom palette, fonts and placeholder
branding.

The template drops the Read the Docs configuration and Sphinx autosummary
scaffolding. It does not configure a publishing workflow; each project
chooses how to publish its site.

## Consequences

- `make docs` builds with `mkdocs build --strict`; `make docs-coverage` checks
  public API modules, docstring coverage and public-page frontmatter.
- A project can switch `docs_theme` later through
  `cruft update --variables-to-update`.
- Generated projects use one Markdown syntax for prose, snippets and API
  content, while hosting and versioned documentation remain project choices.
