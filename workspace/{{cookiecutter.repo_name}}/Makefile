# The only command surface. CI calls `make install` and `make ci` only.
UV_SYNC := uv sync $(if $(wildcard uv.lock),--locked,)

.PHONY: install lint fmt ci layout-check

install: ## Install the locked tools and the git hook
	$(UV_SYNC)
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		uv run pre-commit install; \
		if git lfs version >/dev/null 2>&1; then \
			git lfs install --local; \
		else \
			echo "Git LFS is not installed; install it from https://git-lfs.com/ to track presentation decks."; \
		fi; \
	else \
		echo "Not a git repository yet: run git init, then make install again."; \
	fi

lint: ## Every check, as .pre-commit-config.yaml defines them
	uv lock --check
	uv run pre-commit run --all-files

fmt: ## Apply Prettier only
	uv run pre-commit run prettier --all-files || true

ci: lint ## Exactly what CI runs
{% include "base/template.mk" -%}

layout-check: ## Check paths against the template contract (needs research-foundry 0.2.0 or later)
	uvx --from 'research-foundry>=0.2.0' research-foundry layout .
