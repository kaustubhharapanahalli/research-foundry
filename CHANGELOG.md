# Changelog

All notable changes to the templates are recorded here. The format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and versions
follow [Semantic Versioning](https://semver.org/). A release tag is never
moved once projects may have been generated from it.

## [Unreleased]

## [0.2.0rc1] - 2026-10-08

### Added

- The workspace template tracks presentation deck masters through Git LFS.
  Existing workspaces can pick this up with `cruft update`, then
  `make install`, which runs `git lfs install --local`. A `.pptx` or `.potx`
  already committed without LFS, anywhere in the repository, converts in one
  new commit with `git add --renormalize .` from a clean working tree;
  earlier commits are not rewritten.
- The paper template's ICML venue. `make venue` fetches the year-specific kit
  from ICML; the official 2026 kit is the latest available because the 2027
  kit was not published as of 2026-10-08. Existing papers can switch with
  `cruft update --variables-to-update '{"venue": "icml", "venue_year": "2026"}'`.
- A workspace layout checker backed by a shipped, tested path contract,
  exposed through the command line and the Model Context Protocol server.
  Only a `Moved:` or `Dropped:` rule excuses a missing required path, and a
  repository the checker does not recognize as a workspace exits 2.
  A generated workspace's `make layout-check` requires 0.2.0 and stops with
  uv's "no solution" until 0.2.0 is published. To try this release
  candidate, run
  `uvx --from 'research-foundry==0.2.0rc1' research-foundry layout .`.
- The methodology template's `docs_domain` answer and GitHub Pages workflow,
  with a public-repository deployment guard and setup instructions.
- The methodology template's `docs_theme` answer selects the generic Material
  palette or a customizable CSS palette with placeholder branding. Existing
  projects can change it later with
  `cruft update --variables-to-update`.

### Changed

- The workspace template no longer points to a separate literature synthesis
  file; existing workspaces can pick up the change with `cruft update`.
- The methodology template's generated documentation moves from Sphinx to
  MkDocs Material and mkdocstrings, with strict builds, API module coverage,
  and no generated Read the Docs configuration. Existing projects can apply
  the update with `cruft update`.

### Fixed

- The documentation site's home page title no longer repeats the site name.

## [0.1.0] - 2026-10-03

The first stable release. It holds everything in 0.1.0rc1 below, and these
changes since.

### Added

- A strict MkDocs Material documentation site with a generated Python API
  reference, light and dark palettes, and published template, run-record and
  architecture-decision guides.
- Named `make typecheck`, `make docstrings` and `make doctest` gates, plus
  `make docs`; continuous integration now builds the site.
- The documentation site is published to GitHub Pages on every push to
  `main`, at <https://research-foundry.kaustubhharapanahalli.me/>.

### Changed

- Every template's `.gitignore` ignores `site/`, where MkDocs builds a site.

### Fixed

- The weekly pin report reads GitHub Container Registry tags with an anonymous
  pull token and matches the current image flavour, rather than treating image
  tags as GitHub releases.
- The template matrix and throwaway generator keep Cookiecutter replay and
  checkout directories in the run's work directory instead of the user's home.

## [0.1.0rc1] - 2026-10-02

### Added

- The installable `research-foundry` Python package, with an offline CLI for
  listing templates and questions, generating projects, checking and applying
  cruft updates, and installing the maintained skills. Wheels carry all four
  templates, restore their shared include trees at runtime, and source
  checkouts remain directly usable.
- A standard-input/output Model Context Protocol (MCP) server with tools to
  list and inspect templates, validate a project plan without persistent
  output, create confirmed projects, and check or apply confirmed updates.
- A tag-driven release pipeline that validates the version and changelog, runs
  the generated-project matrix, publishes through trusted publishing to Test
  Python Package Index and then the Python Package Index after maintainer
  approval, attests the distributions, and creates the GitHub Release. Every
  publishing job independently refuses a private repository. Release
  candidates are published as pre-releases, which pip and uv skip unless
  explicitly asked for one.
- Weekly dependency and security maintenance: grouped Dependabot version
  updates, audits of Foundry and every generated heavy variant, reports for
  template pins hidden from Dependabot, public-repository dependency review,
  and issue upserts for audit failures and stale pins.
- Python 3.12 and newer support for research-foundry and generated projects,
  with continuous integration on Python 3.12, 3.13 and 3.14. Generated
  projects keep their chosen interpreter separate from the 3.12 compatibility
  floor used by package metadata, lint and type-check tools.
- The four templates, `methodology`, `workspace`, `paper` and `software`, each
  rendering the shared base: `.editorconfig` and `.gitignore`.
- The shared base in `_shared/`, reached through each template's `templates/`
  link.
- Tests that every template renders, renders identically twice, leaves no
  template syntax behind, and refuses to render when an include is missing; and
  a round trip proving `cruft update` carries a shared change into an existing
  project.
- CI that only calls `make`, with every action pinned to a commit SHA, and
  Dependabot for actions, uv and pre-commit.
- The `methodology` template:
  - an installable `src/` package built with hatchling;
  - the Python toolchain shared in `_shared/python/`;
  - `make install`, `lint`, `test`, `coverage` and `ci`;
  - Apache-2.0, MIT or no licence.
- With `ml_pytorch`, the `methodology` template adds:
  - PyTorch from PyPI, or from the CUDA 12.6 index on Linux;
  - `seeding.py`, `device.py` (refuses a missing device, never falls back),
    `threads.py` (refuses a thread budget over the CPUs the process may use,
    including under SLURM) and `runrecord.py`;
  - a determinism test, and a test of each guard.
- The `workspace` template:
  - every path the research tools read, named as they expect;
  - an empty dataset registry, and no empty `SYNTHESIS.md`;
  - run output untracked except each batch's `ACCEPTED.md`;
  - `make lint` checking OKF frontmatter on every document.
- The workspace renders `results/` with a tracked `.gitkeep`, so the folder
  the contract names exists from the start.
- The `paper` template, with Overleaf as its main source:
  - `main.tex` at the root, built with pdflatex through `latexmkrc` (no
    leading dot), so Overleaf and `make pdf` build the same thing;
  - ICLR, NeurIPS or a plain article layout, anonymous until
    `\camerareadytrue`;
  - `make venue` fetches the venue's kit (none is shipped);
  - `make check` fails on undefined references or citations, overfull lines
    and ChkTeX warnings;
  - `make arxiv` writes a cleaned copy;
  - CI only with a GitHub mirror, building in TeX Live 2025 pinned by digest;
  - no symlinks, and `AGENTS.md` untracked.
- A shared OKF frontmatter checker (`_shared/docs/check_frontmatter.py`). It
  also checks that each document's `resource` names its own path. foundry
  runs it on its own `docs/`.
- Shared files read optional answers with `cookiecutter.get`, so a template
  that does not ask a question can still include them.
- A nightly workflow that generates every project variant and runs its own
  `make ci` (`make test-heavy`).
- The public documentation standard (`standards/public-documentation.md`,
  rules PD1 to PD17), set at PyTorch's level with a source and a check for
  each rule, and the `public-docs` skill that applies it
  (`skills/public-docs/`).
- With `public_docs`, the `methodology` template adds the documentation the
  standard asks for:
  - Sphinx 9.1 with MyST and the PyData theme, built with warnings as errors
    and every cross-reference checked (`make docs`);
  - an API reference generated from the package, and `make docs-coverage`,
    which fails on any undocumented module or object;
  - how-to guides whose code lives in `docs_src/`, run by a test that checks
    what each guide says it prints;
  - `make docs-linkcheck`, and a Read the Docs configuration;
  - `CONTRIBUTING.md`, a Contributor Covenant 3.0 `CODE_OF_CONDUCT.md`,
    `SECURITY.md` and `CITATION.cff`, with a test that they are present and
    that the citation's version matches the package.
- `public_docs` can be turned on in an existing project with
  `cruft update --variables-to-update`, passing `public_docs` and
  `contact_email`. Generation refuses `public_docs` without a licence, or
  without a contact address: `contact_email` has no default, so someone
  types it.
- `make arxiv-verify` in the `paper` template compiles `build/arxiv` on its
  own with plain pdflatex in the pinned image, as arXiv does.

- The `software` template with its first component, `backend_django`
  (see [ADR 0002](docs/adr/0002-software-template-layout.md)):
  - Django 6.1 and DRF 3.18 in `backend/`, one app per domain in the layout
    recorded by ADR 0002, with a worked example app (`notes`);
  - rules in `Meta.constraints`, enforced by Postgres, checked early by
    services, and compared with the catalogue by a drift test;
  - a custom user model from the first migration, and pgvector enabled;
  - closed by default: `IsAuthenticated`, pagination on, an exception
    handler that turns database refusals into 409 and 400;
  - settings per environment, with production refusing to start without
    its secrets or with debug set;
  - Postgres 18 with pgvector in compose, and a uv-built production image
    run by a non-root user, every image pinned by digest;
  - `make ci` adds the migration check, the validated OpenAPI schema,
    Django's deployment checklist, and a smoke test that serves the image
    against Postgres.
- Shared toolchain configs take the Django options (paths, mypy and pylint
  plugins, pytest-django) from the `backend_django` answer; other
  templates render unchanged.
- The `software` template's second component, `frontend_nextjs` (see
  [ADR 0003](docs/adr/0003-frontend-component-and-pins.md)), which needs
  `backend_django`:
  - Next.js 16 with React 19 and strict TypeScript in `frontend/`, laid out
    as routes, features and shared layers, with ESLint refusing imports
    that cross them the wrong way;
  - pages rendered on the server, reading the backend over the compose
    network;
  - Vitest unit and component tests, and Playwright end-to-end tests with
    axe against a production build and the real backend;
  - one coverage report merged from all three, failing below 90%, in which
    a file no test reaches counts at zero;
  - pnpm and Node pinned in `package.json`, every dependency at an exact
    version, and a standalone production image run by a non-root user;
  - `make ci` adds lint and type checks through pre-commit, the merged
    coverage, and `make smoke-stack`, which runs both production images
    together.
