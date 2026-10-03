# The only command surface. CI calls `make install` and `make ci` only.
include make/python.mk
include make/publish.mk
{%- if cookiecutter.public_docs == "yes" %}
include make/docs.mk
{%- endif %}
{%- if cookiecutter.ml_pytorch == "yes" %}

# Thread and worker counts are flags, never guesses. The environment
# variables are a backstop for libraries that start threads before
# torch.set_num_threads runs.
THREADS ?= 4
WORKERS ?= 2
DEVICE ?= cpu
RUN_ENV := OMP_NUM_THREADS=$(THREADS) MKL_NUM_THREADS=$(THREADS) \
	OPENBLAS_NUM_THREADS=$(THREADS)

.PHONY: test-gpu run

test-gpu: ## GPU tests, on the target machine, before any real run
	$(PYTEST) -m gpu

run: ## make run MODULE={{ cookiecutter.package_name }}.train ARGS="..."
	$(if $(MODULE),,$(error MODULE is not set: try make run MODULE={{ cookiecutter.package_name }}.train))
	$(RUN_ENV) uv run python -m $(MODULE) --device $(DEVICE) \
		--threads $(THREADS) --num-workers $(WORKERS) $(ARGS)
{%- endif %}
{% include "base/template.mk" -%}
