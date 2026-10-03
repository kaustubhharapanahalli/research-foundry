"""The software template against Foundry Architecture Decision Records.

Each row is one requirement, with the Foundry decision it comes from,
checked on a fresh render with every built component on. A requirement the
template does not meet is listed in DEFERRED with the reason and the
ADR that carries it, so nothing is left out silently.
"""

import re
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter
from tests.conftest import ROOT

# (path that must exist, where the requirement comes from)
PATHS = [
    # Backend: ADR 0002.
    ("backend/config/settings/base.py", "ADR 0002"),
    ("backend/config/settings/dev.py", "ADR 0002"),
    ("backend/config/settings/prod.py", "ADR 0002"),
    ("backend/config/settings/test.py", "ADR 0002"),
    ("backend/config/urls.py", "ADR 0002"),
    ("backend/config/wsgi.py", "ADR 0002"),
    ("backend/config/asgi.py", "ADR 0002"),
    ("backend/apps/notes/models.py", "ADR 0002"),
    ("backend/apps/notes/serializers.py", "ADR 0002"),
    ("backend/apps/notes/views.py", "ADR 0002"),
    ("backend/apps/notes/urls.py", "ADR 0002"),
    ("backend/apps/notes/services.py", "ADR 0002"),
    ("backend/apps/notes/selectors.py", "ADR 0002"),
    ("backend/apps/notes/permissions.py", "ADR 0002"),
    ("backend/apps/notes/admin.py", "ADR 0002"),
    ("backend/apps/notes/migrations", "ADR 0002"),
    ("backend/apps/notes/tests", "ADR 0002"),
    ("backend/apps/core/tests/functional/test_constraint_drift.py",
     "ADR 0002, Tests: the drift test"),
    # Frontend: ADR 0004.
    ("frontend/app/layout.tsx", "ADR 0004"),
    ("frontend/app/(main)/page.tsx", "ADR 0004: route groups"),
    ("frontend/app/(main)/loading.tsx", "ADR 0004: loading where it waits"),
    ("frontend/app/error.tsx", "ADR 0004: error and not-found files"),
    ("frontend/app/global-error.tsx", "ADR 0004: error and not-found files"),
    ("frontend/app/not-found.tsx", "ADR 0004: error and not-found files"),
    ("frontend/features/status/components", "ADR 0004: inside a feature"),
    ("frontend/features/status/model", "ADR 0004: inside a feature"),
    ("frontend/components/ui", "ADR 0004"),
    ("frontend/components/shared", "ADR 0004"),
    ("frontend/components/layout/AppShell.tsx", "ADR 0004"),
    ("frontend/hooks", "ADR 0004"),
    ("frontend/lib/api", "ADR 0004"),
    ("frontend/lib/server/env.ts", "ADR 0004"),
    ("frontend/lib/domain", "ADR 0004"),
    ("frontend/lib/format", "ADR 0004"),
    # The model inside the web app: ADR 0006.
    ("backend/ml/seeding.py", "ADR 0006: seeding.py"),
    ("backend/ml/device.py", "ADR 0006: device.py"),
    ("backend/ml/runrecord.py", "ADR 0006: runrecord.py"),
    ("backend/ml/threads.py", "ADR 0006: threads"),
    ("backend/ml/tests/functional/test_determinism.py",
     "ADR 0006: the determinism test"),
    ("backend/apps/inference/views.py",
     "ADR 0006: a web app with a model inside it"),
    ("backend/apps/inference/tests/functional/test_api.py",
     "ADR 0006: a web app with a model inside it"),
    # The public export: ADR 0007.
    ("scripts/publish.py", "ADR 0007: make publish"),
    ("make/publish.mk", "ADR 0007: make publish"),
    (".publish-deny", "ADR 0007: the project's private items"),
    ("frontend/types", "ADR 0004"),
    ("frontend/styles/tokens.css", "ADR 0004: one token file"),
    ("frontend/styles/globals.css", "ADR 0004"),
    ("frontend/config/security.ts", "ADR 0004"),
    ("frontend/config/navigation.ts", "ADR 0004"),
    ("frontend/tests/setup.ts", "ADR 0004, Tests"),
    ("frontend/tests/unit/architecture", "ADR 0004, Tests"),
    ("frontend/tests/component", "ADR 0004, Tests"),
    ("frontend/tests/integration", "ADR 0004, Tests"),
    ("frontend/tests/e2e", "ADR 0004, Tests"),
    ("frontend/tests/a11y", "ADR 0004, Tests"),
    ("frontend/tests/smoke", "ADR 0004, Tests"),
    ("frontend/tests/fixtures", "ADR 0004, Tests"),
    ("proxy/Caddyfile", "ADR 0005: Caddy"),
    ("compose.deploy.yaml", "ADR 0005: published only on a server"),
    ("scripts/check_proxy.py", "ADR 0005: tests of each"),
    ("gateway/config.yaml", "ADR 0005"),
    ("gateway/policy.py", "ADR 0005: the visibility policy hook"),
    ("gateway/tests/smoke.yaml", "ADR 0005"),
    ("scripts/check_gateway.py", "ADR 0005"),
]  # fmt: skip