- ADR 0003 records each frontend tool held below its latest release, and
  the condition that lifts the hold.
- After a conformance audit of the software template (ADR 0004):
  - the frontend gains the web structure's shared layers: a route group,
    `loading.tsx`, `components/layout/AppShell` with a skip link,
    `components/ui/state/` (`Pending`, `ErrorNotice`), `config/navigation.ts`
    and `lib/server/env.ts`, with a README in each layer the example does
    not use yet;
  - frontend tests gain `integration/`, `a11y/` (axe on every listed
    route), `smoke/` and `fixtures/`, and `make smoke-stack` checks that
    the frontend shuts down on SIGTERM rather than being killed;
  - the backend gains a pgvector example (`Note.embedding` with an HNSW
    cosine index and `similar_notes`) and `django.contrib.postgres`;
  - `.env.example` lists every setting the code reads, and a test refuses
    one missing or stale;
  - every template has `make template-check` (`cruft check`);
  - foundry's Dependabot watches the software template's npm and
    Dockerfile pins;
  - `tests/functional/test_software_conformance.py` checks every requirement
    recorded in Foundry's software ADRs on a render, and makes each
    requirement not yet met name its ADR.
- `make test-heavy-code` and `make test-heavy-paper` print the free disk
  space after the tests as well as before.
