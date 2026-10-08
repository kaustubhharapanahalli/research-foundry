# The only command surface. Overleaf builds with latexmk alone, so nothing
# here is needed to compile; make adds the checks and the exports.
#
# TeX Live 2025 is arXiv's default, and its TeX Live 2025 accepts only bbl
# format 3.3, so CI builds in the same release, pinned by digest.
TEXLIVE_IMAGE := texlive/texlive:TL2025-historic@sha256:7056390eac37715fd3e01875037ceb4016cb17d44c611f7bbbfa7a012007979f
VENUE := {{ cookiecutter.venue }}
YEAR := {{ cookiecutter.venue_year }}
{%- if cookiecutter.venue == "icml" %}
ICML_URL ?= https://media.icml.cc/Conferences/ICML$(YEAR)/Styles/icml$(YEAR).zip
{%- endif %}
LATEXMK := latexmk -outdir=build -jobname=paper -Werror \
	-interaction=nonstopmode -halt-on-error
UV_SYNC := uv sync $(if $(wildcard uv.lock),--locked,)
# The image runs as root. As the calling user instead, so build/ stays
# writable on a Linux host; HOME gives TeX a writable cache.
DOCKER_RUN := docker run --rm --user "$$(id -u):$$(id -g)" -e HOME=/tmp

.PHONY: install lint fmt pdf check venue arxiv arxiv-export arxiv-verify ci \
	check-container ci-container arxiv-container

install: ## Install the locked tools and the git hook
	$(UV_SYNC)
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		uv run pre-commit install; \
	else \
		echo "Not a git repository yet: run git init, then make install again."; \
	fi

lint: ## Text checks, as .pre-commit-config.yaml defines them
	uv lock --check
	uv run pre-commit run --all-files

fmt: ## Apply Prettier only
	uv run pre-commit run prettier --all-files || true

pdf: ## Build build/paper.pdf; undefined references and citations fail it
{%- if cookiecutter.venue != "article" %}
	@test -n "$$(ls venue/$(VENUE)$(YEAR) 2>/dev/null)" || \
		{ echo "The $(VENUE) $(YEAR) style kit is missing: run make venue."; exit 1; }
{%- endif %}
	$(LATEXMK) main.tex

check: pdf ## The PDF builds clean: no overfull lines, no ChkTeX warnings
	@! grep -n "Overfull \\\\hbox" build/paper.log || \
		{ echo "Overfull lines above: rewrite them, never shrink the font."; exit 1; }
	@# Our own files only: -I0 keeps ChkTeX out of the venue's kit.
	chktex -q -I0 -l .chktexrc main.tex $(wildcard sections/*.tex tables/*.tex)

venue: ## Fetch the venue's style kit into venue/
{%- if cookiecutter.venue == "iclr" %}
	mkdir -p venue/iclr$(YEAR)
	for f in iclr$(YEAR)_conference.sty iclr$(YEAR)_conference.bst \
		math_commands.tex fancyhdr.sty natbib.sty; do \
		curl -fsSL -o venue/iclr$(YEAR)/$$f \
			https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr$(YEAR)/$$f \
		|| exit 1; \
	done
{%- elif cookiecutter.venue == "neurips" %}
	mkdir -p venue/neurips$(YEAR)
	curl -fsSL -o build-styles.zip \
		https://media.neurips.cc/Conferences/NeurIPS$(YEAR)/Styles.zip
	unzip -o -j build-styles.zip '*.sty' -d venue/neurips$(YEAR)
	rm build-styles.zip
{%- elif cookiecutter.venue == "icml" %}
	@if ! curl -fLsS -o icml$(YEAR).zip "$(ICML_URL)"; then \
		rm -f icml$(YEAR).zip; \
		echo "The ICML $(YEAR) style kit is not published at $(ICML_URL). Check https://icml.cc for that year's author instructions, or set venue_year to a year whose kit is published and draft against it." >&2; \
		exit 1; \
	fi
	@mkdir -p venue/icml$(YEAR) && \
		unzip -o -j icml$(YEAR).zip '*.sty' '*.bst' -d venue/icml$(YEAR); \
		status=$$?; rm -f icml$(YEAR).zip; exit $$status
{%- else %}
	@echo "The article layout needs no style kit."
{%- endif %}
	@echo "Fetched on $$(date -u +%F). Commit venue/ so Overleaf has it."

arxiv: check ## A cleaned copy for arXiv in build/arxiv
	@$(MAKE) --no-print-directory arxiv-export

arxiv-export: # The copy alone; make arxiv or arxiv-container runs it
	@test -f build/paper.bbl || \
		{ echo "No build/paper.bbl: run make arxiv, not arxiv-export."; exit 1; }
	rm -rf build/arxiv-src build/arxiv-src_arXiv build/arxiv
	mkdir -p build/arxiv-src
	cp -R main.tex references.bib sections generated tables figures \
		build/arxiv-src/
{%- if cookiecutter.venue != "article" %}
	@# arXiv runs pdflatex alone and never reads latexmkrc, so the kit goes
	@# beside main.tex, where pdflatex and BibTeX look first.
	cp venue/$(VENUE)$(YEAR)/* build/arxiv-src/
{%- endif %}
	cp build/paper.bbl build/arxiv-src/main.bbl
	uv run arxiv_latex_cleaner build/arxiv-src
	mv build/arxiv-src_arXiv build/arxiv
	rm -rf build/arxiv-src

arxiv-verify: ## Compile build/arxiv on its own, as arXiv does, in the image
	@test -d build/arxiv || { echo "No build/arxiv: run make arxiv."; exit 1; }
	@# A scratch copy, so the upload folder gets no aux or log files.
	$(DOCKER_RUN) -v "$(CURDIR)/build/arxiv":/upload:ro $(TEXLIVE_IMAGE) \
		sh -c 'cp -R /upload /tmp/arxiv && cd /tmp/arxiv && \
		for pass in 1 2; do \
			pdflatex -interaction=nonstopmode -halt-on-error main.tex \
				>/dev/null || { tail -n 30 main.log; exit 1; }; \
		done && test -s main.pdf && echo "build/arxiv compiles on its own."'

ci: lint check ## Exactly what CI runs, with this machine's TeX

check-container: ## make check inside the pinned TeX Live image
	$(DOCKER_RUN) -v "$(CURDIR)":/work -w /work $(TEXLIVE_IMAGE) \
		make check

ci-container: lint check-container ## make ci, with TeX from the pinned image

arxiv-container: check-container ## make arxiv, with TeX from the pinned image
	@$(MAKE) --no-print-directory arxiv-export
{% include "base/template.mk" -%}
