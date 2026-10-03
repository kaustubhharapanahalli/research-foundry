# Documentation targets, from foundry's public documentation standard.
# This file comes from the template; change it there and run
# `cruft update`, not here.

.PHONY: docs docs-coverage docs-clean

docs: ## Build strict HTML docs in site/ (PD11)
	uv run --group docs mkdocs build --strict

docs-coverage: ## Check public pages, API modules and docstring coverage (PD3)
	uv run --group docs python .dev-config/check_frontmatter.py --public-pages docs
	uv run --group docs python docs/check_reference.py {{ cookiecutter.package_name }}
	uv run --group docs interrogate --ignore-private --fail-under 100 src/{{ cookiecutter.package_name }}

docs-clean:
	rm -rf site/

# CI builds the docs too. Make merges these with ci's other prerequisites.
ci: docs docs-coverage
