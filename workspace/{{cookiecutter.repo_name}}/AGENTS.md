# {{ cookiecutter.project_name }} workspace: agent instructions

The workspace of the research project `{{ cookiecutter.project_slug }}`:
notes, theory, literature reviews, experiment configs and results. The code
is the sibling repository `{{ cookiecutter.repo_base }}`, and the paper is
`{{ cookiecutter.repo_base }}-paper`.

## Where things go

Skills and tools read and write these paths, so their names are fixed:

- `datasets/registry.yaml`: where this project keeps each benchmark, by its
  canonical slug.
- `methodology/theory/<block>.md`: one theory document per functional block.
- `lit-reviews/<paper>/`: STORM sessions and drafts for one paper. There is no
  `SYNTHESIS.md`: the literature synthesis is read across the review records
  for each paper, not kept in a file of its own.
- `baselines/<paper>/`: a vendored baseline and its data adapter. Copy it for
  a variant; never edit it in place.
- `experiments/configs/*.yaml`: experiment configs, which dispatch reads.
- `results/<batch>/`: run output, untracked, except each batch's `ACCEPTED.md`.
- `advisor-logs/advisor-sync-<date>.md`: one record per advisor meeting.
- `presentations/<deck>/`: decks, with shared styles in `presentations/_base/`.
- `docs/adr/`: decisions about this workspace.

Every Markdown document except README, AGENTS and CHANGELOG carries OKF
frontmatter (`type`, `title`, `description`, `resource`, `tags`,
`timestamp`). `make lint` checks it.

## Commands

- `make install`: the locked tools and the git hook.
- `make lint`: every check.
- `make ci`: exactly what CI runs.
- `make template-check`: whether the foundry template has moved on;
  `cruft update` brings the change in. Not part of `make ci`.

## Local rules

Rules here override the global standards for this workspace only. Name the
global rule, the override, and why. A rule that is not written here does not
apply.

_None yet._
