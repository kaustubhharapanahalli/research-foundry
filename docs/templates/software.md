---
type: Guide
title: "Software Template Guide"
description: How to generate and update an application repository, what every template answer controls, and which combinations the template refuses.
resource: /docs/templates/software.md
tags: [guide, template, software, django, nextjs, cookiecutter, cruft]
timestamp: 2026-10-02T00:00:00Z
---

# Software template guide

The software template creates one application repository from optional Django,
Next.js, Caddy, LiteLLM, and PyTorch components. The component guards keep every
generated combination buildable by requiring the Django backend whenever another
component depends on it.

## Generate and update

```bash
cruft create https://github.com/kaustubhharapanahalli/research-foundry --directory software
```

From the generated repository:

```bash
cruft check
cruft update
make template-check
```

`cruft check` and `make template-check` report whether the template has moved on;
`cruft update` brings its changes into the generated repository for review.

## Questions and output

The prompt column reproduces `software/cookiecutter.json`. Where that file has no
custom prompt, Cookiecutter displays the key shown in backticks. A value in braces
is rendered from an earlier answer.

| Key               | Prompt                                                                  | Choices                     | Default                                                       | What the answer produces                                                                                                                                            |
| ----------------- | ----------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_name`    | Project name, as people write it                                        | Text                        | `My Project`                                                  | Human-readable name in the README, frontend shell, package metadata, and local guidance.                                                                            |
| `project_slug`    | Project slug (the board label and session names use it)                 | Text                        | `{project_name in lowercase with spaces replaced by hyphens}` | Stable project identifier in generated guidance and metadata.                                                                                                       |
| `repo_base`       | Repository base name (may differ from the slug)                         | Text                        | `{project_slug}`                                              | Base for the repository name.                                                                                                                                       |
| `repo_name`       | `repo_name`                                                             | Text                        | `{repo_base}`                                                 | Name of the generated root directory, Python project, Compose project, and frontend package.                                                                        |
| `description`     | `description`                                                           | Text                        | `A web application.`                                          | Description in the README and `pyproject.toml`.                                                                                                                     |
| `author_name`     | `author_name`                                                           | Text                        | `Your Name`                                                   | Author in `pyproject.toml`.                                                                                                                                         |
| `github_owner`    | `github_owner`                                                          | Text                        | `your-github-user`                                            | Repository ownership references in generated guidance.                                                                                                              |
| `license`         | Licence                                                                 | `Apache-2.0`, `MIT`, `none` | `Apache-2.0`                                                  | Renders the selected `LICENSE` and package licence. `none` removes `LICENSE` and omits the licence metadata.                                                        |
| `python_version`  | `python_version`                                                        | Text                        | `3.14`                                                        | Writes `.python-version` and selects the development interpreter; support still begins at Python 3.12.                                                              |
| `backend_django`  | Include the Django and DRF backend, with Postgres?                      | `yes`, `no`                 | `yes`                                                         | `yes` enables Django, Django REST Framework (DRF), Postgres, backend Make targets, settings, accounts, core, and notes apps. Every valid component set includes it. |
| `frontend_nextjs` | Include the Next.js frontend? (it needs the backend)                    | `yes`, `no`                 | `yes`                                                         | `yes` keeps `frontend/` and `make/nextjs.mk`; `no` removes both.                                                                                                    |
| `proxy_caddy`     | `proxy_caddy`                                                           | `yes`, `no`                 | `yes`                                                         | `yes` keeps `proxy/`, `make/caddy.mk`, `compose.deploy.yaml`, and `scripts/check_proxy.py`; `no` removes them.                                                      |
| `gateway_litellm` | `gateway_litellm`                                                       | `no`, `yes`                 | `no`                                                          | `yes` keeps `gateway/`, `make/litellm.mk`, and `scripts/check_gateway.py`; `no` removes them.                                                                       |
| `ml_pytorch`      | Serve a PyTorch model from the backend? (CPU wheels on Linux)           | `no`, `yes`                 | `no`                                                          | `yes` keeps `backend/ml/` and `backend/apps/inference/` and adds NumPy, PyTorch, tests, and the Linux CPU-wheel source; `no` removes both directories.              |
| `db_port`         | Host port for the development Postgres (pick one no other project uses) | Text                        | `5440`                                                        | Sets the host-side Postgres port in `.env.example` and the development Compose configuration.                                                                       |

The internal `_python_floor` key fixes the supported floor at `3.12`,
`_template_kind` records `software`, and `_copy_without_render` preserves frontend
source files whose own braces are not Cookiecutter expressions. They are not
questions.

Every valid project also receives shared editor, Git, pre-commit, continuous
integration, Python quality, Make, publication, and test files; root Compose and
Docker files; the backend tree; a development setup architectural decision; and
smoke and publication scripts. The post-generation hook removes each unselected
component's paths listed above.

## Refused combinations

The pre-generation hook reports every component problem it finds:

- A `python_version` below 3.12: `python_version must be 3.12 or newer.`
- All five component answers set to `no`:
  `Choose at least one component: backend_django, frontend_nextjs, proxy_caddy, gateway_litellm, ml_pytorch`
- `backend_django=no` with `frontend_nextjs=yes`:
  `frontend_nextjs needs backend_django: the frontend reads its data from the Django API.`
- `backend_django=no` with `proxy_caddy=yes`:
  `proxy_caddy needs backend_django: the proxy routes to the backend.`
- `backend_django=no` with `gateway_litellm=yes`:
  `gateway_litellm needs backend_django: the toolchain needs the backend's Python code.`
- `backend_django=no` with `ml_pytorch=yes`:
  `ml_pytorch needs backend_django: the model is served through the Django API.`

If several invalid dependent components are selected, their messages are joined
with newlines.

## Governing decisions

- [Cookiecutter templates, updated with cruft, sharing one base](../adr/0001-cookiecutter-cruft-shared-base.md)
- [The software template's layout](../adr/0002-software-template-layout.md)
- [The Next.js frontend component and its pins](../adr/0003-frontend-component-and-pins.md)
- [What the software template leaves out, and why](../adr/0004-software-template-omissions.md)
- [The Caddy proxy and the LiteLLM gateway components](../adr/0005-proxy-and-gateway.md)
- [The `ml-pytorch` component in the software template](../adr/0006-ml-pytorch-in-software.md)
- [The public export, `make publish`](../adr/0007-public-export.md)
- [Python 3.12 support floor](../adr/0010-python-floor.md)
