---
name: publish
description: Make the public copy of a foundry-generated methodology or software repository with make publish-check and make publish - the curated export without agent files or private history. Use when a project or a published paper's code is to go public, when asked to "publish", "make the public repo" or "release the code", or when make publish refuses.
---

# Publish

The rules are in foundry's ADR 0007 (`docs/adr/0007-public-export.md`) and
the generated README's "Publishing" section. This skill runs them. It does
not restate them, and where they disagree, the ADR wins.

## Steps

1. **Commit first.** The export is `HEAD`, and a working tree with changes is
   refused.
2. **Run `make publish-check`** and report its exact output. It builds the
   export and scans it, and pushes nothing.
3. **On a refusal, fix the file, not the rule.** Each finding is
   `path:line: rule`. Remove the private item from that line and commit. Add
   a pattern to `.publish-deny` when the project has a private item no rule
   catches yet: a hostname, an account group or QOS, the lab's organisation,
   a board number, an advisor's name, an unpublished title.
4. **Ask before `make publish REMOTE=<remote>`.** It pushes to a public
   repository, which cannot be taken back once someone has fetched it. Say
   which remote, which branch and which version, and wait for the owner's
   yes.
5. **Report the release commit** the command prints, and that the public
   branch gained exactly one commit.

## Refusals

Do not publish, and say why, when:

- `make publish-check` refuses;
- the owner has not said yes to this push;
- the repository is a workspace or a paper. Those never go public, and their
  templates have no `make publish`.

Never delete a line from `.publish-deny`, weaken a pattern, or move a private
item into an agent file to get an export through. Each of those hides the
item from the scan without removing it.
