# {{ cookiecutter.paper_title }}: agent instructions for the paper

The paper of the research project `{{ cookiecutter.project_slug }}`. The code
is `{{ cookiecutter.repo_base }}` and the workspace
`{{ cookiecutter.repo_base }}-workspace`.

This file is never committed: the paper repo ignores it, and Overleaf is the
paper's main source.

## How the paper is built

- `main.tex` at the root, built with pdflatex through `latexmkrc`, so
  Overleaf and `make pdf` build the same thing.
- `make pdf` writes `build/paper.pdf`. An undefined reference or citation
  fails the build.
- `make check` also fails on overfull lines and on ChkTeX warnings.
{%- if cookiecutter.venue != "article" %}
- `make venue` fetches the venue's style kit into `venue/`; commit `venue/`
  so Overleaf has it.
{%- endif %}
{%- if cookiecutter.venue == "icml" %} It refuses a `venue_year` whose ICML
  kit is not published; never substitute another year's kit.
{%- endif %}
- `make arxiv` writes a cleaned copy to `build/arxiv`, with the venue kit
  beside `main.tex`. `make arxiv-verify` compiles that copy on its own in
  the pinned image; an upload is ready only when it passes.
- `make template-check` says whether the foundry template has moved on;
  `cruft update` brings the change in.

## Rules for the text

1. **Every reported number comes from `generated/numbers.tex`**, which is
   generated from verified results. Never type a result into the prose.
2. **Submission is anonymous.** `\camerareadyfalse` stays until the
   camera-ready version. Names, acknowledgements and identifying links are
   written inside `\ifcameraready`.
3. **Overleaf has one branch and no symlinks.** Work on `master`, and do not
   add links.
4. **Formatters only check LaTeX here.** They never rewrite it, so an edit
   just pulled from Overleaf is never overwritten.
5. **Generated files are committed**: numbers, tables and figures. Overleaf
   cannot run `make`.

## Local rules

Rules here override the global standards for this paper only. Name the
global rule, the override, and why.

_None yet._
