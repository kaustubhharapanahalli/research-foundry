---
name: release
description: Release foundry itself - move the Unreleased changelog entries under a version, merge the version through a pull request, push its immutable semantic-version tag, and let the release workflow publish it. Use when foundry's templates are ready for projects to update to, or when asked to "cut a release", "tag foundry" or "bump the template version".
---

# Release (foundry)

The rules are in Foundry's ADR 0001
(`docs/adr/0001-cookiecutter-cruft-shared-base.md`): one version line for
every template, tagged with Semantic Versioning, a changelog in Keep a
Changelog 1.1.0, and a tag that is never moved. This skill applies them. It
is for Foundry only; a generated project's releases follow its own
`CHANGELOG.md`.

## Steps

1. **Check the gates.** `make ci` passes locally, and continuous integration
   and the nightly run (`make test-heavy`, every generated project's own
   `make ci`) are green on the commit to be released. Report the run numbers.
2. **Pick the version.** A change a generated project must act on is a major
   version; a new template, answer or component is minor; a fix is a patch.
   Say which entries decided it.
3. **Prepare the release pull request.** Move the entries below
   `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD`, using the Keep a
   Changelog groups Added, Changed, Deprecated, Removed, Fixed and Security.
   Leave an empty `## [Unreleased]` above it, and set the same version in
   `pyproject.toml`.
4. **Merge before tagging.** Review and merge the release changes through a
   pull request. Never release an unmerged version change.
5. **Ask before pushing the tag.** After the owner's approval, create and push
   `vX.Y.Z` for the merge commit. Projects update to tags, so this is
   outward-facing and permanent.
6. **Watch the release workflow.** It validates the tag and changelog, builds
   the distributions, runs the full generated-project matrix, and publishes
   to Test Python Package Index (TestPyPI). It then waits for the maintainer's
   approval in the `pypi` environment, publishes to the Python Package Index
   (PyPI), and creates the GitHub Release with the changelog notes and built
   distributions attached. A release candidate is published to PyPI as a
   pre-release; pip and uv skip pre-release versions unless explicitly asked
   for one.

## Refusals

- Never move or delete a pushed tag. A mistake gets a new patch release.
- Never tag a commit whose nightly run has not passed.
- Never bypass or approve publication from a private repository.
