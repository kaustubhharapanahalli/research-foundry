---
title: {{ cookiecutter.project_name | tojson }}
description: {{ cookiecutter.description | tojson }}
---

# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

```{toctree}
:maxdepth: 2

how-to/index
{%- if cookiecutter.ml_pytorch == "yes" %}
explanation/reproducibility
{%- endif %}
api/index
```
