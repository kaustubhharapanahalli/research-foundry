"""Refuse a component set that cannot work, before any file is rendered.

Cookiecutter runs this without asking. It reads the answers only: no
files, no network.
"""

# Each template hook is a standalone entrypoint, so guards cannot be shared.
# pylint: disable=duplicate-code

import sys

# Rendered by cookiecutter before it runs; typed as str so a type checker
# reading the unrendered file does not see two unequal literals.
ANSWERS: dict[str, str] = {
    "backend_django": "{{ cookiecutter.backend_django }}",
    "frontend_nextjs": "{{ cookiecutter.frontend_nextjs }}",
    "proxy_caddy": "{{ cookiecutter.proxy_caddy }}",
    "gateway_litellm": "{{ cookiecutter.gateway_litellm }}",
    "ml_pytorch": "{{ cookiecutter.ml_pytorch }}",
}
PYTHON_VERSION = "{{ cookiecutter.python_version }}"
PYTHON_FLOOR = "{{ cookiecutter._python_floor }}"
# Components that only make sense beside the backend, and why.
NEEDS_BACKEND = {
    "frontend_nextjs": "the frontend reads its data from the Django API",
    "proxy_caddy": "the proxy routes to the backend",
    # The toolchain checks Python code, and the backend is the only Python
    # code a software project has; a gateway-only repository is not built.
    "gateway_litellm": "the toolchain needs the backend's Python code",
    "ml_pytorch": "the model is served through the Django API",
}


def problems() -> list[str]:
    """Return every reason the chosen components cannot make a project."""
    chosen = {name for name, answer in ANSWERS.items() if answer == "yes"}
    found = []
    if not chosen:
        # Nothing to build, test or deploy.
        found.append("Choose at least one component: " + ", ".join(ANSWERS))
    if "backend_django" not in chosen:
        for name, reason in NEEDS_BACKEND.items():
            if name in chosen:
                found.append(f"{name} needs backend_django: {reason}.")
    return found


def main() -> None:
    """Exit with every problem found, or do nothing."""
    if tuple(map(int, PYTHON_VERSION.split("."))) < tuple(
        map(int, PYTHON_FLOOR.split("."))
    ):
        sys.exit("python_version must be 3.12 or newer.")
    found = problems()
    if found:
        sys.exit("\n".join(found))


if __name__ == "__main__":
    main()
