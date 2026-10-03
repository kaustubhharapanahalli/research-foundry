# The only command surface. CI calls these targets and nothing else.
ifdef PYTHON
export UV_PYTHON := $(PYTHON)
endif

PYTEST := uv run pytest -c .dev-config/pytest.ini --rootdir . tests src/research_foundry --doctest-modules

.PHONY: install lint fmt test test-unit test-functional test-all test-heavy test-heavy-code test-heavy-software test-heavy-paper template-matrix install-skills throwaway free-runner-disk audit audit-generated audit-issue check-pins pins-issue dist release-check github-release refuse-private coverage ci

install: ## Install the locked toolchain and the git hook (PYTHON=3.12 to use another interpreter)
	uv sync --locked
	uv run pre-commit install

lint: ## Every static check, as pre-commit defines them
	uv lock --check
	uv run pre-commit run --all-files

fmt: ## Apply the formatters only
	uv run pre-commit run black --all-files || true
	uv run pre-commit run isort --all-files || true
	uv run pre-commit run prettier --all-files || true

test: ## Unit and functional tests, without the slow ones
	$(PYTEST) -m "not slow and not heavy"

test-unit:
	$(PYTEST) -m "unit and not heavy"

test-functional:
	$(PYTEST) -m "functional and not heavy"

test-all: ## Everything but the generated projects, including the cruft round trip
	$(PYTEST) -m "not heavy"

test-heavy: test-heavy-code test-heavy-software test-heavy-paper ## Every generated project's own make ci

test-heavy-code: ## The generated methodology and workspace projects (installs PyTorch)
	df -h .
	$(PYTEST) -m heavy -k "not paper and not software"; status=$$?; df -h .; exit $$status

test-heavy-software: ## The generated software projects (builds images, pulls LiteLLM)
	df -h .
	$(PYTEST) -m heavy -k software; status=$$?; df -h .; exit $$status

test-heavy-paper: ## The generated papers and their guards (pulls TeX Live)
	df -h .
	$(PYTEST) -m heavy -k paper; status=$$?; df -h .; exit $$status

template-matrix: ## Every template x every answer that changes its files: generate, install, ci, cruft update (hours; TEMPLATES=a,b and WHERE=name=value narrow it, OUT=dir moves the report)
	uv run python -m tools.template_matrix $(if $(TEMPLATES),--templates $(TEMPLATES)) $(foreach w,$(WHERE),--where $(w)) $(if $(OUT),--out $(OUT))

install-skills: ## Install skills/ for this user (~/.claude/skills), refusing to overwrite an edited copy (ARGS=--check, --adopt or --force)
	uv run python -m tools.install_skills $(ARGS)

throwaway: ## A throwaway project from a named variant, offline (VARIANT=name; ARGS for --into, --ref)
	@test -n "$(VARIANT)" || { echo "VARIANT=<name>: one of tools/variants.py"; exit 2; }
	uv run python -m tools.throwaway $(VARIANT) $(ARGS)

free-runner-disk: ## CI only: delete a GitHub runner's unused preinstalled toolchains
	df -h /
	sudo rm -rf /usr/local/lib/android /usr/share/dotnet /opt/ghc \
		/opt/hostedtoolcache/CodeQL /usr/local/share/boost
	df -h /

audit: ## Audit Foundry's locked dependencies for known vulnerabilities
	uv run python -m tools.audit

audit-generated: ## Generate, lock and audit every heavy project variant
	uv run python -m tools.audit_generated

audit-issue: ## Open or update the one weekly security-audit issue
	@number=$$(gh issue list --state open --label security --search 'Weekly dependency audit in:title' --json number --jq '.[0].number'); \
	if [ -n "$$number" ]; then \
		gh issue edit "$$number" --title "Weekly dependency audit" --body-file build/audit-report.md; \
	else \
		gh issue create --title "Weekly dependency audit" --label security --body-file build/audit-report.md; \
	fi

check-pins: ## Report current and newest pins hidden inside template files
	uv run python -m tools.check_pins

pins-issue: ## Open or update the one weekly template-pin issue
	@number=$$(gh issue list --state open --label dependencies --search 'Weekly template pin report in:title' --json number --jq '.[0].number'); \
	if [ -n "$$number" ]; then \
		gh issue edit "$$number" --title "Weekly template pin report" --body-file build/pins-report.md; \
	else \
		gh issue create --title "Weekly template pin report" --label dependencies --body-file build/pins-report.md; \
	fi

dist: ## Build source and wheel distributions into dist/
	uv build

release-check: ## Refuse unless TAG=v<project version> and its changelog section exists
	uv run python -m tools.release check --tag "$(TAG)"

github-release: ## Create the GitHub Release for TAG with distributions attached
	uv run python -m tools.release github-release --tag "$(TAG)"

refuse-private: ## Refuse publication unless GitHub reports a public repository
	uv run python -m tools.release refuse-private

coverage: ## test-all, failing below 90% coverage of the plain Python
	$(PYTEST) -m "not heavy" --cov --cov-config=.dev-config/.coveragerc

ci: lint coverage ## Exactly what GitHub CI runs (PYTHON=3.12 to use another interpreter)
