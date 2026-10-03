---
name: release
description: Release foundry itself - move the Unreleased changelog entries under a version, tag it in semantic versioning, and never move a tag. Use when foundry's templates are ready for projects to update to, or when asked to "cut a release", "tag foundry" or "bump the template version".
---

# Release (foundry)

The rules are in Foundry's ADR 0001
(`docs/adr/0001-cookiecutter-cruft-shared-base.md`): one version line for
every template, tagged with Semantic Versioning, a changelog in Keep a
Changelog 1.1.0, and a tag that is never moved. This skill applies them. It
is for Foundry only; a generated project's releases follow its own
`CHANGELOG.md`.

## Steps

1. **Check the gates.** `make ci` passes locally, and CI and the nightly run
   (`make test-heavy`, every generated project's own `make ci`) are green on
   the commit to be tagged. Report the run numbers.
2. **Pick the version.** A change a generated project must act on is a major
   version; a new template, answer or component is minor; a fix is a patch.
   Say which entries decided it.
3. **Move the entries.** Under `## [Unreleased]`, the entries become
   `## [x.y.z] - YYYY-MM-DD`, in the groups Added, Changed, Deprecated,
   Removed, Fixed and Security. Leave an empty `## [Unreleased]` above.
4. **Commit the changelog**, then tag that commit `vX.Y.Z` with an annotated
   tag.
5. **Ask before pushing the tag.** Projects update to tags, so a pushed tag
   is outward-facing and permanent. Wait for the owner's yes.

## Refusals

- Never move or delete a pushed tag. A mistake gets a new patch release.
- Never tag a commit whose nightly run has not passed.
