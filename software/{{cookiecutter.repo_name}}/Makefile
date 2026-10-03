# The only command surface. CI calls `make install` and `make ci` only.
include make/python.mk
include make/publish.mk
{%- if cookiecutter.backend_django == "yes" %}
include make/django.mk
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}
include make/nextjs.mk
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}
include make/caddy.mk
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}
include make/litellm.mk
{%- endif %}
{% include "base/template.mk" -%}
