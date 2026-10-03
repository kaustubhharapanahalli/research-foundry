# The public export: this private repository's HEAD without the agent files,
# refused if it holds a private item, pushed as one release commit with no
# private history (scripts/publish.py). Neither target is part of `make ci`.
.PHONY: publish-check publish
publish-check: ## Build and scan the public export; push nothing
	uv run python scripts/publish.py check

publish: ## Push the public export as one release commit (REMOTE=name-or-url, BRANCH=main)
	@test -n "$(REMOTE)" || { echo "REMOTE=<the public repository's remote or URL>"; exit 2; }
	uv run python scripts/publish.py push "$(REMOTE)" $(if $(BRANCH),--branch $(BRANCH))
