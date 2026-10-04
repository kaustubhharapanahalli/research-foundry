---
title: Repeat a run exactly
description: Seed every random number generator from one integer, so a run repeats on the same machine.
---

# Repeat a run exactly

Call `{{ cookiecutter.package_name }}.seeding.seed_everything` once, before
the model or any data is created. Pass the generator it returns to each
`DataLoader`, with `{{ cookiecutter.package_name }}.seeding.seed_worker` as
its `worker_init_fn`.

```python
--8<-- "repeat_a_run.py"
```

Run it with `uv run python docs_src/repeat_a_run.py`. It prints `True`: two
runs seeded with the same integer draw the same numbers.