- The `software` template's `proxy_caddy` component (on by default) and
  `gateway_litellm` component (off by default), both needing the backend
  (ADR 0005):
  - Caddy 2.11.4, pinned by digest, as the only published service. It is
    unprivileged, read-only, has every capability dropped except binding
    ports, and has memory, CPU and process limits. It serves on
    `127.0.0.1:8443` on a laptop, and on 80 and 443 with
    `compose.deploy.yaml`.
  - The Caddyfile sets TLS 1.2 and 1.3; HSTS, Permissions-Policy, COOP and
    CORP once for the whole site; and JSON access logs. It removes
    `Forwarded`, `x-middleware-subrequest`, `Server` and `Via`, refuses
    unknown hosts, sets a 10 MB body limit and flushes streamed responses.
  - `make proxy-check` runs `caddy fmt` and `caddy validate`.
    `make smoke-proxy` checks the running stack from inside its network.
  - LiteLLM 1.103.2 (`litellm-non_root`, pinned by digest, past
    GHSA-7hp6-4w63-5g45) on its own network and compose profile. It
    refuses a master key without the `sk-` prefix and runs with the
    production settings recorded in ADR 0005, an empty model list and a
    visibility policy (`gateway/policy.py`).
  - `make smoke-gateway` checks the key, the health check, docs off and the
    policy against two mock models.
