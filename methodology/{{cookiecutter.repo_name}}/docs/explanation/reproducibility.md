---
title: Reproducibility
description: What a seeded run repeats, and what it does not.
---

# Reproducibility

A seeded run with deterministic algorithms repeats exactly on one machine,
in one environment. PyTorch does not promise more than that: results may
differ across PyTorch releases, across platforms, and between CPU and GPU.

So the package does three things:

- {py:func}`~{{ cookiecutter.package_name }}.seeding.seed_everything` seeds
  Python, NumPy and PyTorch from one integer. It also makes PyTorch raise an
  error on any operation that has no deterministic version, instead of
  quietly using a non-deterministic one.
- {py:func}`~{{ cookiecutter.package_name }}.device.resolve_device` refuses a
  device that is not there, instead of falling back to the CPU without
  saying so.
- {py:mod}`{{ cookiecutter.package_name }}.runrecord` writes down what a run
  used, so a result can be traced to the code, environment and seed that
  made it.
