# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Install

You need [uv](https://docs.astral.sh/uv/), `make`
{%- if cookiecutter.frontend_nextjs == "yes" %}, [pnpm](https://pnpm.io/){% endif %}
{%- if cookiecutter.backend_django == "yes" %} and Docker with Compose{% endif %}.
uv installs Python {{ cookiecutter.python_version }} itself.
{%- if cookiecutter.frontend_nextjs == "yes" %} pnpm installs the version
of itself that `frontend/package.json` names, and downloads the Node version
that file pins.
{%- endif %}

```bash
make install
```
{%- if cookiecutter.backend_django == "yes" %}

## Run

```bash
make run   # Postgres in Docker, then the development server on :8000
```

Postgres listens on `127.0.0.1:{{ cookiecutter.db_port }}`. Copy
`.env.example` to `.env` to change a development value.
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}

With the backend running, in a second terminal:

```bash
make frontend-dev   # the Next.js development server on :3000
```
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}

To run the production images behind the Caddy proxy, set
`DJANGO_SECRET_KEY` and run `docker compose --profile app up --build`,
then open https://localhost:8443. Caddy's own local certificate authority
signs that certificate, so the browser warns until you trust it. On a
server, set `SITE_ADDRESS` to the domain and add `compose.deploy.yaml`,
which publishes ports 80 and 443; Caddy then obtains the certificate
itself.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}

The model gateway starts on its own, with a master key that begins `sk-`:

```bash
LITELLM_MASTER_KEY=sk-... docker compose --profile gateway up
```

It serves no model until `gateway/config.yaml` lists one, and publishes no
port: the backend reaches it at `http://gateway:4000`. `gateway/policy.py`
refuses a request for any model outside `local/` unless the request's
metadata says `"visibility": "public"`.
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}

The backend serves a PyTorch model at `POST /api/inference/score/`. Point
`ML_WEIGHTS` at a file saved with `torch.save(model.state_dict(), path)`;
until then the endpoint answers 503, and no untrained model answers in its
place. `ML_DEVICE` is the device or an error, never a fallback, and
`ML_THREADS` is PyTorch's thread budget for each web worker.
{%- endif %}

## Test

```bash
make test   # unit and functional tests
make ci     # everything CI runs
```
{%- if cookiecutter.backend_django == "yes" %}

`make ci` also checks that every model change has a migration, validates the
OpenAPI schema, runs Django's deployment checklist against the production
settings, and serves the production image against Postgres (`make smoke`).
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}

For the frontend, `make ci` runs ESLint and the TypeScript check, the
Vitest unit and component tests, and the Playwright end-to-end tests
against a production build and the real backend. It merges the coverage of
all three and fails below 90%. Last, it starts both production images
together and checks that the page reports the backend up
(`make smoke-stack`).
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}

For the proxy, `make lint` formats and validates the Caddyfile, and
`make ci` starts the stack behind it and checks it from inside its network
(`make smoke-proxy`):

- TLS 1.2 and 1.3 only;
- each site header exactly once;
- client forwarding headers replaced;
- plain HTTP redirected;
- unknown host names refused.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}

For the gateway, `make ci` checks that it refuses a key without the `sk-`
prefix. It then starts the gateway with two mock models that need no network
(`gateway/tests/smoke.yaml`) and checks:

- the key;
- the health check;
- that the API docs are off;
- each case of the visibility policy (`make smoke-gateway`).
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}

For the model, `make test` also trains a small model twice from one seed and
requires bit-identical weights, and checks that the device and thread
settings refuse what this machine cannot do.
{%- endif %}

## Publishing

The public repository is a curated export of the private one, never a
mirror of it. `make publish-check` builds the export from `HEAD`: every
tracked file except the agent files (`AGENTS.md`, `CLAUDE.md`,
`.agent-state/`, `.work/`, `.claude/`, `journal.md`) and `.publish-deny`.
It refuses the export if any line holds an Overleaf project ID, a home path
or a pattern listed in `.publish-deny`. `make publish REMOTE=<remote>` then
pushes it as one release commit on top of the last one, so no private
history travels.

## Layout
{%- if cookiecutter.backend_django == "yes" %}

- `backend/config/`: settings (`base`, `dev`, `prod`, `test`), URLs and the
  WSGI and ASGI entry points.
- `backend/apps/<domain>/`: one Django app per domain, each with `models.py`
  (tables and every rule), `services.py` (writes), `selectors.py` (reads),
  `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `admin.py`,
  `migrations/` and `tests/`.
- `backend/apps/core/`: the health check and the error handler.
- `backend/apps/accounts/`: the project's user model.
- `backend/apps/notes/`: a worked example of an app. Replace it with your
  first real one.
- `compose.yaml`, `Dockerfile`: Postgres for development, and the production
  image.
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}
- `frontend/app/`: the routes, in route groups such as `(main)/`. They
  compose features and hold no logic.
- `frontend/features/<feature>/`: one folder per feature, with its
  `components/` and its `model/` (plain functions, no React). A feature
  never imports another feature.
- `frontend/components/`: shared UI with no feature knowledge: `layout/`
  (the page frame), `ui/` (small pieces, such as the loading and error
  states) and `shared/` (composites two features use).
- `frontend/hooks/`, `frontend/lib/`: hooks two features share; plain
  TypeScript in `lib/api/`, `lib/domain/` and `lib/format/`; and
  `lib/server/`, code that runs only on the server, such as the calls to
  the backend. An empty folder holds a README saying what goes in it.
- `frontend/config/`, `frontend/types/`, `frontend/styles/`: the navigation
  and security headers, shared types, and the design tokens.
- `frontend/tests/`: `unit/`, `component/`, `integration/`, `e2e/`,
  `a11y/`, `smoke/` and `fixtures/`; below each, the path mirrors the
  source.
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}
- `proxy/Caddyfile`: the reverse proxy, the one public entry point;
  `compose.deploy.yaml` publishes it on a server.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}
- `gateway/`: the LiteLLM gateway's configuration, its model list and the
  visibility policy, with the smoke test's mock models in `tests/`.
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}
- `backend/ml/`: the model and the code around it: seeding, the device,
  the thread budget, the run record and the predictor. Replace `model.py`
  with your own.
- `backend/apps/inference/`: the score endpoint. It stores nothing, so it
  has no models, selectors, permissions, admin or migrations.
{%- endif %}
- `scripts/`: the public export (`publish.py`, for `make publish`)
{%- if cookiecutter.proxy_caddy == "yes" or cookiecutter.gateway_litellm == "yes" %}
  and the checks the smoke targets run inside the compose network
{%- endif %}.
- `docs/adr/`: architecture decision records.
- `.dev-config/`: every lint, type and test configuration.
{%- if cookiecutter.license != "none" %}

## Licence

[{{ cookiecutter.license }}](LICENSE).
{%- endif %}
