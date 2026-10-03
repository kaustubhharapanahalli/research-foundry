# lib/api

Typed clients the browser uses to call the backend's API: one module per
resource, each built on `fetch`. Pages rendered on the server read the
backend through `lib/server/` instead, so most data never needs these.

No React and no JSX: this folder is plain TypeScript, tested in
`tests/unit/lib/api/`.
