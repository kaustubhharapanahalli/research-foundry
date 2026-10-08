---
type: ADR
title: "ADR 0012: The Workspace Path Contract"
description: Why workspace workflow paths are listed in a shipped contract, how local deviations are declared, and why the layout checker is read-only.
resource: /docs/adr/0012-workspace-path-contract.md
tags: [adr, workspace, layout, contract]
timestamp: 2026-10-08T00:00:00Z
status: accepted
---

# ADR 0012: The workspace path contract

## Context

Workflow tools need stable workspace paths. A generated workspace can add or
move paths, but template freshness alone does not reveal whether those paths
still exist or whether additions have been declared. A contract beside the
workspace template gives the package and generated workspace one tested
source of expected paths.

[ADR 0009, the paper and workspace layout](0009-paper-and-workspace-layout.md),
fixes the workspace's names, its dataset registry and its ignored local
outputs. This decision narrows it to a checked list of workflow paths.

## Decision

Ship `workspace/contract.json` outside the rendered project directory. The
package includes it with the workspace template, and tests compare its
required entries with a fresh render. The checker renders a temporary copy to
derive expected top-level names and reads Git's indexed and visible,
non-ignored paths. It never writes to the checked workspace.

The contract records these paths and roles:

| Path                                  | Used by                                                  |
| ------------------------------------- | -------------------------------------------------------- |
| `datasets/registry.yaml`              | Data adapters resolve dataset locations here.            |
| `methodology/theory/<block>.md`       | Research notes keep each functional block's theory here. |
| `lit-reviews/<paper>/`                | Paper-specific literature notes live here.               |
| `baselines/<paper>/`                  | Baseline code and data adapters live here.               |
| `experiments/configs/*.yaml`          | The dispatcher reads experiment configs here.            |
| `results/<batch>/ACCEPTED.md`         | Accepted run records are kept with each batch.           |
| `advisor-logs/advisor-sync-<date>.md` | Meeting records are kept by date here.                   |
| `.agent-state/<name>.md`              | Working state stays outside version control.             |
| `AGENTS.md`                           | Workspace instructions and Local rules are read here.    |
| `docs/`                               | Workspace documentation pages live here.                 |

A placeholder or glob represents its fixed parent directory. Runtime paths
are allowed to be absent. Top-level additions and missing contract paths can
be declared by naming a path in backticks in the `## Local rules` section of
`AGENTS.md`. The checker reports missing paths, undeclared additions, and a
missing Local rules section; it is read-only.

## Consequences

- The contract stays outside rendered projects but is present in installed
  wheels.
- A generated workspace can run `make layout-check`; it is separate from
  `make ci` because the command uses `uvx`.
- Tests detect contract/template drift, exercise each required path, and
  verify that local declarations and ignored files are interpreted
  consistently.
