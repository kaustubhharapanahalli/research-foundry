---
type: ADR
title: "ADR 0002: The Software Template's Layout"
description: Why a software project is one repository with a root Python project and one folder per component, why the backend starts with a custom user model and a worked example app, and what the first build left open.
resource: /docs/adr/0002-software-template-layout.md
tags: [adr, software, django, layout, components]
timestamp: 2026-10-01T00:00:00Z
status: accepted
---

# ADR 0002: The software template's layout

## Context

The `software` template generates an application. It is built from
components chosen at generation: `backend_django` today, and later
`frontend_nextjs`, `proxy_caddy`, `gateway_litellm` and others. Component
boundaries let a project select only the stacks it runs while the root keeps
their shared build, composition and continuous-integration surface. The
backend uses the feature-oriented API layout recorded below.

## Decision

1. **One repository, one folder per component.** The backend is
   `backend/`, and the frontend will be `frontend/`. Root files hold what
   the components share: `compose.yaml`, the `Makefile` and CI.
2. **The Python project sits at the root**, with its code in `backend/`. So
   the shared toolchain, `.dev-config/` and `make/python.mk`, work
   unchanged. Each shared config branches on `backend_django` only for paths
   and plugins, and the other templates render byte for byte as before.
3. **Validation runs before rendering.** A pre-generation hook refuses a
   project with no component, so no half-rendered project is left behind.
4. **A custom user model from the first migration.** Django's documentation
   recommends one for every new project, because switching after the first
   migration means rewriting every table that points at users.
5. **A worked example app (`notes`)** shows the whole layout, with tests
   for every layer. The drift test and the guard tests are generic, so they
   keep working after `notes` is deleted.
6. **Postgres 18.** A new project has no existing database compatibility
   constraint, and the version policy is "always the latest", so the
   template uses 18 with pgvector 0.8.7.

## Consequences

- `make ci` needs Docker: tests run on a real Postgres, and the smoke test
  builds and serves the production image.
- django-stubs-ext is a runtime dependency, because `ModelAdmin[Note]` must
  be subscriptable at runtime for the strict type check.
- These declare support only up to Django 6.0 or Python 3.13 on PyPI:
  drf-spectacular, pytest-django, whitenoise and gunicorn. All of them pass
  the generated project's `make ci` and smoke test on Python 3.14 with
  Django 6.1.
- The frontend component (ADR 0003) adds `frontend/` beside `backend/`. Its checks join
  `make ci` the same way `make/django.mk` joins today.