# (file, text it must contain, where the requirement comes from)
CONTENTS = [
    ("backend/config/settings/prod.py", "SECRET_KEY_FALLBACKS", "ADR 0002"),
    ("backend/config/settings/prod.py", "SECURE_HSTS_PRELOAD", "ADR 0002"),
    ("backend/config/settings/prod.py", "SECURE_PROXY_SSL_HEADER",
     "ADR 0002"),
    ("backend/config/settings/base.py", "DEFAULT_PERMISSION_CLASSES",
     "ADR 0002: deny by default"),
    ("backend/config/settings/base.py", "DEFAULT_PAGINATION_CLASS",
     "ADR 0002: pagination on"),
    ("backend/config/settings/base.py", "NUM_PROXIES", "ADR 0002"),
    ("backend/config/settings/prod.py", '"pool": True',
     "ADR 0002: connections"),
    ("backend/apps/core/migrations/0001_vector_extension.py",
     "VectorExtension", "ADR 0002: pgvector"),
    ("backend/apps/notes/models.py", "VectorField", "ADR 0002: pgvector"),
    ("backend/apps/notes/models.py", "HnswIndex", "ADR 0002: pgvector"),
    ("backend/apps/notes/models.py", "constraints", "ADR 0002: rules"),
    ("backend/apps/notes/services.py", "validate_constraints",
     "ADR 0002: rules"),
    ("backend/apps/core/exceptions.py", "IntegrityError",
     "ADR 0002: 409"),
    ("make/django.mk", "makemigrations --check", "ADR 0002: Tests"),
    ("make/django.mk", "check --deploy --fail-level WARNING",
     "ADR 0002: production settings"),
    ("make/django.mk", "spectacular --validate --fail-on-warn",
     "ADR 0002: DRF"),
    ("Dockerfile", "UV_COMPILE_BYTECODE=1", "ADR 0002: Serving"),
    ("Dockerfile", "UV_LINK_MODE=copy", "ADR 0002: Serving"),
    ("Dockerfile", "--no-install-project", "ADR 0002: Serving"),
    ("Dockerfile", "USER app", "ADR 0002: Serving"),
    ("frontend/next.config.ts", 'output: "standalone"',
     "ADR 0004: Deployment"),
    ("frontend/next.config.ts", "outputFileTracingRoot",
     "ADR 0004: Deployment"),
    ("frontend/next.config.ts", "typedRoutes: true", "ADR 0004"),
    ("frontend/tsconfig.json", '"strict": true', "ADR 0004"),
    ("frontend/tsconfig.json", "noUncheckedIndexedAccess", "ADR 0004"),
    ("frontend/tsconfig.json", "exactOptionalPropertyTypes", "ADR 0004"),
    ("frontend/tsconfig.json", "noImplicitOverride", "ADR 0004"),
    ("frontend/tsconfig.json", "noFallthroughCasesInSwitch", "ADR 0004"),
    ("frontend/eslint.config.mjs", "jsx-a11y", "ADR 0004"),
    ("frontend/eslint.config.mjs", "import/no-restricted-paths",
     "ADR 0004: import boundaries"),
    ("frontend/Dockerfile", "NEXT_TELEMETRY_DISABLED=1",
     "ADR 0004: Deployment"),
    ("frontend/Dockerfile", "USER node", "ADR 0004: Deployment"),
    ("frontend/lib/server/env.ts", 'import "server-only"',
     "ADR 0004: server-only code"),
    ("frontend/lib/server/backend.ts", 'import "server-only"',
     "ADR 0004: server-only code"),
    ("frontend/config/security.ts", "Content-Security-Policy",
     "ADR 0004: static CSP"),
    ("frontend/tests/a11y/routes.spec.ts", "@axe-core/playwright",
     "ADR 0004: Tests"),
    ("frontend/scripts/coverage.mjs", "all:",
     "ADR 0004: explicit coverage include"),
    ("make/nextjs.mk", "ExitCode\":143",
     "ADR 0004: graceful shutdown on SIGTERM"),
    (".github/dependabot.yml", "package-ecosystem: npm",
     "ADR 0004: Dependabot on npm"),
    ("Makefile", "template-check:", "ADR 0004: cruft check"),
    ("compose.yaml", "caddy:2.11.4-alpine@sha256:", "ADR 0005: pinned"),
    ("proxy/Caddyfile", "abort", "ADR 0005: host allowlist"),
    ("proxy/Caddyfile", "request_header -Forwarded",
     "ADR 0005: client forwarding headers replaced"),
    ("proxy/Caddyfile", "request_header -X-Middleware-Subrequest",
     "ADR 0004: CVE-2025-29927"),
    ("proxy/Caddyfile", "-Server", "ADR 0005: server_tokens off"),
    ("compose.yaml", '"127.0.0.1:${PROXY_PORT:-8443}:8443"',
     "ADR 0005: loopback only for development"),
    ("proxy/Caddyfile", "protocols tls1.2 tls1.3",
     "ADR 0005: Mozilla intermediate"),
    ("proxy/Caddyfile", "Strict-Transport-Security", "ADR 0005: HSTS"),
    ("proxy/Caddyfile", "max_size 10MB", "ADR 0005: explicit body limit"),
    ("proxy/Caddyfile", "format json", "ADR 0005: JSON access logs"),
    ("proxy/Caddyfile", "flush_interval -1",
     "ADR 0005: unbuffered streaming"),
    ("proxy/Caddyfile", "Permissions-Policy", "ADR 0005: one place"),
    ("proxy/Caddyfile", "Cross-Origin-Opener-Policy", "ADR 0005: one place"),
    ("proxy/Caddyfile", "Cross-Origin-Resource-Policy",
     "ADR 0005: one place"),
    ("compose.yaml", "read_only: true", "ADR 0005: compose hardening"),
    ("compose.yaml", "cap_drop: [ALL]", "ADR 0005: compose hardening"),
    ("compose.yaml", "no-new-privileges:true",
     "ADR 0005: compose hardening"),
    ("compose.yaml", "mem_limit:", "ADR 0005: resource limits"),
    ("compose.yaml", "pids_limit:", "ADR 0005: resource limits"),
    ("compose.yaml", "litellm-non_root:v1.103.2@sha256:",
     "ADR 0005: non-root, past GHSA-7hp6-4w63-5g45, pinned"),
    ("compose.yaml", "must start with sk-",
     "ADR 0005: refuse a missing or unprefixed key"),
    ("compose.yaml", "LITELLM_LOCAL_MODEL_COST_MAP", "ADR 0005"),
    ("compose.yaml", "networks: [gateway-edge]",
     "ADR 0005: its own network"),
    ("compose.yaml", "/health/liveliness", "ADR 0005: health check"),
    ("compose.yaml", "LITELLM_MODE: PRODUCTION", "ADR 0005"),
    ("compose.yaml", "LITELLM_LOG: ERROR", "ADR 0005"),
    ("compose.yaml", 'NO_DOCS: "True"', "ADR 0005"),
    ("compose.yaml", 'NO_REDOC: "True"', "ADR 0005"),
    ("compose.yaml", 'NO_OPENAPI: "True"', "ADR 0005"),
    ("compose.yaml", "--num_workers", "ADR 0005"),
    ("compose.yaml", "--max_requests_before_restart", "ADR 0005"),
    ("gateway/config.yaml", "drop_params: false", "ADR 0005"),
    ("gateway/config.yaml", "json_logs: true", "ADR 0005"),
    ("gateway/config.yaml", "request_timeout:", "ADR 0005"),
    ("gateway/config.yaml", "trusted_proxy_ranges: []", "ADR 0005"),
    ("gateway/config.yaml", "disable_env_credential_login: true",
     "ADR 0005"),
    ("gateway/config.yaml", "allow_client_side_credentials: false",
     "ADR 0005"),
    ("gateway/config.yaml", "model_list: []",
     "ADR 0005: an empty tier table"),
    ("gateway/policy.py", 'LOCAL_PREFIX = "local/"',
     "ADR 0005: unknown visibility goes to the local model only"),
    ("backend/ml/seeding.py",
     "use_deterministic_algorithms(True, warn_only=False)",
     "ADR 0006: warn_only=False"),
    ("backend/ml/seeding.py", "cudnn.benchmark = False", "ADR 0006"),
    ("backend/ml/seeding.py", '":4096:8"',
     "ADR 0006: CUBLAS_WORKSPACE_CONFIG"),
    ("backend/ml/device.py", "PYTORCH_ENABLE_MPS_FALLBACK",
     "ADR 0006: no silent fallback"),
    ("backend/ml/tests/functional/test_determinism.py", "torch.equal",
     "ADR 0006: same device, torch.equal"),
    ("backend/ml/predictor.py", "weights_only=True",
     "ADR 0006: checkpoints"),
    ("pyproject.toml", "required-environments",
     "ADR 0006: lock both platforms"),
    ("compose.yaml", "OMP_NUM_THREADS: ${ML_THREADS:-1}",
     "ADR 0006: threads held, ADR 0006"),
    ("scripts/publish.py", '"AGENTS.md",',
     "ADR 0007: no agent files in public"),
    ("scripts/publish.py", '"CLAUDE.md",',
     "ADR 0007: no agent files in public"),
    ("scripts/publish.py", '".agent-state",', "ADR 0007"),
    ("scripts/publish.py", '"Overleaf project ID"', "ADR 0007"),
    ("scripts/publish.py", '"home path"', "ADR 0007"),
    ("scripts/publish.py", '"commit-tree", tree, *parents',
     "ADR 0007: no private history"),
    ("Makefile", "include make/publish.mk", "ADR 0007"),
]  # fmt: skip

