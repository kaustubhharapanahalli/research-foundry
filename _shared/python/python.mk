# Python targets every template with Python shares. This file comes from the
# template; change it there and run `cruft update`, not here.
PYTEST := uv run pytest -c .dev-config/pytest.ini --rootdir .
# Locked once uv.lock exists; the very first install creates it.
UV_SYNC := uv sync --all-groups $(if $(wildcard uv.lock),--locked,)

.PHONY: install lint fmt test test-unit test-functional test-all coverage ci

install: ## Install the locked environment and the git hook
	$(UV_SYNC)
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		uv run pre-commit install; \
	else \
		echo "Not a git repository yet: run git init, then make install again."; \
	fi

lint: ## Every static check, as .pre-commit-config.yaml defines them
	uv lock --check
	uv run pre-commit run --all-files

fmt: ## Apply the formatters only
	uv run pre-commit run black --all-files || true
	uv run pre-commit run isort --all-files || true
	uv run pre-commit run prettier --all-files || true

test: ## Unit and functional tests, without slow or GPU tests
	$(PYTEST) -m "not slow and not gpu"

test-unit:
	$(PYTEST) -m "unit and not gpu"

test-functional:
	$(PYTEST) -m "functional and not gpu"

test-all: ## Everything that runs without a GPU
	$(PYTEST) -m "not gpu"

coverage: ## Everything that runs without a GPU, failing below 90% coverage
	$(PYTEST) -m "not gpu" --cov --cov-config=.dev-config/coveragerc

ci: lint coverage ## Exactly what CI runs
