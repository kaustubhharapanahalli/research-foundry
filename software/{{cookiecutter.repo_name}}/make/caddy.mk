# Proxy targets: Caddy in front of the backend{% if cookiecutter.frontend_nextjs == "yes" %} and the frontend{% endif %}. The image is
# the one compose.yaml pins; a foundry test keeps the two the same.
CADDY_IMAGE := caddy:2.11.4-alpine@sha256:6aeddd44c3078b0f9a35206472a11420648a79c184603ef95957d0a20044cb2b
CADDY_RUN := docker run --rm -v "$(CURDIR)/proxy:/etc/caddy:ro" \
	--tmpfs /data --tmpfs /config $(CADDY_IMAGE)
APP_SERVICES := proxy backend{% if cookiecutter.frontend_nextjs == "yes" %} frontend{% endif %}

.PHONY: proxy-check smoke-proxy

proxy-check: ## The Caddyfile is formatted and valid, by the pinned Caddy
	$(CADDY_RUN) sh -c 'caddy fmt /etc/caddy/Caddyfile | diff -u /etc/caddy/Caddyfile -'
	$(CADDY_RUN) caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

smoke-proxy: ## The stack behind the proxy: TLS, headers, forwarding, hosts
	DJANGO_SECRET_KEY="$$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
		$(COMPOSE) --profile app up --detach --build --wait $(APP_SERVICES)
	proxy="$$($(COMPOSE) ps --quiet proxy)"; \
		docker run --rm --network "container:$$proxy" \
		--volumes-from "$$proxy:ro" --user 65532 \
		-v "$(CURDIR)/scripts:/scripts:ro" --entrypoint python \
		{{ cookiecutter.repo_name }}-backend:dev /scripts/check_proxy.py; \
		status=$$?; $(COMPOSE) --profile app rm --stop --force $(APP_SERVICES); \
		exit $$status

lint: proxy-check
ci: smoke-proxy
