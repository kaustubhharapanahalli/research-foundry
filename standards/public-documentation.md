---
type: Standard
title: Public Documentation Standard
description: The numbered rules for the documentation of any public repository generated from foundry, set at the level of PyTorch's own documentation, each with its reason, an example, its source and the check that enforces it.
resource: /standards/public-documentation.md
tags: [standard, documentation, mkdocs, docstrings, public]
timestamp: 2026-10-02T00:00:00Z
status: accepted
version: 2.0.0
---

# Public documentation standard

Version 2.0.0. This standard covers the documentation of a public
repository: its API reference, guides, tutorials and project files. Design
documents and Architecture Decision Records (ADRs) are internal documents
and keep their full OKF frontmatter: `type`, `title`, `description`,
`resource`, `tags` and `timestamp`, as `_shared/docs/check_frontmatter.py`
checks.

The `public-docs` skill applies these rules and cites them by number. It does
not restate them.

**Sources.** Every source cited below was opened on 2026-10-02.
PyTorch remains the reference for documentation practices. The toolchain uses
the current releases of mkdocs-material, mkdocstrings and its Python handler,
configured for Google-style docstrings.

**Why not PyTorch's own toolchain.** PyTorch remains the reference for the
practices in this standard, but research-foundry does not inherit PyTorch's
Sphinx constraints. The current releases of mkdocs-material, mkdocstrings and
its Python handler, configured with
`docstring_style: google`, provide the site and API reference. This keeps one
Google-style docstring format in source, generated projects and the rendered
reference.

## Rules

### PD1. Each page is one of the four kinds

A page is a tutorial, a how-to guide, a reference page or an explanation,
never a mix. Tutorials may be ordered from beginner to advanced inside their
section.

- **Why:** a reader looking up an argument should not wade through a lesson,
  and a learner should not be handed a reference table.
- **Example:** `docs/tutorials/first-run.md` teaches.
  `docs/how-to/repeat-a-run.md` answers one question. `docs/api/` is generated.
  `docs/explanation/` says why.
