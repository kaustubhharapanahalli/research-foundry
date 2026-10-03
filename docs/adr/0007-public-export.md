---
type: ADR
title: "ADR 0007: The Public Export, make publish"
description: How a methodology or software project publishes a curated export of its private repository as one release commit, which files it leaves out, which private items it refuses, and why the private history never travels.
resource: /docs/adr/0007-public-export.md
tags: [adr, publish, methodology, software, privacy]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0007: The public export, `make publish`

## Context

Agent instructions and process state are private working material, so no agent
file appears in a public repository: `AGENTS.md`, `CLAUDE.md`,
`.agent-state/`, `.work/` and `.claude/`. That applies to software
repositories and to methodology repositories once their paper is published.

GitHub sets visibility per repository, not per branch, so one repository
cannot keep the agent files private and the code public. A public-facing
project is therefore two repositories: a private one with every branch and
the agent files, and a public one that receives only a curated export. The
three requirements for `make publish` are:

1. leave out the agent files;
2. refuse if a line contains an Overleaf project identifier, a home path or
   a project-specific pattern in `.publish-deny`;
3. push one branch to the public remote as a new release commit, so no
   private history goes with it.

## Decision

`scripts/publish.py` and `make/publish.mk` ship in the `methodology` and
`software` templates, from `_shared/publish/`. The `workspace` and `paper`
templates never become public and do not get them.

| Requirement           | How                                                                                                                                                                                                                           |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leave out agent files | The export is `git archive HEAD` without any path that is, or sits under, `AGENTS.md`, `CLAUDE.md`, `.agent-state`, `.work`, `.claude`, `journal.md` or `.publish-deny`, at any depth                                         |
| Refuse private items  | Built in: Overleaf project IDs and home paths (`/Users/<name>/`, `/home/<name>/`, except a CI runner's). Project-specific hostnames, groups, organisations, board numbers, names and unpublished titles go in `.publish-deny` |
| No private history    | The release commit is built with `git commit-tree` in a fresh repository: its tree is the export and its only parent is the public branch's tip, or none for the first release                                                |

Further rules:

- **The export is `HEAD`**, so a working tree with changes is refused rather
  than published without them.
- **A refusal names the file, the line and the rule**, never the matched
  text, so the refusal itself does not repeat the private item.
- **An export identical to the last release is refused** ("nothing to
  publish"), so a commit that only touched agent files adds no empty
  release.
- **`.publish-deny` holds one regular expression per line**, matched without
  case, and a line that is not a valid expression is refused. The template
  ships it with comments only: the template cannot know a lab's hostnames,
  account group, organisation, board numbers, advisors or unpublished titles,
  and writing examples of them into a public template would be a private item
  itself.
- **`make publish-check`** builds and scans and pushes nothing.
  **`make publish REMOTE=<name or URL>`** pushes. Neither is part of
  `make ci`; pushing is the owner's action.
- **The script uses only the standard library and git**, so it runs before
  `make install`, and it is tested where it is defined, as `_shared/docs/` is.

## Left out

- **Scanning file history.** The export carries no history, so only the
  exported tree is scanned.
- **Secrets.** Every template's pre-commit already runs `detect-private-key`,
  and the `.env` files are ignored. The publish scan covers private context
  that is not necessarily a secret.
- **Creating the public repository**, or its settings. That is outward-facing
  and stays a person's step.
- **Tags and GitHub releases** on the public side. The release commit's
  message names the version (`Release <version>` from `pyproject.toml`);
  tagging it is left to the owner.

## Consequences

- The public repository's history is one commit per release, each built on
  the last, which is what a reader of a published paper's code needs.
- A private item the rules do not know about still gets through. The
  built-in rules catch Overleaf identifiers and home paths; the rest depends
  on `.publish-deny` being kept up to date.
- `scripts/publish.py` and `make/publish.mk` travel into the public copy, so
  its `Makefile` stays valid. Run there, `make publish-check` finds no agent
  files to leave out.
