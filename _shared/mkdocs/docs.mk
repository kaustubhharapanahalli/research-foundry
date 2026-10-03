# Documentation targets, from foundry's public documentation standard.
# This file comes from the template; change it there and run
# `cruft update`, not here.

.PHONY: docs docs-coverage docs-clean refuse-private

docs: ## Build strict HTML docs in site/ (PD11)
	uv run --group docs mkdocs build --strict

docs-coverage: ## Check public pages, API modules and docstring coverage (PD3)
	uv run --group docs python .dev-config/check_frontmatter.py --public-pages docs
	uv run --group docs python docs/check_reference.py {{ cookiecutter.package_name }}
	uv run --group docs interrogate --ignore-private --fail-under 100 src/{{ cookiecutter.package_name }}

docs-clean:
	rm -rf site/

refuse-private: ## Refuse Pages deployment unless GitHub reports a public repository
	@private=$$(gh api "repos/$$GITHUB_REPOSITORY" --jq .private) || { echo "refusing Pages deployment: could not verify repository visibility" >&2; exit 1; }; \
	if [ "$$private" != "false" ]; then \
		echo "refusing Pages deployment: expected repository privacy to be false, got '$$private'" >&2; exit 1; \
	fi

# CI builds the docs too. Make merges these with ci's other prerequisites.
ci: docs docs-coverage
