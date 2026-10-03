# Documentation targets, from foundry's public documentation standard.
# This file comes from the template; change it there and run
# `cruft update`, not here.
SPHINX := uv run sphinx-build -W -n --keep-going -q

.PHONY: docs docs-coverage docs-linkcheck docs-clean

docs: ## Build the HTML docs; any warning fails (PD11)
	$(SPHINX) -b html docs docs/_build/html

docs-coverage: ## Fail on a public symbol missing from the reference (PD3)
	$(SPHINX) -b coverage docs docs/_build/coverage

docs-linkcheck: ## Check every external link; needs the network (PD12)
	$(SPHINX) -b linkcheck docs docs/_build/linkcheck

docs-clean:
	rm -rf docs/_build docs/api/generated

# CI builds the docs too. Make merges these with ci's other prerequisites.
ci: docs docs-coverage
