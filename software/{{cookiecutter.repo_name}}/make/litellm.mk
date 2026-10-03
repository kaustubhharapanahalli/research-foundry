# Gateway targets: LiteLLM's proxy under the `gateway` compose profile.

.PHONY: smoke-gateway

smoke-gateway: image ## The gateway with two mock models: key, policy, health
	@out="$$(LITELLM_MASTER_KEY=no-prefix $(COMPOSE) --profile gateway \
		run --rm --no-deps gateway 2>&1)"; \
		case "$$out" in *"refusing to serve"*) \
			echo "gateway: refuses a key without the sk- prefix";; \
		*) echo "$$out"; exit 1;; esac
	key="sk-$$(uv run python -c 'import secrets; print(secrets.token_hex(24))')"; \
		LITELLM_MASTER_KEY="$$key" GATEWAY_CONFIG=tests/smoke.yaml \
		$(COMPOSE) --profile gateway up --detach --wait gateway \
		&& $(COMPOSE) run --rm --no-deps -v "$(CURDIR)/scripts:/scripts:ro" \
		-e LITELLM_MASTER_KEY="$$key" backend python /scripts/check_gateway.py; \
		status=$$?; $(COMPOSE) --profile gateway rm --stop --force gateway; \
		exit $$status

ci: smoke-gateway
