---
title: >-
  {{ cookiecutter.project_name }}
description: >-
  {{ cookiecutter.description }}
---

# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

Start with the [how-to guides](how-to/index.md), see
{%- if cookiecutter.ml_pytorch == "yes" %}
the [reproducibility explanation](explanation/reproducibility.md), or browse
{%- else %}
or browse
{%- endif %}
the [API reference](api/index.md).
