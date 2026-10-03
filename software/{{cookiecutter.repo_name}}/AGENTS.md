# {{ cookiecutter.project_name }}: agent instructions

{{ cookiecutter.description }} Generated from the foundry `software`
template.

This file stays private. `make publish` leaves it out of any public copy.

## Commands

`make` is the only command surface:

- `make install`: the locked environment and the git hook.
- `make lint`: every static check.
- `make test`: unit and functional tests.
- `make ci`: exactly what CI runs.
- `make template-check`: whether the foundry template has moved on;
  `cruft update` brings the change in. Not part of `make ci`.
{%- if cookiecutter.backend_django == "yes" %}
- `make db` and `make db-down`: the development Postgres.
- `make run`: migrate, then the development server.
- `make smoke`: the production image, served against Postgres.
{%- endif %}
{%- if cookiecutter.frontend_nextjs == "yes" %}
- `make frontend-dev`: the Next.js development server.
- `make frontend-coverage`: every frontend test, with the merged 90% floor.
- `make smoke-stack`: both production images, run together.
{%- endif %}
{%- if cookiecutter.proxy_caddy == "yes" %}
- `make proxy-check`: `caddy fmt` and `caddy validate` on the Caddyfile.
- `make smoke-proxy`: the stack behind the proxy, checked from inside.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}
- `make smoke-gateway`: the gateway with mock models, and its policy.
{%- endif %}

Add a dependency with `uv add <package>`, never `uv pip install`.
{%- if cookiecutter.frontend_nextjs == "yes" %} Add a
frontend dependency with `pnpm --dir frontend add --save-exact <package>`.
{%- endif %}
{%- if cookiecutter.backend_django == "yes" %}

## Rules for the backend

1. **Rules live in `models.py`**, as `Meta.constraints`, so Postgres
   enforces them for every writer. Services call `validate_constraints()`
   for an early 400; never re-implement a rule in a serializer or view.
2. **Writes go through `services.py`**, reads that need more than a filter
   through `selectors.py`. Views route, authenticate and paginate only.
3. **Views are closed by default.** `IsAuthenticated` is the default
   permission; a view that opens itself says why. List views filter in
   `get_queryset`, because object permissions do not apply to lists.
4. **Postgres for every test**, never SQLite.
5. **Production settings come from the environment.** `prod.py` refuses to
   start without them, and `make lint` runs the deployment checklist.
6. **A model change ships with its migration**; `make lint` refuses one
   without.
{%- endif %}

{%- if cookiecutter.frontend_nextjs == "yes" %}

## Rules for the frontend

1. **Layers point one way:** `app/` uses `features/`, which use
   `components/`, `hooks/` and `lib/`. ESLint refuses an import against
   that direction, between two features, or that climbs with `../`.
2. **The backend is called from the server only**, through
   `lib/server/`. The browser never learns the backend's address.
3. **Named exports**, except where Next requires a default (`app/` and
   the config files).
4. **Every dependency at an exact version.** pnpm refuses a release less
   than a day old, and runs no dependency build script that
   `pnpm-workspace.yaml` does not allow.
5. **Coverage counts what the end-to-end tests reach**, merged with the
   unit tests, and counts a file no test reaches at zero.
{%- endif %}

{%- if cookiecutter.proxy_caddy == "yes" %}

## Rules for the proxy

1. **Headers for the whole site are set in the Caddyfile**, and replace
   any copy an upstream sends: HSTS, Permissions-Policy, COOP and CORP.
{%- if cookiecutter.frontend_nextjs == "yes" %}
   Permissions-Policy also stays in `frontend/config/security.ts` for the
   frontend run alone. A foundry test keeps the two values equal, so change
   both together.
{%- endif %}
2. **The backend trusts the proxy's `X-Forwarded-Proto`**, so no application
   port is ever published past the proxy.
3. **Format before committing:** `make lint` refuses a Caddyfile that
   `caddy fmt` would change.
{%- endif %}
{%- if cookiecutter.gateway_litellm == "yes" %}

## Rules for the gateway

1. **A model that may see private content is named `local/...`.**
   `gateway/policy.py` sends anything else only content marked public.
2. **The visibility comes from the caller**, so the gateway is never
   published: only services on `gateway-edge` reach it.
3. **The master key starts with `sk-`**; the gateway refuses to start
   otherwise.
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}

## Rules for the model

1. **No silent fallback.** A missing device is an error, and so is
   `PYTORCH_ENABLE_MPS_FALLBACK=1`. A missing weights file is a 503, never
   an untrained model.
2. **Checkpoints are `state_dict()` files**, loaded with
   `weights_only=True`. Keep them free of anything but tensors and plain
   values.
3. **Determinism is tested on one device with `torch.equal`.** PyTorch does
   not promise the same numbers across releases, platforms, or CPU and GPU.
4. **Threads are held to `ML_THREADS`** per web worker. Keep workers times
   `ML_THREADS` within the CPUs the backend can use; gunicorn starts one
   worker unless `WEB_CONCURRENCY` says otherwise.
{%- endif %}

## Local rules

Rules here override the global standards for this repository only. Name the
global rule, the override, and why. A rule that is not written here does not
apply.

_None yet._
