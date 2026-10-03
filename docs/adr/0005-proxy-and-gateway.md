---
type: ADR
title: "ADR 0005: The Caddy Proxy and the LiteLLM Gateway Components"
description: The requirements for the software template's proxy-caddy and gateway-litellm components, which requirements Caddy changes, what is left out and why, and the pinned versions.
resource: /docs/adr/0005-proxy-and-gateway.md
tags: [adr, software, proxy, caddy, gateway, litellm, security]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0005: The Caddy proxy and the LiteLLM gateway components

## Context

This decision adds two optional components to the software template:

- `proxy-caddy`, the one public entry point, which is on by default;
- `gateway-litellm`, a model gateway, which is off by default.

Both need `backend-django`, and the pre-generation hook refuses a project
that asks for either without it.

The proxy must be an unprivileged, digest-pinned public entry point with a
host allowlist, trusted forwarding headers, modern Transport Layer Security
(TLS), security headers, request limits, structured logs, streaming and
container hardening. Caddy was chosen instead of nginx, so the decision below
states how Caddy meets each requirement.

The optional model gateway must be isolated from the database, refuse weak
master-key configuration, avoid metadata and telemetry calls, expose a health
check, hide its documentation endpoints, constrain credentials and reject
models outside its visibility policy. The gateway is not public; only the
backend can reach its network.

The facts about Caddy 2.11.4 and LiteLLM 1.103.2 behind each choice were
tested against the pinned images on 2026-10-02, unless a line cites the
documentation instead.

## Decision

### The proxy

| Requirement                                          | How the template meets it                                                                                                                                         |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unprivileged image, pinned by digest                 | `caddy:2.11.4-alpine@sha256:…`, run as uid 65532                                                                                                                  |
| Configuration from the environment, filtered         | Caddy reads `{$SITE_ADDRESS:localhost}` itself; the backend's `.env.example` test scans the Caddyfile                                                             |
| Host allowlist                                       | one site address; `http://, https:// { abort }` closes any other host's connection unanswered                                                                     |
| Client `X-Forwarded-*` and `Forwarded` replaced      | Caddy replaces `X-Forwarded-For`, `-Proto` and `-Host`, but passes `Forwarded` through, so the Caddyfile removes it                                               |
| `X-Forwarded-Proto` from the real scheme             | the same replacement; `make smoke-proxy` sends a spoofed `http` and still gets 200                                                                                |
| `server_tokens off`                                  | `-Server` and `-Via` on every response, Caddy's own error pages included                                                                                          |
| Loopback only for development                        | `127.0.0.1:${PROXY_PORT:-8443}`; `compose.deploy.yaml` publishes 80 and 443 on a server                                                                           |
| TLS 1.2 and 1.3, Mozilla intermediate                | Caddy's default cipher suites, with `protocols tls1.2 tls1.3` written out                                                                                         |
| HSTS                                                 | set by the proxy; Caddy does not add it on its own                                                                                                                |
| Explicit body limit                                  | `request_body max_size 10MB` (see "Left out or changed", item 2)                                                                                                  |
| JSON access logs                                     | `log { output stdout format json }`                                                                                                                               |
| Unbuffered streaming, App Router pages included      | `flush_interval -1` on every upstream                                                                                                                             |
| Permissions-Policy, COOP and CORP in one place       | the proxy sets them and replaces an upstream's copy; the smoke check counts exactly one of each on a backend path and a frontend page                             |
| `read_only`, `cap_drop`, `no-new-privileges`, limits | all four, plus `cap_add: NET_BIND_SERVICE`: the image grants the binary that file capability, and exec fails without it                                           |
| Tests of each                                        | `make proxy-check` runs `caddy fmt` and `caddy validate`; `make smoke-proxy` checks TLS, headers, forwarding, the redirect and unknown hosts in the running stack |

The proxy also strips `x-middleware-subrequest`, the header
behind CVE-2025-29927. The Caddyfile removes it before any upstream sees it.

Additional settings come from the tests:

- `admin off`;
- `skip_install_trust`, since the root filesystem is read-only;
- `protocols h1 h2`, since HTTP/3's `Alt-Svc` header would advertise the
  container's port 8443 rather than the published 443;
- a header-read timeout and a maximum header size.

