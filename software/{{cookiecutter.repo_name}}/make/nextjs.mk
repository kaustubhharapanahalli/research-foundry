# Frontend targets: Next.js in frontend/, run with the pnpm and Node
# versions frontend/package.json pins. Make merges the extra prerequisites
# below with python.mk's own targets; lint runs through pre-commit.
FRONTEND := cd frontend &&
PLAYWRIGHT_DEPS := $(if $(CI),--with-deps,)

.PHONY: frontend-install frontend-test frontend-coverage frontend-dev smoke-stack

frontend-install: ## The locked frontend dependencies and the test browser
	$(FRONTEND) pnpm install $(if $(wildcard frontend/pnpm-lock.yaml),--frozen-lockfile,)
	$(FRONTEND) pnpm exec playwright install $(PLAYWRIGHT_DEPS) chromium

frontend-test: ## Unit, component and integration tests
	$(FRONTEND) pnpm exec vitest run

frontend-coverage: db ## Unit, component and end-to-end tests; 90% merged
	rm -rf frontend/coverage
	$(FRONTEND) pnpm exec vitest run
	$(FRONTEND) COVERAGE=1 pnpm exec next build
	$(FRONTEND) pnpm exec playwright test
	$(FRONTEND) pnpm exec node scripts/coverage.mjs

frontend-dev: db ## The development server on http://localhost:3000
	$(FRONTEND) BACKEND_URL=http://127.0.0.1:8000 pnpm exec next dev

smoke-stack: ## Both production images together, then a graceful stop
	DJANGO_SECRET_KEY="$$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
		$(COMPOSE) --profile app up --detach --build --wait backend frontend
	$(COMPOSE) exec -T frontend node - < frontend/tests/smoke/stack.mjs \
		&& $(COMPOSE) --profile app stop --timeout 10 frontend \
		&& $(COMPOSE) --profile app ps --all --format json frontend | grep -q '"ExitCode":143' \
		&& echo "smoke: the frontend finished on SIGTERM (exit 143), not killed"; \
		status=$$?; $(COMPOSE) --profile app rm --stop --force backend frontend; \
		exit $$status

install: frontend-install
test: frontend-test
coverage: frontend-coverage
ci: smoke-stack
