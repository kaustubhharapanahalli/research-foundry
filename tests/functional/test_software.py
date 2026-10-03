"""The software template renders the components it promises."""

import json
import re
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest
from cookiecutter.exceptions import FailedHookException
from tests.conftest import LEFTOVER, PROJECT_DIR, ROOT

Render = Callable[..., Path]
BACKEND_FILES = [
    "backend/manage.py",
    "backend/config/settings/base.py",
    "backend/config/settings/dev.py",
    "backend/config/settings/prod.py",
    "backend/config/settings/test.py",
    "backend/config/urls.py",
    "backend/config/wsgi.py",
    "backend/config/asgi.py",
    "backend/apps/accounts/models.py",
    "backend/apps/core/exceptions.py",
    "backend/apps/core/migrations/0001_vector_extension.py",
    "backend/apps/notes/migrations/0001_initial.py",
    "backend/conftest.py",
    "make/django.mk",
    "compose.yaml",
    "Dockerfile",
    ".dockerignore",
    ".env.example",
    "scripts/smoke.sh",
]
FRONTEND_FILES = [
    "frontend/package.json",
    "frontend/pnpm-workspace.yaml",
    "frontend/next.config.ts",
    "frontend/tsconfig.json",
    "frontend/eslint.config.mjs",
    "frontend/vitest.config.ts",
    "frontend/playwright.config.ts",
    "frontend/Dockerfile",
    "frontend/app/layout.tsx",
    "frontend/app/(main)/page.tsx",
    "frontend/lib/server/backend.ts",
    "frontend/scripts/coverage.mjs",
    "frontend/tests/e2e/home.spec.ts",
    "make/nextjs.mk",
]
PROXY_FILES = [
    "proxy/Caddyfile",
    "make/caddy.mk",
    "compose.deploy.yaml",
    "scripts/check_proxy.py",
]
GATEWAY_FILES = [
    "gateway/config.yaml",
    "gateway/policy.py",
    "gateway/tests/smoke.yaml",
    "make/litellm.mk",
    "scripts/check_gateway.py",
]
ML_MODULES = ["seeding", "device", "threads", "runrecord"]
ML_FILES = [
    *(f"backend/ml/{name}.py" for name in ML_MODULES),
    "backend/ml/__init__.py",
    "backend/ml/model.py",
    "backend/ml/predictor.py",
    "backend/ml/tests/unit/test_predictor.py",
    "backend/ml/tests/functional/test_determinism.py",
    "backend/apps/inference/views.py",
    "backend/apps/inference/services.py",
    "backend/apps/inference/tests/functional/test_api.py",
]
# The shape every app under backend/apps/ follows (ADR 0002).
APP_LAYOUT = [
    "models.py",
    "serializers.py",
    "views.py",
    "urls.py",
    "services.py",
    "selectors.py",
    "permissions.py",
    "admin.py",
    "migrations/__init__.py",
    "tests/unit",
    "tests/functional",
]


def test_backend_files_are_rendered(render: Render) -> None:
    project = render("software")
    for name in BACKEND_FILES:
        assert (project / name).is_file(), name


def test_the_example_app_shows_the_whole_layout(render: Render) -> None:
    app = render("software") / "backend" / "apps" / "notes"
    for name in APP_LAYOUT:
        assert (app / name).exists(), name