- Heavy variants `software-everything` and `software-django-alone`, and a
  third nightly runner, so the software images have a disk of their own.
- The `methodology` template's `dataset_registry` answer (default `no`). With
  `yes` it ships the same empty `datasets/registry.yaml` as the workspace
  template, now one shared file in `_shared/base/`. A lab project's methodology
  repository is its root, so its run launchers, literature tools and data
  adapters read the registry there; a paper project's workspace already holds
  one.
- `make throwaway VARIANT=<name>`, a project generated offline by `cruft
create` from this repository, for setup tests; and `make template-matrix`,
  every combination of the answers that change a template's files, each
  generated, installed, put through its own `make ci` and a `cruft update`,
  then deleted, with a report in `build/template-matrix/`. The named variants
  moved to `tools/variants.py`, which the heavy tests read too.
- The `software` template's `ml_pytorch` answer (default `no`; needs the
  backend), for a web app with a PyTorch model inside it
  ([ADR 0006](docs/adr/0006-ml-pytorch-in-software.md)):
  - `backend/ml/` with the methodology template's own `seeding.py`,
    `device.py`, `threads.py` and `runrecord.py` and their tests, shared from
    `_shared/ml/`, plus a small model and a predictor;
  - `POST /api/inference/score/`, which answers 503 until `ML_WEIGHTS` names a
    `state_dict` file;
  - CPU wheels on Linux from PyTorch's index, locked for linux x86_64 and
    aarch64 and macOS arm64;
  - the thread variables held to `ML_THREADS` in compose;
  - heavy variant `software-ml`, and its conformance rows.
- `tools.throwaway --working-tree`, which generates from uncommitted changes.
- Skills `publish`, `template-update`, `ci-local`, `paper-build` and `release`,
  and `make install-skills`, which installs `skills/` into
  `~/.claude/skills`, updates a copy nobody edited, and refuses to overwrite
  one edited in place (`--adopt`, `--force`) or a same-named skill it did not
  install.
- The `methodology` template's `run_records` answer (default `no`;
  needs `ml_pytorch`;
  [ADR 0008](docs/adr/0008-run-sidecars.md)): `sidecars.py` writes the witness
  (`observed.attempt<N>.json`) and `metrics.json` in Foundry's versioned run
  record format, held by tests to the documented field contract. The project
  writes files and calls no service.
- `make publish-check` and `make publish REMOTE=<remote>` in the `methodology`
  and `software` templates
  ([ADR 0007](docs/adr/0007-public-export.md)): the public export is `HEAD`
  without the agent files, refused if a line holds an Overleaf project ID, a
  home path or a pattern in the project's `.publish-deny`, and pushed as one
  release commit whose only parent is the last release.
- `make template-matrix WHERE=name=value OUT=<dir>`, to run part of the matrix
  and keep its report apart.

### Security

- Security fixes are published as patch releases; the weekly locked-dependency
  audit reports known vulnerabilities.

### Fixed

- Every template ignores `graphify-out/` and `.venue-check` from the shared
  base, as ADR 0009 records; `graphify-out/` was in the workspace's own list
  only, so a methodology or software repository could commit a knowledge
  graph. A test now pins all five local-output entries.
- `tools.throwaway` refuses an answer the template does not ask at the ref it
  generates from. cruft reads commits, not the working tree, and cookiecutter
  dropped such an answer without a word.
- The template matrix commits a paper's venue kit after `make venue`, as the
  paper asks, instead of failing the variant for leaving it uncommitted.
- In a software project with a model, mypy's `untyped_calls_exclude = torch`
  was rendered into the django-stubs section, where mypy does not read it.
- The nightly code run frees the runner's unused preinstalled toolchains
  first, and each generated project is deleted once its test passes: the
  PyTorch environments and the software images filled the disk.

- `.editorconfig` gives `.mjs` and `.cjs` files two-space indents, as
  Prettier writes them.

- The arXiv copy of an ICLR or NeurIPS paper now carries the venue kit beside
  `main.tex`. arXiv never reads `latexmkrc`, so the kit in `venue/` was
  invisible to it.
- The paper template's `AGENTS.md` and `CLAUDE.md` are committed. Its own
  `.gitignore` names them, and git applied that file inside foundry too.
- The paper's TeX Live container runs as the calling user, so `build/` stays
  writable on a Linux host.
