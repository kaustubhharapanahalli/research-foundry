---
type: ADR
title: "ADR 0003: The Next.js Frontend Component and Its Pins"
description: How the software template's frontend_nextjs component is built and measured, why six of its tools are held below their latest release, and the condition that lifts each hold.
resource: /docs/adr/0003-frontend-component-and-pins.md
tags: [adr, software, frontend, nextjs, coverage, pins]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0003: The Next.js frontend component and its pins

## Context

This decision adds `frontend_nextjs` to the `software` template, beside the
Django backend of ADR 0002. The owner's answers that shape it:

- "always the latest" versions, with Node 26;
- coverage above 90%, end to end as well: measured by Vitest and
  Playwright together, not by unit tests alone.

The frontend uses a feature-oriented folder layout with route files, shared
components, server-only adapters, configuration, styles and tests separated
by responsibility. Taking the latest release of every tool is not always
possible, because some tools declare that they do not accept the latest
release of another yet. This ADR records each such hold, so it can be lifted
the day its condition is met.

## Decision

1. **The frontend needs the backend.** The pre-generation hook refuses
   `frontend_nextjs` without `backend_django`: the frontend reads its data
   from the Django API, and a frontend on its own would need its own
   standards first.
2. **Pages render on the server**, which reads the backend over the
   compose network (`BACKEND_URL`). The browser never calls the backend.
3. **Layers are enforced, not described.** ESLint refuses:
   - an import against `app → features → components, hooks, lib`;
   - an import from one feature into another;
   - an import of `lib/server` from client layers;
   - a `../` import, a cycle, or a default export outside `app/` and the
     config files.
4. **One coverage number.** Monocart merges three sources into one report
   and fails it below 90% on statements, branches, functions and lines:
   - the Vitest unit and component tests;
   - the browser during Playwright, read through `page.coverage`;
   - the Next server during Playwright, read through `NODE_V8_COVERAGE`.

   A coverage build keeps source maps and turns off minification, so the
   numbers map back to the TypeScript.

5. **A file no test reaches counts, at zero.** The merge lists every
   source file under `app`, `features`, `components`, `hooks`, `lib` and
   `config`, compiling each with TypeScript's `transpileModule` for
   Monocart. Without this, a file nothing imports was left out of the
   report and could not lower the number (found 2026-10-02).
6. **Every version is exact**, and the toolchain is pinned in
   `package.json`: pnpm through `packageManager`, and Node through
   `devEngines.runtime`, which pnpm downloads.
7. **The stack is checked whole.** `make smoke-stack` starts both
   production images and asks, from inside the frontend container, for the
   page that says the backend is up. Neither image publishes a host port,
   so the check never collides with a server already running on the
   machine. The first version published `127.0.0.1:8000` and failed on a
   laptop where another API held that port. The check removes both
   containers when it ends. A stopped container keeps the network it was
   created on, and a later `compose down` deletes that network, so the next
   start failed with "network not found" (2026-10-02).

## Holds, and when each lifts

Each row was checked against the installed package's own `package.json` on
2026-10-02.

| Held at                  | Latest it could be | Why it is held                                                                                                                                                                                                         | Lifts when                                                                                                 |
| ------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Vitest 4.1.11            | Vitest 5           | `vitest-monocart-coverage` 4.0.2 depends on `@vitest/coverage-v8` `^4.1.2`. A spike on Vitest 5 merged its Istanbul output with Monocart's and counted the same code differently, so the merged number was wrong.      | `vitest-monocart-coverage` accepts `@vitest/coverage-v8` 5, and the merged report matches the printed one. |
| TypeScript 6.0.3         | TypeScript 7       | `typescript-eslint` 8.71.0 declares `typescript` `>=4.8.4 <6.1.0`.                                                                                                                                                     | `typescript-eslint` widens that range.                                                                     |
| ESLint 9.39.5            | ESLint 10          | `eslint-plugin-import` 2.32.0 and `eslint-plugin-jsx-a11y` 6.10.2 both declare `eslint` up to `^9`.                                                                                                                    | Both accept ESLint 10. `typescript-eslint` and `eslint-config-next` already do.                            |
| `@types/node` 26.6.3     | 26.6.4             | pnpm 12 refuses a release published less than a day before. 26.6.4 was that new when the template was written.                                                                                                         | Already lifted in effect: Dependabot raises it once it is old enough.                                      |
| Node 26.10.0             | the 26 line        | `devEngines.runtime` and the image tag name one exact version, so every machine and the image run the same Node. Node 26 enters long-term support on 2026-10-28.                                                       | Not a hold: raise both together. A test refuses the two disagreeing.                                       |
| `unrs-resolver` no build | its build script   | pnpm 12 runs no dependency build script unless `allowBuilds` names it. The only one asked for is `unrs-resolver`'s, which looks for a native binary that pnpm already installs as an optional dependency. Lint passes. | Its build script starts doing more than that check: read it on each update to `unrs-resolver`.             |

At the owner's request, these lift conditions were re-checked on 2026-10-02
and remained unmet: `vitest-monocart-coverage` 4.0.2 still depends on
`@vitest/coverage-v8` `^4.1.2`; `typescript-eslint` 8.71.0 still declares
`typescript` `>=4.8.4 <6.1.0`; and `eslint-plugin-import` 2.32.0 and
`eslint-plugin-jsx-a11y` 6.10.2 still declare `eslint` only through `^9`.
Dependabot ignores major updates for `vitest`, `@vitest/coverage-v8`,
`typescript` and `eslint`, so it opens no pull requests for those majors. The
weekly pin report lists every hold with its blocker's latest requirement, so a
lift is noticed.

## Consequences

- The generated `make ci` needs pnpm as well as uv and Docker. CI installs
  it with `pnpm/action-setup`, reading the version from
  `frontend/package.json`; so does foundry's nightly run.
- `make ci` builds both production images and a coverage build of the
  frontend, so it is slower than the backend alone.
- An unheld tool that cannot be raised shows up as a failing Dependabot pull
  request. Held majors show up in the weekly pin report; the row above says
  when to lift each hold.