- **Source:** [Diátaxis, "Diátaxis"](https://diataxis.fr/); [NumPy, "A guide to NumPy documentation"](https://numpy.org/doc/stable/dev/howto-docs.html).
- **Check:** the `public-docs` skill reviews the page kind.

### PD2. Every public symbol has a docstring

Every public module, class, function and method has a docstring.

- **Why:** the reference is generated from docstrings, so a missing docstring
  is a missing page.
- **Example:** `def resolve_device(requested: str) -> torch.device:` begins
  with a summary line.
- **Source:** [Ruff, "pydocstyle (D)"](https://docs.astral.sh/ruff/rules/#pydocstyle-d).
- **Check:** `make lint` runs Ruff's pydocstyle `D` rules with
  `convention = "google"`.

### PD3. Every public symbol appears in the reference

The API reference contains a generated mkdocstrings `:::` block for every
public module and includes all of that module's public symbols. Public
docstring coverage is 100%. A pull request fails if a public module, symbol or
docstring is missing.

- **Why:** a documented function nobody can find is undocumented.
- **Example:** a generated `docs/api/index.md` contains
  `::: package.devices` and its configured member list includes
  `resolve_device`.
- **Source:** [mkdocstrings, "Automatic code reference pages"](https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages); [Interrogate, "Usage"](https://interrogate.readthedocs.io/en/latest/#usage).
- **Check:** `make docs-coverage` will generate and validate the `:::` module
  blocks, then run Interrogate with a 100% threshold. Not yet enforced; the
  docs scaffolding moves to mkdocs in a later change.

### PD4. Docstrings are Google style, and fit in 79 columns

Use `Args:`, `Returns:` or `Yields:`, `Raises:`, `Examples:` and, where they
apply, `Attributes:` and `Shape:`. Types come from the annotations, not the
prose. No line is longer than 79 characters. mkdocstrings' Python handler uses
`docstring_style: google`.

- **Why:** one shape for every docstring makes the reference predictable.
  PyTorch keeps docstrings to 80 columns so they fit into Jupyter
  documentation popups, and Black's limit here is 79.
- **Example:** see `seeding.seed_everything` in a generated methodology
  repository.
- **Source:** [PyTorch, "Writing documentation"](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#writing-documentation); [mkdocstrings Python, "Docstrings"](https://mkdocstrings.github.io/python/usage/configuration/docstrings/); [the repository Ruff configuration](../.dev-config/ruff.toml).
- **Check:** `make lint` runs Ruff's pydocstyle `D` rules with
  `convention = "google"`; Black and Flake8 enforce the line length.

### PD5. Tensor shapes go in a `Shape:` section

A function or module that takes or returns tensors states their shapes in a
`Shape:` section. Use `*` for any number of leading dimensions and named sizes
such as `(*, H_in)`. mkdocstrings' Google parser (griffe) renders a section it does not
know, such as `Shape:`, as an admonition titled **Shape** (checked against
griffe on 2026-10-02).

- **Why:** shapes are the contract of tensor code, and they are what readers
  look for first.
- **Example:** `Shape: input (*, H_in); output (*, H_out)`.
- **Source:** [PyTorch, `Linear`, "Shape"](https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/linear.py); [mkdocstrings Python, "Docstrings"](https://mkdocstrings.github.io/python/usage/configuration/docstrings/).
- **Check:** the `public-docs` skill reviews the source section and
  `make docs` will verify that mkdocstrings renders it. Not yet enforced; the
  docs scaffolding moves to mkdocs in a later change.

### PD6. Mathematics uses dollar delimiters in raw docstrings

Write inline mathematics as `$...$` and display mathematics as `$$...$$` in
raw `r"""` docstrings. `pymdownx.arithmatex` passes the expressions to MathJax
when mkdocs builds the site.

- **Why:** raw strings preserve mathematical backslashes, and one Markdown
  syntax renders consistently in docstrings and pages.
- **Example:** `r"""Applies $y = xA^T + b$."""`
- **Source:** [Python-Markdown Extensions, "Arithmatex"](https://facelessuser.github.io/pymdown-extensions/extensions/arithmatex/); [MathJax, "Writing Mathematics for MathJax"](https://docs.mathjax.org/en/latest/basic/mathematics.html); [Ruff, "escape-sequence-in-docstring (D301)"](https://docs.astral.sh/ruff/rules/escape-sequence-in-docstring/).
- **Check:** `make lint` runs Ruff `D301`; `make docs` will run
  `mkdocs build --strict` with `pymdownx.arithmatex`. Not yet enforced; the
  docs scaffolding moves to mkdocs in a later change.

### PD7. Every docstring example runs, and prints the same thing every time

`Examples:` blocks are doctests. They run under `pytest --doctest-modules`, and
they print shapes or exact values, never random numbers.

- **Why:** an example that does not run teaches the wrong thing, and an
  example with random output cannot be tested.
- **Example:** `>>> seed_everything(7).initial_seed()` prints `7`.
- **Source:** [Python, "doctest — Test interactive Python examples"](https://docs.python.org/3/library/doctest.html); [scikit-learn, "Docstring examples"](https://scikit-learn.org/stable/developers/contributing.html#docstring-examples).
- **Check:** `make test` runs pytest doctests.

### PD8. How-to code lives in files that tests run

A how-to guide's code is a real file under `docs_src/`, included into the page
with `pymdownx.snippets`. A test runs it in a fresh interpreter and checks that
it prints what the guide says.

- **Why:** code pasted into Markdown goes stale silently. A file that a test
  runs cannot. A fresh interpreter keeps one script's seeds and settings out
  of the next test.
- **Example:** `docs_src/repeat_a_run.py` is included by
  `docs/how-to/repeat-a-run.md`, and `tests/functional/test_docs_src.py`
  requires it to print `True`.
- **Source:** [Python-Markdown Extensions, "Snippets"](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/).
- **Check:** `make test` runs the `docs_src` functional tests; `make docs` will
  refuse a missing snippet. Not yet enforced; the docs scaffolding moves to
  mkdocs in a later change.

### PD9. Tutorials run on every build

A tutorial is an executable script that mkdocs-gallery runs every time the
docs are built. Work that needs a GPU runs on a small CPU input in the docs
build. mkdocs-gallery is the chosen runner because scripts remain directly
executable and diffable, and it preserves the existing script-based tutorial
contract without notebook state or committed outputs.

- **Why:** a tutorial that stops running is the first thing a new user meets.
- **Example:** `docs/tutorials/plot_first_run.py`, executed by mkdocs-gallery.
- **Source:** [mkdocs-gallery, "mkdocs-gallery"](https://smarie.github.io/mkdocs-gallery/); [PyTorch tutorials, "README"](https://github.com/pytorch/tutorials).
- **Check:** `make docs` will run mkdocs-gallery and fail on an example error.
  Not yet enforced; the docs scaffolding moves to mkdocs in a later change.

### PD10. Changes are marked, and deprecations name two versions

Mark additions and changes with MkDocs admonitions titled `Added in version`
and `Changed in version`. A deprecation uses an admonition titled
`Deprecated`, gives the reason and replacement, and names both the version
that deprecated it and the version that removes it. Removal is at least two
releases later.

- **Why:** users upgrading need to know what changed under them, and when
  something they use will go.
- **Example:** `!!! warning "Deprecated in 1.2; removed in 1.4"` followed by
  `Use resolve_device instead.`
- **Source:** [Material for MkDocs, "Admonitions"](https://squidfunk.github.io/mkdocs-material/reference/admonitions/); [Django, "Documenting new features"](https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/#documenting-new-features); [scikit-learn, "Deprecation"](https://scikit-learn.org/stable/developers/contributing.html#deprecation).
- **Check:** the `public-docs` skill refuses a deprecation without both
  versions and reviews the addition and change admonitions.

### PD11. The docs build with no warnings

MkDocs builds in strict mode, so every warning is an error.

- **Why:** a warning in the docs build is a broken page or link that nobody
  sees until a reader does.
- **Example:** `make docs` runs `mkdocs build --strict`.
- **Source:** [MkDocs, `build`, "Options"](https://www.mkdocs.org/user-guide/cli/#mkdocs-build).
- **Check:** `make docs` will run `mkdocs build --strict`. Not yet enforced;
  the docs scaffolding moves to mkdocs in a later change.

### PD12. Links are checked

Lychee checks external links in the built site on pages a pull request changes
and checks every built page nightly. Lychee is the chosen checker because it
validates the rendered site independently of MkDocs, including generated API
pages, relative links and assets.

- **Why:** dead links are the most common docs defect, and checking every page
  on every push is slow and flaky.
- **Example:** `make docs-linkcheck` builds the site, then runs Lychee against
  the selected HTML files.
- **Source:** [Lychee, "Command-line usage"](https://github.com/lycheeverse/lychee#commandline-usage); [PyTorch, `check-links.yml`](https://github.com/pytorch/pytorch/blob/main/.github/workflows/_link_check.yml).
- **Check:** `make docs-linkcheck` will run Lychee against the built site. Not
  yet enforced; the docs scaffolding moves to mkdocs in a later change.

### PD13. Each release has its own docs

Mike publishes versioned docs for every release, with `stable` and `latest`
aliases and a preview for each pull request. The pipeline publishes `main` as
`latest` first; a release then publishes its tag and moves `stable`. Read the
Docs may host or preview the site, but it is not required.

- **Why:** readers on an older release need that release's docs.
- **Example:** `mike deploy --push --update-aliases 2.0 stable` publishes a
  release without replacing `latest` from `main`.
- **Source:** [mike, "Deploying docs"](https://github.com/jimporter/mike#deploying-docs); [Read the Docs, "Versions"](https://docs.readthedocs.com/platform/stable/versions.html); [PyTorch, "Docs"](https://pytorch.org/docs/stable/).
- **Check:** the release workflow will run Mike and verify the release,
  `stable` and `latest` versions. Not yet enforced; the docs scaffolding moves
  to mkdocs in a later change.

### PD14. The project files are present

A public repository has:

- `README.md` and `LICENSE`;
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 3.0) and
  `SECURITY.md`;
- `CHANGELOG.md` (Keep a Changelog 1.1.0);
- for research software, `CITATION.cff` (Citation File Format version 1.2.0).

- **Why:** they answer the questions a visitor asks first: what it is, whether
  they may use it, how to help, how to report a flaw, and how to cite it.
- **Source:** [GitHub, "About community profiles for public repositories"](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories); [Keep a Changelog, "1.1.0"](https://keepachangelog.com/en/1.1.0/); [Citation File Format, "Schema guide"](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md).
- **Check:** `make lint` runs the project-file test.

### PD15. Prose follows the Google developer documentation style

Write in the second person and the present tense, with active voice. Images
have alt text. Link text makes sense on its own. Heading levels are not
skipped, and colour is never the only signal.

- **Why:** one voice across projects, and people using screen readers can use
  the documentation.
- **Source:** [Google, "Developer documentation style guide"](https://developers.google.com/style); [Google, "Accessibility"](https://developers.google.com/style/accessibility).
- **Check:** the `public-docs` skill reviews prose; Vale checks it where Vale
  is configured.

### PD16. Public pages carry only `title` and `description`

A public documentation page's YAML frontmatter has `title` and `description`,
nothing more. Design documents and ADRs keep the full OKF frontmatter.

- **Why:** MkDocs exposes YAML frontmatter as page metadata for themes and
  plugins. Agent-facing workflow fields do not belong in public page metadata
  and mean nothing to a public reader.
- **Source:** [MkDocs, "Meta-data"](https://www.mkdocs.org/user-guide/writing-your-docs/#meta-data).
- **Check:** the `public-docs` skill reviews page frontmatter; a mkdocs page
  metadata check will enforce the two-key allowlist. Not yet enforced; the
  docs scaffolding moves to mkdocs in a later change.

### PD17. No agent files in a public repository

`AGENTS.md`, `CLAUDE.md`, `.agent-state/`, `.work/` and `.claude/` never appear
in a public repository.

- **Why:** they are private working material. The public copy is made by
  `make publish`, which leaves them out.
- **Source:** [Architecture Decision Record 0007, "The public export, `make publish`"](../docs/adr/0007-public-export.md#adr-0007-the-public-export-make-publish).
- **Check:** `make publish` refuses an export that contains an agent file.

## Not decided here

- **Vale, and spelling with cspell.** Both are named in PD15 but not yet
  configured in the templates.
- **A TypeScript reference.** TypeDoc, for the software template, waits on
  TypeDoc supporting TypeScript 7. Its peer range stops at 6.0, unverified
  beyond that.
