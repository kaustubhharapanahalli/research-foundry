---
type: ADR
title: "ADR 0009: The Paper and Workspace Layout"
description: Why paper and workspace repositories have distinct names and fixed paths, how paper numbers and references enter the build, and which local files stay out of version control.
resource: /docs/adr/0009-paper-and-workspace-layout.md
tags: [adr, paper, workspace, layout, overleaf, reproducibility]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0009: The paper and workspace layout

## Context

A research project can have a methodology repository, a workspace and a
paper. Tools need stable paths between those repositories, while the project
slug used by boards and session names may be shorter than the repository
names people recognize. Paper builds also need one reproducible route from
verified results and references to the submitted Portable Document Format
(PDF), without competing edits between Overleaf and GitHub.

The templates and their tests already enforce these paths. This ADR records
the rules and their reasons in Foundry so a generated project does not need
another repository to explain them.

## Decision

### Names

`project_slug` is the project identifier used by boards and session names.
`repo_base` is the base of repository names and may differ from the slug. The
methodology repository is `<repo_base>`, the workspace is
`<repo_base>-workspace`, and the paper is `<repo_base>-paper`. Keeping the two
answers separate supports a short stable identifier without forcing it to be
the public repository name.

### Paper

Overleaf is the paper's main source because its Git bridge and editor are the
shared authoring surface. A GitHub mirror is optional; when selected it adds
continuous integration, but it does not become the main source.

The paper uses these fixed interfaces:

- `generated/numbers.tex` is generated from verified project results by the
  project's own tooling. It defines `\rnum{label}`, which is how text refers
  to a reported number. Hand-typed result values do not belong in that file
  or in the prose, because they have no reproducible link to a run.
- `references.bib` is the bibliography. One filename keeps local, Overleaf
  and archive builds on the same reference database.
- `make pdf` is the build command and writes `build/paper.pdf`. A single
  command and output path give local checks and continuous integration the
  same artifact; undefined references or citations fail the build.
- `AGENTS.md` and `CLAUDE.md` are local instructions and remain untracked in
  a paper repository. Overleaf turns symlinks into ordinary files, so the
  paper template uses copied local files plus `.gitignore` rather than links.

### Workspace

The workspace owns `datasets/registry.yaml`. It records where each benchmark
is kept and which version is in use. It starts empty because a template cannot
truthfully name a new project's datasets. A methodology repository includes
its own registry only when it is the project root; a paper project uses the
workspace registry so there is one authority.

Every generated repository ignores these five local process outputs:

- `.agent-state/` and `.work/`, which hold transient agent state and work;
- `journal.md`, which is local process material;
- `graphify-out/`, which is generated knowledge-graph output;
- `.venue-check`, which is a local venue-check marker.

They are ignored because generated and process-local files must not become
project history. The shared `.gitignore` keeps the rule identical across all
four templates.

## Consequences

- Skills and tests can refer to this ADR for the paper and workspace contract.
- A project can change its repository wording without changing its slug, or
  vice versa, by answering both explicitly at generation.
- Paper numbers remain reproducible only when project tooling regenerates the
  macro file from verified results.
- Tools can find the workspace registry and local-output exclusions without
  project-specific configuration.

## Related decisions

- [ADR 0012, the workspace path contract](0012-workspace-path-contract.md),
  lists the workflow paths inside a workspace and how a workspace declares its
  own additions. It narrows the workspace part of this decision without
  changing it.
