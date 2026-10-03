---
type: ADR
title: "ADR 0001: The Workspace Layout"
description: Why this workspace has the folders it has, and why their names are fixed.
resource: /docs/adr/0001-workspace-layout.md
tags: [adr, workspace, layout]
timestamp: {% now 'utc', '%Y-%m-%dT00:00:00Z' %}
status: accepted
---

# ADR 0001: The workspace layout

## Context

Skills and tools find a project's material by path: the dataset registry,
theory documents, literature reviews, experiment configs and accepted
results. A workspace with other names is invisible to them.

## Decision

The workspace keeps the layout it was generated with, from the foundry
`workspace` template. `AGENTS.md` lists each path and what it holds. Every
document carries OKF frontmatter, checked by `make lint`.

## Consequences

Renaming one of these folders breaks the tools that read it. A change to the
layout arrives through `cruft update`, as a diff to review.