@pytest.mark.parametrize(
    ("answers", "reason"),
    [
        (
            {
                "backend_django": "no",
                "frontend_nextjs": "no",
                "proxy_caddy": "no",
            },
            "Choose at least one component",
        ),
        (
            {"backend_django": "no", "frontend_nextjs": "yes"},
            "frontend_nextjs needs backend_django",
        ),
        (
            {
                "backend_django": "no",
                "frontend_nextjs": "no",
                "proxy_caddy": "yes",
            },
            "proxy_caddy needs backend_django",
        ),
        (
            {
                "backend_django": "no",
                "frontend_nextjs": "no",
                "proxy_caddy": "no",
                "gateway_litellm": "yes",
            },
            "gateway_litellm needs backend_django",
        ),
        (
            {
                "backend_django": "no",
                "frontend_nextjs": "no",
                "proxy_caddy": "no",
                "ml_pytorch": "yes",
            },
            "ml_pytorch needs backend_django",
        ),
    ],
    ids=[
        "no-component",
        "frontend-without-backend",
        "proxy-without-backend",
        "gateway-without-backend",
        "ml-without-backend",
    ],
)
def test_a_component_set_that_cannot_work_is_refused(
    answers: dict[str, str],
    reason: str,
    render: Render,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(FailedHookException):
        render("software", **answers)
    assert reason in capfd.readouterr().err
    assert not (tmp_path / "my-project").exists()


def test_frontend_files_are_rendered(render: Render) -> None:
    project = render("software")
    for name in FRONTEND_FILES:
        assert (project / name).is_file(), name
    assert "include make/nextjs.mk" in (project / "Makefile").read_text()
    assert "\n  frontend:\n" in (project / "compose.yaml").read_text()


def test_the_frontend_can_be_left_out(render: Render) -> None:
    project = render("software", frontend_nextjs="no")
    assert not (project / "frontend").exists()
    assert not (project / "make" / "nextjs.mk").exists()
    assert "nextjs.mk" not in (project / "Makefile").read_text()
    assert "frontend" not in (project / "compose.yaml").read_text()
    config = project / ".pre-commit-config.yaml"
    assert "pnpm" not in config.read_text()
    dependabot = project / ".github" / "dependabot.yml"
    assert "/frontend" not in dependabot.read_text()
    for path in project.rglob("*"):
        if path.is_file():
            assert not LEFTOVER.search(path.read_text()), path


def test_frontend_files_are_copied_without_rendering() -> None:
    # JSX's {{ ... }} would break the render, so these are copied as they
    # are; one carrying a cookiecutter variable would arrive unrendered.
    source = ROOT / "software" / PROJECT_DIR
    answers = json.loads((ROOT / "software" / "cookiecutter.json").read_text())
    for pattern in answers["_copy_without_render"]:
        for path in source.glob(pattern):
            files = [path] if path.is_file() else path.rglob("*")
            for name in files:
                if name.is_file():
                    assert "cookiecutter." not in name.read_text(), name


def test_the_frontend_tools_run_from_pre_commit(render: Render) -> None:
    config = (render("software") / ".pre-commit-config.yaml").read_text()
    assert "pnpm --dir frontend run lint" in config
    assert "pnpm --dir frontend run typecheck" in config
    assert "frontend/pnpm-lock" in config


def test_node_and_pnpm_are_pinned(render: Render) -> None:
    package = render("software") / "frontend" / "package.json"
    data = json.loads(package.read_text())
    assert re.fullmatch(r"pnpm@\d+\.\d+\.\d+", data["packageManager"])
    runtime = data["devEngines"]["runtime"]
    assert runtime["name"] == "node"
    assert re.fullmatch(r"\d+\.\d+\.\d+", runtime["version"])
    for group in ("dependencies", "devDependencies"):
        for name, version in data[group].items():
            assert re.fullmatch(r"\d+\.\d+\.\d+", version), name


def test_the_database_port_is_one_answer(render: Render) -> None:
    project = render("software", db_port="5499")
    assert "5499" in (project / "compose.yaml").read_text()
    base = project / "backend" / "config" / "settings" / "base.py"
    assert '"5499"' in base.read_text()


def test_dependencies_are_declared_for_the_backend(render: Render) -> None:
    with (render("software") / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    names = {dep.split(">=")[0] for dep in data["project"]["dependencies"]}
    assert {"django", "djangorestframework", "psycopg[binary,pool]"} <= names
    assert data["tool"]["uv"]["package"] is False


def test_every_image_is_pinned_by_digest(render: Render) -> None:
    project = render("software", gateway_litellm="yes")
    dockerfiles = [project / "Dockerfile", project / "frontend" / "Dockerfile"]
    for dockerfile in dockerfiles:
        stages: set[str] = set()
        for line in dockerfile.read_text().splitlines():
            if not line.startswith("FROM "):
                continue
            words = line.split()
            # FROM <earlier stage> is not an image to pin.
            if words[1] not in stages:
                assert "@sha256:" in words[1], line
            if len(words) == 4 and words[2] == "AS":
                stages.add(words[3])
    images = [
        line.split("image:", 1)[1].strip()
        for line in (project / "compose.yaml").read_text().splitlines()
        if line.strip().startswith("image: ")
    ]
    built = {"my-project-backend:dev", "my-project-frontend:dev"}
    pulled = [image for image in images if image not in built]
    assert len(pulled) == 3, pulled  # Postgres, Caddy and LiteLLM
    for image in pulled:
        assert re.fullmatch(r"\S+:\S+@sha256:[0-9a-f]{64}", image), image


def test_the_proxy_check_uses_the_image_compose_runs(render: Render) -> None:
    project = render("software")
    caddy_mk = (project / "make" / "caddy.mk").read_text()
    pinned = re.search(r"^CADDY_IMAGE := (\S+)$", caddy_mk, re.MULTILINE)
    assert pinned
    assert (
        f"image: {pinned.group(1)}" in (project / "compose.yaml").read_text()
    )


def test_proxy_files_are_rendered(render: Render) -> None:
    project = render("software")
    for name in PROXY_FILES:
        assert (project / name).is_file(), name
    assert "include make/caddy.mk" in (project / "Makefile").read_text()
    compose = (project / "compose.yaml").read_text()
    assert "\n  proxy:\n" in compose
    assert 'DJANGO_TRUST_FORWARDED_PROTO: "1"' in compose


def test_the_proxy_routes_only_to_components_that_exist(
    render: Render,
) -> None:
    caddyfile = (
        render("software", frontend_nextjs="no") / "proxy" / "Caddyfile"
    )
    text = caddyfile.read_text()
    assert "reverse_proxy backend:8000" in text
    assert "frontend" not in text


def test_the_proxy_and_frontend_agree_on_permissions_policy(
    render: Render,
) -> None:
    # The proxy replaces the frontend's copy; the two must not drift, or
    # the page behaves differently with the proxy and without it.
    project = render("software")
    caddyfile = (project / "proxy" / "Caddyfile").read_text()
    proxy_value = re.search(r'Permissions-Policy "([^"]+)"', caddyfile)
    security = (project / "frontend" / "config" / "security.ts").read_text()
    frontend_value = re.search(
        r'key: "Permissions-Policy",\s*value: "([^"]+)"', security
    )
    assert proxy_value and frontend_value
    assert proxy_value.group(1) == frontend_value.group(1)


def test_the_proxy_can_be_left_out(render: Render) -> None:
    project = render("software", proxy_caddy="no")
    for name in PROXY_FILES:
        assert not (project / name).exists(), name
    assert "caddy.mk" not in (project / "Makefile").read_text()
    compose = (project / "compose.yaml").read_text()
    assert "proxy" not in compose
    assert "DJANGO_TRUST_FORWARDED_PROTO" not in compose


def test_gateway_files_are_rendered(render: Render) -> None:
    project = render("software", gateway_litellm="yes")
    for name in GATEWAY_FILES:
        assert (project / name).is_file(), name
    assert "include make/litellm.mk" in (project / "Makefile").read_text()
    compose = (project / "compose.yaml").read_text()
    assert "\n  gateway:\n" in compose
    # The backend reaches it; the database never shares its network.
    assert "networks: [default, gateway-edge]" in compose
    assert compose.count("gateway-edge") == 3


def test_the_gateway_is_off_by_default(render: Render) -> None:
    project = render("software")
    for name in GATEWAY_FILES:
        assert not (project / name).exists(), name
    assert "gateway" not in (project / "compose.yaml").read_text()
    assert "LITELLM" not in (project / ".env.example").read_text()


def test_tools_are_configured_for_django(render: Render) -> None:
    project = render("software")
    config = project / ".dev-config"
    assert "mypy_django_plugin.main" in (config / "mypy.ini").read_text()
    assert "pylint_django" in (config / "pylintrc").read_text()
    pytest_ini = (config / "pytest.ini").read_text()
    assert "DJANGO_SETTINGS_MODULE = config.settings.test" in pytest_ini
    assert "pythonpath = ../backend" in pytest_ini


def test_no_licence_means_no_licence_file(render: Render) -> None:
    project = render("software", license="none")
    assert not (project / "LICENSE").exists()


def test_claude_md_imports_agents_md(render: Render) -> None:
    assert (render("software") / "CLAUDE.md").read_text() == "@AGENTS.md\n"


def test_the_image_runs_the_pinned_node_and_pnpm(render: Render) -> None:
    # Dependabot raises the image tag; package.json must move with it.
    frontend = render("software") / "frontend"
    data = json.loads((frontend / "package.json").read_text())
    dockerfile = (frontend / "Dockerfile").read_text()
    node = data["devEngines"]["runtime"]["version"]
    tags = re.findall(r"^FROM node:([\d.]+)-", dockerfile, re.MULTILINE)
    assert tags and set(tags) == {node}, (tags, node)
    pnpm = data["packageManager"].removeprefix("pnpm@")
    assert f"pnpm@{pnpm}" in dockerfile


def test_ml_files_are_rendered(render: Render) -> None:
    project = render("software", ml_pytorch="yes")
    for name in ML_FILES:
        assert (project / name).is_file(), name
    base = (project / "backend/config/settings/base.py").read_text()
    assert '"apps.inference"' in base and "ML_WEIGHTS" in base
    assert (
        "apps.inference.urls"
        in (project / "backend/config/urls.py").read_text()
    )


def test_ml_is_off_by_default(render: Render) -> None:
    project = render("software")
    assert not (project / "backend" / "ml").exists()
    assert not (project / "backend" / "apps" / "inference").exists()
    for name in (
        "backend/config/settings/base.py",
        "backend/config/urls.py",
        "pyproject.toml",
        "compose.yaml",
        ".env.example",
    ):
        text = (project / name).read_text()
        assert "inference" not in text and "torch" not in text, name
        assert "ML_" not in text, name


@pytest.mark.parametrize("module", ML_MODULES)
def test_ml_modules_are_the_methodology_templates_own(
    module: str, render: Render
) -> None:
    # One copy in _shared/ml/: a fix to seeding reaches both templates.
    software = render("software", ml_pytorch="yes") / "backend" / "ml"
    methodology = render(
        "methodology", ml_pytorch="yes", project_name="Other Project"
    )
    package = methodology / "src" / "other_project"
    assert (software / f"{module}.py").read_text() == (
        package / f"{module}.py"
    ).read_text()


def test_the_web_image_takes_cpu_torch_on_linux(render: Render) -> None:
    data = tomllib.loads(
        (render("software", ml_pytorch="yes") / "pyproject.toml").read_text()
    )
    index = data["tool"]["uv"]["index"][0]
    assert index["url"] == "https://download.pytorch.org/whl/cpu"
    assert index["explicit"] is True
    source = data["tool"]["uv"]["sources"]["torch"][0]
    assert source == {
        "index": "pytorch-cpu",
        "marker": "sys_platform == 'linux'",
    }
    # Docker on Apple silicon builds the image for linux on arm64.
    assert any(
        "aarch64" in env for env in data["tool"]["uv"]["required-environments"]
    )


def test_the_model_threads_are_held_in_the_container(render: Render) -> None:
    compose = (
        render("software", ml_pytorch="yes") / "compose.yaml"
    ).read_text()
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        assert f"{name}: ${{ML_THREADS:-1}}" in compose, name
