---
type: ADR
title: "ADR 0001: The Development Setup"
description: Why this repository uses make as its only command surface, the toolchain under .dev-config, and the backend layout it was generated with.
resource: /docs/adr/0001-development-setup.md
tags: [adr, toolchain, testing, setup]
timestamp: {% now 'utc', '%Y-%m-%dT00:00:00Z' %}
status: accepted
---

# ADR 0001: The development setup

## Context

This repository was generated from the foundry `software` template. The
template encodes the shared coding, documentation and testing standards, so
every project starts the same way and can take later changes with
`cruft update`.

## Decision

- **`make` is the only command surface.** CI runs `make install` and
  `make ci`, nothing else, so a laptop and CI run the same checks.
- **One source per concern:** dependencies in `pyproject.toml` and `uv.lock`;
  every tool's configuration in `.dev-config/`; every check defined once in
  `.pre-commit-config.yaml`.
- **The toolchain:** black, isort, flake8, pylint and mypy (strict), Ruff for
  Google-style docstrings, and pytest with coverage of at least 90%.
{%- if cookiecutter.backend_django == "yes" %}
- **The backend** is Django and DRF on Postgres:
  - one app per domain under `backend/apps/`, each in the same shape;
  - rules declared in `Meta.constraints` and enforced by Postgres, with a
    drift test that compares them with the catalogue;
  - a custom user model from the first migration;
  - settings per environment, with production refusing to start without
    its secrets;
  - pgvector enabled by the first migration;
  - a production image built with uv, run by a non-root user, every base
    image pinned by digest.
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}
- **The frontend** is Next.js with React and TypeScript (strict), run with
  the pnpm and Node versions `frontend/package.json` pins:
  - routes in `app/`, one folder per feature in `features/`, server-only
    code in `lib/server/`, with the import direction enforced by ESLint;
  - pages rendered on the server, which reads the backend over the
    network; the browser never calls it;
  - Vitest for unit and component tests, Playwright for end-to-end tests
    against a production build, and axe for accessibility;
  - one coverage report merged from all three, with a 90% floor;
  - a standalone production image, run by a non-root user.
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}
- **The proxy** is Caddy, the only service a server publishes:
  - TLS 1.2 and 1.3, with a certificate it obtains itself;
  - HSTS, Permissions-Policy, COOP and CORP set once for the whole site;
  - client forwarding headers replaced, so the backend can trust them;
  - any other host name refused;
  - read-only, with every capability dropped but binding ports, and with
    memory, CPU and process limits.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}
- **The model gateway** is LiteLLM, on its own network and compose profile:
  - a master key that must start with `sk-`;
  - no API docs, and no outbound metadata calls;
  - an empty model list;
  - a policy that sends content not marked public to `local/` models
    only.
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}
- **The model** is PyTorch, served inside the backend:
  - seeding, device and thread modules shared with research code, with
    their tests;
  - CPU wheels on Linux, from PyTorch's own index;
  - a 503 until weights are configured;
  - a determinism test that trains twice and compares with `torch.equal`.
{%- endif %}

## Consequences

- A change to a shared standard reaches this repository through
  `cruft update`, as a reviewable diff.
{%- if cookiecutter.backend_django == "yes" %}
- Tests need Docker, for Postgres; `make test` starts it.
- `make ci` builds the production image, so it takes longer than the tests
  alone, and catches a broken image before a deployment does.
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}
- Some frontend tools are held below their latest release, because a tool
  that depends on them does not accept the newer one yet. The foundry
  repository records each, and when it lifts (its ADR 0003).
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}
- The proxy has no rate limiting: Caddy has none built in. Add it at the
  host's edge if the site needs it (the foundry repository's ADR 0005).
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}
- The gateway offers no virtual keys. Adding them needs a database and a
  `LITELLM_SALT_KEY` that never changes once set.
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}
- The production image carries the CPU build of PyTorch, so it is larger
  and slower to build. Serving on a GPU means changing the index in
  `pyproject.toml` (the foundry repository's ADR 0006).
{%- endif %}
