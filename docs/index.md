---
type: Guide
title: Templates for research repositories
description: Install research-foundry, create a template project, use its Model Context Protocol server, and cite the repository.
resource: /docs/index.md
tags: [research-foundry, guide, templates]
timestamp: 2026-10-03T00:00:00Z
---

# research-foundry

research-foundry provides Cookiecutter templates for the repositories that
support a research project: its code, workspace, paper, and any application it
grows into. The templates share a common base and are kept current with cruft.

## Install and create a project

Run a template directly with `uvx`:

```bash
uvx research-foundry new <template>
```

Or install the command with pip:

```bash
pip install research-foundry
research-foundry new <template>
```

Use `research-foundry templates` to list templates and
`research-foundry questions <template>` to inspect a template's answers.

## Model Context Protocol server

Run `research-foundry mcp` to start the Model Context Protocol (MCP) server over
standard input and output. It can list templates, describe questions, plan a
project without persistent output, and create or update a project only after
explicit confirmation. The read-only `check_layout` tool checks workspace
paths against the shipped contract.

## Checking a workspace's layout

In a generated workspace, run `make layout-check` to compare its paths with
the template. The check is read-only, and a path in backticks in `AGENTS.md`'s
`## Local rules` section declares a workspace-specific deviation.

## Citing research-foundry

If you build on research-foundry or publish work made with its templates, cite
it using the GitHub **Cite this repository** button. GitHub reads the
repository's `CITATION.cff` file and offers APA and BibTeX citations.

The DOI
[10.5281/zenodo.23123933](https://doi.org/10.5281/zenodo.23123933) is
Zenodo's concept DOI: it names research-foundry as a whole and resolves to the
latest archived version.
