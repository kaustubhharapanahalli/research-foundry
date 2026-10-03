---
type: Standard
title: Security Standard
description: The numbered rules for supply-chain, secret, hook, vulnerability, dependency, release and public-export security in research-foundry and its generated projects.
resource: /standards/security.md
tags: [standard, security, supply-chain, secrets, publishing]
timestamp: 2026-10-02T00:00:00Z
status: accepted
version: 1.0.0
---

# Security standard

Version 1.0.0. This standard covers research-foundry, the projects it
generates, their automation, and the boundary between private research work
and a public release.

**Sources.** The repository workflows, policies, hooks, publish code and
Architecture Decision Records (ADRs) cited below were opened on 2026-10-02.
A source that was not available locally is marked and must be
opened before this proposal is accepted.

## Rules

### SS1. Every third-party action is pinned by commit SHA

- **Rule:** Pin each GitHub Action `uses:` reference to its full commit Secure
  Hash Algorithm (SHA), with the release tag in a comment. Do not pin an action
  by a mutable tag or branch.
- **Why:** a full commit SHA is the immutable action identity; the comment
  keeps the human-readable version visible for updates.
- **Example:** `actions/checkout@3d3c42... # v7.0.1`.
- **Source:** [GitHub, "Using third-party actions"](https://docs.github.com/en/actions/reference/security/secure-use#using-third-party-actions).
- **Enforced by:** unit workflow tests inspect root and generated workflows;
  Dependabot updates the SHA and version comment each week.

### SS2. Workflow permissions are least privilege

- **Rule:** Set explicit least-privilege `permissions:` at workflow or job
  scope. Read-only checks use `contents: read`; a job that needs more grants
  only that permission at job scope. Checkout does not persist credentials,
  jobs have timeouts, and untrusted pull-request code never runs through
  `pull_request_target`.
- **Why:** a compromised step can use only the token capabilities and time the
  job actually needs.
- **Source:** [GitHub, "Use GITHUB_TOKEN for authentication in workflows"](https://docs.github.com/en/actions/reference/security/secure-use#use-github_token-for-authentication-in-workflows).
- **Enforced by:** unit workflow tests and review of
  `.github/workflows/*.yml` and generated `.github/workflows/ci.yml`.

### SS3. Repositories contain examples, never secrets

- **Rule:** Commit no credential, token, private key or populated environment
  file. Ignore `.env` and every `.env.*` file except `.env.example`; examples
  contain names and safe development placeholders only.
- **Why:** Git history and generated repositories are durable and easy to
  copy; deleting a leaked secret later does not revoke it.
- **Example:** production supplies `DJANGO_SECRET_KEY`; `.env.example` states
  the name but contains no production value.
- **Source:** [GitHub, "Avoid hardcoding secrets in your code"](https://docs.github.com/en/actions/reference/security/secure-use#avoid-hardcoding-secrets-in-your-code).
- **Enforced by:** `make lint` runs the pre-commit `detect-private-key` hook;
  `_shared/base/gitignore` excludes environment files; generated software
  tests keep code-read variables and `.env.example` in sync.

### SS4. Template hooks are local and offline

- **Rule:** A pre-generation or post-generation hook performs no network
  access and reads or writes only inside the template input or generated
  project. A hook refuses invalid answers before creating a project; it does
  not inspect or modify unrelated user files.
- **Why:** Cookiecutter runs accepted hooks as code, so an unbounded hook would
  inherit the user's filesystem and network authority.
- **Example:** a post-generation hook may delete an unselected component from
  the generated tree; it may not download a tool or edit a global config.
- **Source:** [Cookiecutter, "Pre/Post-Generate Hooks"](https://cookiecutter.readthedocs.io/en/stable/advanced/hooks.html).
- **Enforced by:** Not yet enforced; functional hook tests check current
  refusal and deletion behaviour, but hooks need a sandboxed test that blocks
  sockets and fails filesystem access outside the generated temporary project.

### SS5. Vulnerabilities are reported privately

- **Rule:** `SECURITY.md` names the supported versions and directs reporters to
  GitHub private vulnerability reporting, never a public issue. Generated
  public projects also provide a private advisory URL or the maintainer's
  security contact and state the expected response time.
- **Why:** private reporting gives maintainers time to assess, fix and release
  before exploit details become public.
- **Source:** [GitHub, "Privately reporting a security vulnerability"](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).
- **Enforced by:** root and generated `SECURITY.md` files plus structural tests
  that require community policy files in rendered projects.

### SS6. Dependencies are updated and audited weekly

- **Rule:** Dependabot checks GitHub Actions, uv, pre-commit, npm and container
  dependencies that apply to the repository each week. A weekly dependency
  audit also fails on known applicable vulnerabilities; an ignored advisory
  names its reason and expiry.
- **Why:** update proposals keep pins current, while an audit detects a known
  vulnerability even when no compatible upgrade proposal is available.
- **Source:** [GitHub, "Dependabot version updates configuration options"](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file) and [PyPA, "pip-audit"](https://github.com/pypa/pip-audit).
- **Enforced by:** Not yet enforced; `.github/dependabot.yml` and generated
  Dependabot configuration schedule weekly updates, but add a weekly workflow
  that audits locked Python, npm and container dependencies and records bounded
  advisory exceptions.

### SS7. Python releases use trusted publishing and attestations

- **Rule:** Publish Python distributions to the Python Package Index (PyPI)
  from a protected GitHub Actions environment through OpenID Connect trusted
  publishing. Build from the accepted tag, publish the exact artifacts tested,
  and emit build provenance attestations. Store no long-lived PyPI token.
- **Why:** short-lived identity removes a reusable release secret, and an
  attestation ties the artifact to its source workflow and commit.
- **Source:** [PyPI, "Publishing with a Trusted Publisher"](https://docs.pypi.org/trusted-publishers/using-a-publisher/) and [GitHub, "Using artifact attestations to establish provenance"](https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds).
- **Enforced by:** Not yet enforced; add a protected release workflow with
  `id-token: write`, PyPI trusted publishing and build attestations after the
  owner accepts the release design.

### SS8. Public export refuses private material

- **Rule:** Public methodology and software releases contain no agent files,
  private history, Overleaf identifier, home path or project-specific deny-list
  match. Build and scan the export without pushing before every release; a
  refusal names the file, line and rule without repeating the private text.
- **Why:** the public repository must stand alone without exposing private
  research context or relying on deletion from Git history after release.
- **Example:** `make publish-check` creates the `HEAD` export and pushes
  nothing; `make publish` creates one release commit only after the check.
- **Source:** [Architecture Decision Record 0007, "Decision"](../docs/adr/0007-public-export.md#decision).
- **Enforced by:** generated `make publish-check`, `_shared/publish/publish.py`
  and the public-export unit and functional tests.

### SS9. Lock files are committed and installs are locked

- **Rule:** Commit every supported ecosystem's lock file. The initial generated
  project install may create its lock file, which the template matrix commits;
  every subsequent local, CI and container install uses the locked resolution
  and fails if declarations and locks disagree.
- **Why:** a lock records the reviewed dependency graph so the same commit does
  not resolve to different code on different days.
- **Example:** root installs run `uv sync --locked`; generated Python installs
  add `--locked` as soon as `uv.lock` exists; containers use
  `uv sync --locked`.
- **Source:** [uv, "Locking and syncing"](https://docs.astral.sh/uv/concepts/projects/sync/) and [uv, "Using uv in Docker"](https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment).
- **Enforced by:** `make install`, `make lint` (`uv lock --check`), generated
  Python Makefiles, container builds, and the template-matrix test that commits
  a newly created lock before running the remaining checks.
