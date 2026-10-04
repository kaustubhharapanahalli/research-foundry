---
title: API reference
description: Every public module, class and function, generated from the docstrings.
---

# API reference

Every public module, class and function in `{{ cookiecutter.package_name }}`.
This page is generated from the docstrings, so it is never out of date.

::: {{ cookiecutter.package_name }}
{%- if cookiecutter.ml_pytorch == "yes" %}

::: {{ cookiecutter.package_name }}.device

::: {{ cookiecutter.package_name }}.seeding

::: {{ cookiecutter.package_name }}.threads

::: {{ cookiecutter.package_name }}.runrecord
{%- endif %}
{%- if cookiecutter.run_records == "yes" %}

::: {{ cookiecutter.package_name }}.sidecars
{%- endif %}
