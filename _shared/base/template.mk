
# Whether a newer foundry template exists than the one this project was
# made from. cruft records that commit in .cruft.json. Not part of `make ci`:
# the check reads the template repository over the network on every run, so
# it is run by hand rather than in every CI build.
.PHONY: template-check
template-check: ## Report whether the foundry template has moved on
	@test -f .cruft.json || { echo "No .cruft.json: not created with cruft create."; exit 1; }
	uvx --from cruft==2.16.0 cruft check
