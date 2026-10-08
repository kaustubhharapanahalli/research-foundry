# {{ cookiecutter.paper_title }}

The paper of {{ cookiecutter.project_name }}. Overleaf is its main source;
{%- if cookiecutter.github_mirror == "yes" %} GitHub holds a mirror, where CI
builds and checks every push.
{%- else %} this repository has no other remote.
{%- endif %}

## Connect Overleaf

Create an Overleaf project, then add its git URL as the remote. Overleaf's
git bridge has a single branch, `master`:

```bash
git remote add overleaf https://git.overleaf.com/<project-id>
git push overleaf master
```

## Build

```bash
make venue   # once: fetch the venue's style kit, then commit venue/
make pdf     # build/paper.pdf
make check   # also fails on overfull lines and ChkTeX warnings
make arxiv   # a cleaned copy for arXiv, in build/arxiv
make arxiv-verify   # compile build/arxiv on its own, as arXiv will
```

You need a TeX Live 2025 installation, or Docker: `make check-container`
and `make arxiv-container` build inside the pinned TeX Live image instead.
`make arxiv-verify` always uses that image, with plain pdflatex and no
`latexmkrc`, because that is how arXiv builds. Run it before every upload.

## Layout

- `main.tex`: the paper; `sections/`: one file per section.
- `generated/numbers.tex`: every reported number, generated from verified
  results.
- `references.bib`: the bibliography, exported from Zotero by Better BibTeX.
- `tables/`, `figures/`: generated from results, and committed.
- `venue/`: the venue's style kit, fetched by `make venue`.
{%- if cookiecutter.venue == "icml" %}

For ICML, `make venue` fetches the kit for `venue_year` from ICML's site, and
refuses if that year's kit is not published yet.
{%- endif %}
