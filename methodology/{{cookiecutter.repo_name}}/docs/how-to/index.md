---
title: How-to guides
description: Short answers to one question each.
---

# How-to guides

Each guide answers one question. Its code is a file in `docs_src/`, and a
test runs that file, so the guide stays true.

```{toctree}
:maxdepth: 1

check-the-install
{%- if cookiecutter.ml_pytorch == "yes" %}
repeat-a-run
{%- endif %}
```
