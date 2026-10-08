---
type: ADR
title: "ADR 0013: The Frontend Is a Client-Side Rendered App That Calls the API"
description: Replaces the Next.js server-rendered frontend of ADR 0003 with a client-side rendered React single-page app built by Vite, which renders every page in the browser and calls the Django API directly, so a generated project has one backend; and adds the CORS and CSRF settings that browser writes need.
resource: /docs/adr/0013-frontend-single-page-app.md
tags: [adr, software, frontend, react, vite, cors, csrf, supersedes-0003]
timestamp: 2026-10-07T00:00:00Z
status: proposed
---

# ADR 0013: The frontend is a client-side rendered app that calls the API

**Status: proposed.** Drafted on 2026-10-07 from the owner's answers. Not
accepted until the owner says so; the open questions at the end are settled first.

**Supersedes** ADR 0003, decision 2 ("Pages render on the server, which reads the backend over
the compose network (`BACKEND_URL`). The browser never calls the backend."), and changes
decisions 4 and 7 of the same record. ADR 0003's other decisions, and its pins, stand until the
implementation replaces them.

## Context

ADR 0003 gave the `software` template a Next.js frontend whose pages render on a Node server.
That server reads the Django API over the compose network, and the browser never calls the
backend. A generated project therefore runs two servers that both answer requests: Django, and
the Next.js server in front of it.

The owner reviewed this on 2026-10-07 while designing a generated project with
`frontend_nextjs`. Their words:

- "Browser not calling the backend is not a good approach at all … The browser communicates
  with the backend and the content is dynamically rendered."
- "We need to have just one backend. Two backends don't make sense at all."
- On rendering: "it should query the API for the necessary details. Not have two backends."
- "The data management, manipulation, everything should happen through the API itself."

The owner's existing portfolio site is the reference: a React single-page app, built to
static files, that calls a Django REST Framework API from the browser. Its API address comes
from an environment variable at build time, and Django allows its origins with
django-cors-headers.

**A server is not needed for React.** React's documentation: "Full-stack frameworks do not
require a server. All the frameworks on this page support client-side rendering (CSR),
single-page apps (SPA), and static-site generation (SSG)."
(<https://react.dev/learn/creating-a-react-app>, opened 2026-10-07)

**Why not keep Next.js as a static export.** Next.js can build to static files
(`output: 'export'`), but lists as unsupported "Dynamic Routes without `generateStaticParams()`",
rewrites, redirects, headers, cookies, the proxy and server actions
(<https://nextjs.org/docs/app/guides/static-exports>, Next.js 16.3.8, opened 2026-10-07). A page
for content created at runtime, such as a record added through the app, has no route unless its
URL changes shape.

**Why Vite, not Create React App.** The portfolio uses Create React App, which React deprecated
on 2025-02-14: "we're deprecating Create React App for new apps, and encouraging existing apps to
migrate to a framework, or to migrate to a build tool like Vite, Parcel, or RSBuild."
(<https://react.dev/blog/2025/02/14/sunsetting-create-react-app>, opened 2026-10-07)

## Decision

1. **The frontend is a client-side rendered React single-page app, built by Vite, with React
   Router.** `vite build` writes one HTML shell plus the JavaScript and CSS; no page is
   generated ahead of time. In the browser, React Router picks the page from the URL, and the
   page asks the API for its data and renders it. Content created at run time has a page at
   once, with no rebuild. No Node process runs in production. The owner chose "like portfolio"
   on 2026-10-07, confirmed Vite in place of Create React App, and asked for a client-side
   generated app the same day.

2. **The browser calls the Django API directly** and renders from what the API returns. The
   generated project has one backend: Django.

3. **The API's address is baked in at build time from an environment variable**, as in the
   portfolio. Vite exposes only variables prefixed `VITE_`, "statically replaced at build time".
   Nothing secret goes in one: "VITE\_\* variables should _not_ contain sensitive information
   such as API keys. The values of these variables are bundled into your source code at build
   time." (<https://vite.dev/guide/env-and-mode>, Vite 8.3.1, opened 2026-10-07) One build
   serves one environment.

4. **The backend allows the frontend's origin with django-cors-headers**, configured as its
   documentation says (<https://github.com/adamchainz/django-cors-headers>, opened 2026-10-07;
   supports Django 5.2–6.1):
   - `CorsMiddleware` "placed as high as possible, especially before any middleware that can
     generate responses such as Django's `CommonMiddleware`";
   - an explicit `CORS_ALLOWED_ORIGINS`, read from the environment. Never
     `CORS_ALLOW_ALL_ORIGINS`: "it allows any website to make cross-origin requests to yours";
   - `CORS_ALLOW_CREDENTIALS = True`, so the session cookie travels with the browser's requests.

5. **Browser writes carry a CSRF token.** "CORS and CSRF function independently", so the
   frontend's origin is also in `CSRF_TRUSTED_ORIGINS`. The frontend sends the token in an
   `X-CSRFToken` header on every unsafe request
   (<https://docs.djangoproject.com/en/6.1/howto/csrf/>). In production the frontend and the API
   sit on one registrable domain, for example `app.example.com` and `api.example.com`.
   Browsers treat different ports and subdomains of one domain as the same site
   (<https://developer.mozilla.org/en-US/docs/Glossary/Site>), so the session cookie keeps its
   default `SameSite=Lax`. The CSRF cookie is shared with the frontend through
   `CSRF_COOKIE_DOMAIN`, as the CSRF reference describes for cross-subdomain requests
   (<https://docs.djangoproject.com/en/6.1/ref/csrf/>).

6. **Production settings refuse to start without these values.** This follows the template's
   existing rule that production settings come from the environment: `CORS_ALLOWED_ORIGINS` and
   `CSRF_TRUSTED_ORIGINS` in the backend, and the API address in the frontend build.

7. **Kept from ADR 0003:** layers enforced by ESLint (`app → features → components, hooks,
lib`, no feature-to-feature imports); one merged coverage number with a 90% floor; a file no
   test reaches counts at zero; exact versions; TypeScript in strict mode; and a check of the
   whole stack.

## Consequences

**ADR 0003 changes in three places:**

- decision 2 is replaced by decisions 1–3 above;
- decision 4's coverage merge loses its third source ("the Next server during Playwright"),
  since there is no server; Vitest and the browser during Playwright remain;
- decision 7's stack check asks a browser, not the frontend container, to load the page and
  show the backend up.

**Files expected to change**, from where they mention the server-rendered frontend today
(confirmed at implementation):

- `software/cookiecutter.json` and both hooks: the `frontend_nextjs` option (see "Open
  questions", 2);
- `docs/templates/software.md`;
- the generated `frontend/`: `next.config.ts` and `app/` give way to a Vite entry and React
  Router routes. `lib/server/` is removed, and `lib/api/` becomes the one way to reach the
  backend. `config/security.ts`'s headers move to whatever serves the files. `eslint.config.mjs`
  drops the `lib/server` rule, `vitest.config.ts` drops the `server-only` alias, and
  `scripts/coverage.mjs` drops the Next server source. The `Dockerfile` serves static files.
  `package.json` replaces `next` with `vite` and `react-router`;
- `compose.yaml`: the frontend no longer receives `BACKEND_URL` at run time; the API address is
  a build argument;
- `proxy/Caddyfile`: the `frontend:3000` upstream changes (see "Open questions", 1). The
  `x-middleware-subrequest` strip, there for a Next.js CVE, is no longer needed;
- the generated backend: django-cors-headers (`uv add django-cors-headers`) and the settings in
  decisions 4–6;
- the generated `AGENTS.md` (frontend rule 2) and `docs/adr/0001-development-setup.md`;
- the foundry's own tests that render and check the frontend (`tests/functional/test_software.py`,
  `test_software_conformance.py`, `test_generated_projects.py`).

**Generated projects** take the change through `cruft update`. A project generated with
`frontend_nextjs` is updated after this record is accepted and implemented.

**What a generated project gives up:** pages rendered on the server, so the first paint shows a
loading state until the API answers; Next.js's image optimisation and server actions; and
reading settings at request time (one build per environment).

## Alternatives considered

- **Keep the Next.js server** (ADR 0003 as it stands). Rejected by the owner: two backends.
- **Next.js as a static export.** One backend, and most of the current frontend code stays.
  Rejected because runtime content needs dynamic routes, which a static export does not
  support.
- **Create React App, exactly as the portfolio.** Rejected because React deprecated it on
  2025-02-14.
- **The API's address read at run time from a config file** the app loads at start, so one
  build serves every environment. The owner chose build-time environment variables, as in the
  portfolio.

## Open questions

Settled before this record is accepted.

1. **How the built files are served in production.** Whatever serves them must answer every
   path the app routes, such as `/items/42`, with the same `index.html`, so a refreshed
   page or a shared link is not a 404 (the portfolio runs `serve -s build`, single-page mode).
   Either a small static server on its own
   origin, with CORS as above, or, when `proxy_caddy` is on, Caddy serving the files and routing
   `/api/*` to Django on one origin, so production needs no CORS and development still does.
   The owner asked for CORS "setup correctly", which the first option needs everywhere.
2. **The option's name.** Keep `frontend_nextjs`, which would now be misleading, or rename it
   (for example `frontend_react`). A rename changes the answers stored in a generated project's
   `.cruft.json` on its next update.
3. **Which server serves the files**, if the first answer to question 1: Caddy's file server
   (already pinned by ADR 0005), nginx, or `serve` as in the portfolio.
4. **Where the Content Security Policy and the other page headers are set**, now that no Next.js
   server sends them: the static server, or the proxy.
5. **Versions** of Vite and React Router, checked against the latest releases when implemented
   (the "always the latest" policy of ADR 0003).
