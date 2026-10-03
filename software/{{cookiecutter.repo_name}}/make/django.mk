# Backend targets: Postgres, migrations, the API schema, the deploy check
# and the image. Make merges the extra prerequisites below with
# python.mk's own targets.
MANAGE := uv run python backend/manage.py
COMPOSE := docker compose
# Values for the checks only, never for a deployment.
CHECK_ENV := DJANGO_SETTINGS_MODULE=config.settings.prod \
	DJANGO_SECRET_KEY="$$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
	DJANGO_ALLOWED_HOSTS=example.org \
	DJANGO_CSRF_TRUSTED_ORIGINS=https://example.org \
	POSTGRES_PASSWORD=check-only

.PHONY: db db-down migrations-check schema deploy-check image smoke run

db: ## Start Postgres and wait until it accepts connections
	$(COMPOSE) up -d --wait db

db-down: ## Stop Postgres and any app container; the data volume is kept
	$(COMPOSE) --profile app down

migrations-check: db ## Fail if a model change has no migration
	$(MANAGE) makemigrations --check --dry-run

schema: ## Write the OpenAPI schema; any warning fails
	mkdir -p build
	$(MANAGE) spectacular --validate --fail-on-warn --file build/openapi.yaml

deploy-check: ## Django's deployment checklist against prod settings
	$(CHECK_ENV) $(MANAGE) check --deploy --fail-level WARNING

image: ## Build the production image
	$(COMPOSE) build backend

smoke: image db ## Serve the image against Postgres and call /health/
	$(COMPOSE) run --rm -v "$(CURDIR)/scripts:/scripts:ro" \
		-e DJANGO_SECRET_KEY="$$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
		backend sh /scripts/smoke.sh

run: db ## The development server on http://localhost:8000
	$(MANAGE) migrate
	$(MANAGE) runserver

lint: migrations-check schema deploy-check
test test-unit test-functional test-all coverage: db
ci: smoke