The container's health check and metrics are on a loopback-only site, port 2020.

### The gateway

| Requirement                                                 | How the template meets it                                                                                                    |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| ≥ 1.102.2 or 1.103.1, by digest (GHSA-7hp6-4w63-5g45)       | `litellm-non_root:v1.103.2@sha256:…`, outside every affected range                                                           |
| Refuse to start without a master key, checked for `sk-`     | the entrypoint refuses any key not matching `sk-?*` and exits 64; LiteLLM itself started with a key lacking the prefix       |
| `LITELLM_LOCAL_*`, no outbound metadata calls               | all five flags the image reads                                                                                               |
| Its own network, away from the database                     | `gateway-edge`, shared with the backend only                                                                                 |
| `/health/liveliness` health check                           | yes, through the image's `python3`, since it has no curl or wget                                                             |
| `drop_params: false`                                        | yes                                                                                                                          |
| `LITELLM_MODE=PRODUCTION`, `json_logs`, `LITELLM_LOG=ERROR` | yes                                                                                                                          |
| `NO_DOCS`, `NO_REDOC`, `NO_OPENAPI`                         | yes; the smoke check gets 404 from `/docs` and `/openapi.json`                                                               |
| `request_timeout`, workers, restart after N requests        | 600 s, one worker, 10 000 requests                                                                                           |
| `trusted_proxy_ranges: []`, no env or client credentials    | yes                                                                                                                          |
| Drop `--telemetry False`                                    | not passed                                                                                                                   |
| Empty tier table; unknown visibility goes to local only     | `model_list: []`; `gateway/policy.py` refuses with 403 any request for a non-`local/` model whose visibility is not `public` |

The gateway runs under its own compose profile, so `--profile app` never
starts it. `make smoke-gateway` first checks the refusal of a bad key. It
then starts the gateway with `gateway/tests/smoke.yaml`, which adds two
mock models that answer without a network, and checks:

- the key;
- the health endpoint;
- docs off;
- each case of the visibility policy.

## Left out or changed

1. **No rate limiting.** Caddy has no
   built-in rate limiter. The module that adds one,
   `mholt/caddy-ratelimit`, is third-party, at v0.1.0, and needs a custom
   build with `xcaddy`. That would replace a pinned upstream image with one
   the project builds and patches itself. A project that needs rate
   limiting adds it at the host's edge or builds that image deliberately.
2. **The body limit is enforced on read, and not tested.** Caddy applies
   `request_body max_size` as the upstream reads the body: a request over
   the limit gets 413 only once an upstream reads that far. A test that
   sent 11 MB had its connection reset mid-send instead of getting a status
   code, so the smoke check does not include it. Django refuses form
   bodies over 2.5 MB on its own.
3. **No virtual keys.** `LITELLM_SALT_KEY` and a database are needed only
   when virtual keys are wanted. The template offers no
   virtual keys, so it sets neither. LiteLLM uses the master key as the
   salt when none is set. A project that adds virtual keys sets the salt
   key once, before the first key is issued, and never changes it.
4. **The visibility comes from the request.** `policy.py` reads
   `metadata.visibility` from the caller, so it guards against a mistake
   by a trusted backend, not against a hostile client. That is why the
   gateway has no published port: only the backend, on `gateway-edge`,
   can reach it.
5. **Caddy 2.11.4, not 2.11.6.** On 2026-10-02, 2.11.6 was released on
   GitHub but not on Docker Hub. 2.11.4 carries GHSA-6365-7ppr-5r92
   (medium), which needs `forward_auth` and `reverse_proxy` on the same
   route. The template does not combine them. Raise the pin when 2.11.6
   reaches Docker Hub.

## Consequences

- The proxy is the default, so a new software project gets TLS, HSTS and
  forwarded-header handling unless the creator turns it off. Django's
  `DJANGO_TRUST_FORWARDED_PROTO` and `DJANGO_NUM_PROXIES` are set only when
  the proxy is chosen.
- The images in `compose.yaml` sit in a Jinja file, so Dependabot does not
  raise them (ADR 0004, decision 4). foundry's test checks that each image
  is pinned by digest, and raising the pin is manual.
- `make ci` in a project with either component now starts that component's
  container, so CI needs Docker, as it already did for the backend.