# (file, text it must NOT contain, where the requirement comes from)
ABSENT = [
    # No `images` key at all, so no remotePatterns.
    ("frontend/next.config.ts", "  images:", "ADR 0004: Images"),
    ("frontend/package.json", "NEXT_PUBLIC_",
     "ADR 0004: per-environment values on the server"),
    ("compose.yaml", "--telemetry", "ADR 0005: a no-op since 2024"),
]  # fmt: skip

# Requirements the template does not meet yet: the reason, and the ADR that
# carries each. A row moves to PATHS or CONTENTS when it is built.
DEFERRED = {
    "limit_req rate limits (ADR 0005)":
        "Caddy has none built in; the module is third-party, ADR 0005",
    "a test of the proxy's body limit (ADR 0005)":
        "Caddy enforces it as the upstream reads, ADR 0005",
    "LITELLM_SALT_KEY and a database for virtual keys (ADR 0005)":
        "the template offers no virtual keys, ADR 0005",
    "torch.compile for the served model (ADR 0006)":
        "the template serves eagerly; a project that compiles adds it, "
        "ADR 0006",
    "desktop-electron and mobile components (ADR 0004)":
        "names reserved only, ADR 0004",
    "migrate --check in make lint (ADR 0002, Tests)":
        "meaningful only against a deployed database, ADR 0004",
    "cruft check inside make lint (ADR 0004)":
        "needs network and credentials CI lacks; make template-check "
        "instead, ADR 0004",
    "Dependabot for compose.yaml, pyproject.toml and the TeX Live image "
    "inside templates (ADR 0004)":
        "Jinja makes them unparseable; raised by hand, ADR 0004",
    "browser matrix of Chromium, WebKit and Firefox (ADR 0004)":
        "browser coverage beyond Chromium is not promised; ADR 0004",
}  # fmt: skip


