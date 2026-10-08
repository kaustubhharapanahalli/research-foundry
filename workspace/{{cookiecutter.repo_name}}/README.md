# {{ cookiecutter.project_name }} workspace

{{ cookiecutter.description }}

The code lives in the sibling repository `{{ cookiecutter.repo_base }}`, and
the paper in `{{ cookiecutter.repo_base }}-paper`.

## Layout

- `datasets/registry.yaml`: where each benchmark is kept, and which version.
- `methodology/theory/`: one theory document per functional block.
- `lit-reviews/`: literature reviews, one folder per paper.
- `baselines/`: vendored baselines, never edited in place.
- `experiments/configs/`: experiment configs.
- `results/`: run output. Only each batch's `ACCEPTED.md` is tracked.
- `advisor-logs/`: one record per advisor meeting.
- `presentations/`: decks; shared styles in `presentations/_base/`. Deck
  masters are tracked through Git LFS; install Git LFS, then `make install`
  sets it up.
- `docs/adr/`: decisions about this workspace.

## Checks

```bash
make install
make ci
```
