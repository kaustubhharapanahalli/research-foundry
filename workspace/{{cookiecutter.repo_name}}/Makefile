# The only command surface. CI calls `make install` and `make ci` only.
UV_SYNC := uv sync $(if $(wildcard uv.lock),--locked,)

.PHONY: install lint fmt ci

install: ## Install the locked tools and the git hook
	$(UV_SYNC)
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		uv run pre-commit install; \
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