@pytest.fixture(name="project", scope="module")
def project_fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("conformance")
    return Path(
        cookiecutter(
            str(ROOT),
            directory="software",
            no_input=True,
            output_dir=str(out),
            extra_context={
                "backend_django": "yes",
                "frontend_nextjs": "yes",
                "proxy_caddy": "yes",
                "gateway_litellm": "yes",
                "ml_pytorch": "yes",
            },
        )
    )


@pytest.mark.parametrize(
    ("path", "source"), PATHS, ids=[path for path, _ in PATHS]
)
def test_required_path_exists(project: Path, path: str, source: str) -> None:
    assert (project / path).exists(), f"{path} is required by {source}"


@pytest.mark.parametrize(
    ("path", "text", "source"),
    CONTENTS,
    ids=[f"{path}:{text}" for path, text, _ in CONTENTS],
)
def test_required_content_is_present(
    project: Path, path: str, text: str, source: str
) -> None:
    assert text in (project / path).read_text(), f"{source}: {path}"


@pytest.mark.parametrize(
    ("path", "text", "source"),
    ABSENT,
    ids=[f"{path}:{text}" for path, text, _ in ABSENT],
)
def test_forbidden_content_is_absent(
    project: Path, path: str, text: str, source: str
) -> None:
    assert text not in (project / path).read_text(), f"{source}: {path}"


@pytest.mark.parametrize("requirement", sorted(DEFERRED))
def test_every_deferral_names_its_card_or_adr(requirement: str) -> None:
    assert re.search(r"#\d+|ADR \d{4}", DEFERRED[requirement]), requirement
