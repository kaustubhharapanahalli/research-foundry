"""Remove the files of options the project did not choose.

Cookiecutter runs this inside the generated project, without asking. It
only deletes files inside that project: no network, nothing outside it.
"""

import shutil
from pathlib import Path

# Rendered by cookiecutter before it runs; typed as str so a type checker
# reading the unrendered file does not see two unequal literals.
ANSWERS: dict[str, str] = {
    "frontend_nextjs": "{{ cookiecutter.frontend_nextjs }}",
    "proxy_caddy": "{{ cookiecutter.proxy_caddy }}",
    "gateway_litellm": "{{ cookiecutter.gateway_litellm }}",
    "ml_pytorch": "{{ cookiecutter.ml_pytorch }}",
    "license": "{{ cookiecutter.license }}",
}


def main() -> None:
    """Delete what the answers left out."""
    if ANSWERS["frontend_nextjs"] != "yes":
        shutil.rmtree("frontend")
        Path("make", "nextjs.mk").unlink()
    if ANSWERS["proxy_caddy"] != "yes":
        shutil.rmtree("proxy")
        for name in ("make/caddy.mk", "compose.deploy.yaml"):
            Path(name).unlink()
        Path("scripts", "check_proxy.py").unlink()
    if ANSWERS["gateway_litellm"] != "yes":
        shutil.rmtree("gateway")
        Path("make", "litellm.mk").unlink()
        Path("scripts", "check_gateway.py").unlink()
    if ANSWERS["ml_pytorch"] != "yes":
        shutil.rmtree(Path("backend", "ml"), ignore_errors=True)
        shutil.rmtree(Path("backend", "apps", "inference"), ignore_errors=True)
    if ANSWERS["license"] == "none":
        Path("LICENSE").unlink()


if __name__ == "__main__":
    main()
