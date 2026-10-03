---
type: ADR
title: "ADR 0004: What the Software Template Leaves Out, and Why"
description: The software and web requirements that the template does not meet as written, the reason for each, and where each is carried, after the conformance audit of 2026-10-02.
resource: /docs/adr/0004-software-template-omissions.md
tags: [adr, software, audit, conformance, deferrals]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0004: What the software template leaves out, and why

## Context

On 2026-10-02 the owner found the software template incomplete and asked for
a check of everything present and absent. The required structure was a Django
backend, a feature-oriented Next.js frontend, repository-wide maintenance
checks and explicit import boundaries. The frontend needed route groups,
loading and error states, shared user-interface layers, server-only settings,
and unit, component, integration, end-to-end, accessibility and smoke tests.
The backend needed production settings, database constraints, vector search,
API validation and deployment checks, among them a graceful shutdown on
SIGTERM. Optional proxy, gateway and model
components had to join the same build without changing those boundaries.

The frontend's 35 files were all present. What was missing were the required
shared layers and test kinds, part of the backend specification, and two
repository-level items. The audit added them, listed
in "Built after the audit" below. `tests/functional/test_software_conformance.py`
now checks every requirement on a fresh render. Each requirement the
template still does not meet is listed there in `DEFERRED`, with a reason
and the ADR that carries it. This ADR is that record.

## Decision

1. **Empty shared layers carry a README, not invented code.** The template
   has one example feature. It has no honest use for `components/shared/`,
   `hooks/`, `lib/api/`, `lib/domain/` or `lib/format/`. Each of those
   folders holds a `README.md` saying what belongs there and what it may
   import. `public/` is not created until an asset needs it, but a template
   has to show the shared code layout before it has an honest implementation.
2. **`cruft check` runs as `make template-check`, outside `make ci`.** Putting
   it in `make lint` would need network access and
   credentials for the private foundry repository on every CI run, which a
   generated project's CI does not have. The target refuses a project that
   `cruft create` did not make. A foundry test shows that it fails when the
   template moves on, and passes after `cruft update`.
3. **`migrate --check` is not in `make lint`.** Against CI's fresh database,
   every migration is unapplied, so it would always fail. Run after
   `migrate`, it always passes. It means something only against a deployed
   database, as a deployment step. `makemigrations --check` stays in lint
   and now starts the database first.
4. **Dependabot covers the template's npm and Dockerfile pins only.** Inside Foundry,
   `compose.yaml`, `pyproject.toml` and the paper's TeX Live image sit in
   files that hold Jinja, so Dependabot cannot parse them. Those pins are
   raised by hand. The weekly template pin report now lists them for review.
   foundry's tests check that each image is pinned by
   digest, not that the digest is current. Whether Dependabot
   accepts the template's `{{cookiecutter.repo_name}}` directory is
   unverified until its first run.
5. **No browser matrix.** The template requires Playwright with axe and runs
   it on Chromium. WebKit and Firefox are not promised by this template.
6. **Components not built yet:**
   - **`proxy-caddy` and `gateway-litellm`**, with the proxy stripping
     `x-middleware-subrequest`: built after this ADR. What
     they leave out is in ADR 0005.
   - **`ml-pytorch` as a software component**, for a web app with a model
     inside it: built after this ADR. How it
     carries the methodology requirements, and what it leaves out, is in
     ADR 0006.
   - **`desktop-electron` and `mobile-<stack>`**: these names are reserved so
     no existing path changes when the components arrive.

## Built after the audit

| Requirement                                               | Source                | Now                                                                                         |
| --------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------- |
| Route groups                                              | Context               | `app/(main)/page.tsx`                                                                       |
| `loading.tsx` where the server waits                      | Context               | `app/(main)/loading.tsx`, using `components/ui/state/Pending`                               |
| `components/ui/`, `components/layout/`                    | Context               | `Pending`, `ErrorNotice`, `AppShell` with a skip link, used by the routes                   |
| `config/navigation.ts`                                    | Context               | the one route list; the navigation and the accessibility sweep read it                      |
| `lib/server/env.ts`                                       | Context               | `requiredEnv`, the one reader of server settings                                            |
| Test kinds `integration/`, `a11y/`, `smoke/`, `fixtures/` | Context               | header wiring; axe on every listed route; the stack smoke script; shared test data          |
| Graceful shutdown on SIGTERM                              | Context               | `make smoke-stack` stops the frontend and requires exit 143, not a kill (137)               |
| `VectorField` and `HnswIndex`                             | ADR 0002              | `Note.embedding`, an HNSW cosine index, `similar_notes`, and its test                       |
| `django.contrib.postgres`                                 | needed by `HnswIndex` | installed                                                                                   |
| Every setting in `.env.example`                           | ADR 0004              | 13 settings listed, and a test that refuses one read but not listed, or listed but not read |
| `cruft check`                                             | ADR 0001              | `make template-check` in every template (decision 2)                                        |
| Dependabot on the template's npm pins                     | ADR 0004              | Foundry's `dependabot.yml` (decision 4)                                                     |

## Consequences

- A requirement left out of the template now has to be written into
  `DEFERRED`, or the conformance test has no row for it and the next audit
  finds it.
- The conformance rows cite Foundry's ADRs. When an ADR changes, the rows are
  rechecked against it.
- `make ci` in a generated project does not tell anyone that the template
  has moved on. `make template-check` does, when run by hand or by the
  planned `template-update` skill.
