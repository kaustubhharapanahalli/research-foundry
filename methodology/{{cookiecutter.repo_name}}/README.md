# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Install

You need [uv](https://docs.astral.sh/uv/). It installs Python
{{ cookiecutter.python_version }} itself.

```bash
make install
```

{%- if cookiecutter.ml_pytorch == "yes" %}

On Linux, PyTorch comes from
{%- if cookiecutter.cuda_source == "cu126" %} the CUDA 12.6 index, which runs on
older drivers.
{%- else %} PyPI, built for CUDA 13, which needs NVIDIA driver 580 or newer.
{%- endif %} On macOS it uses the Apple GPU (MPS).
{%- endif %}

## Test

```bash
make test   # unit and functional tests
make ci     # everything CI runs, including coverage
```

{%- if cookiecutter.public_docs == "yes" %}

## Documentation

```bash
make docs   # builds the site in site/
```

The docs have how-to guides and an API reference generated from the
docstrings. Publishing is left to the project; no hosting workflow is
configured. To contribute, see [`CONTRIBUTING.md`](CONTRIBUTING.md).
{%- endif %}

## Publishing

The public repository is a curated export of the private one, never a
mirror of it. `make publish-check` builds the export from `HEAD`: every
tracked file except the agent files (`AGENTS.md`, `CLAUDE.md`,
`.agent-state/`, `.work/`, `.claude/`, `journal.md`) and `.publish-deny`.
It refuses the export if any line holds an Overleaf project ID, a home path
or a pattern listed in `.publish-deny`. `make publish REMOTE=<remote>` then
pushes it as one release commit on top of the last one, so no private
history travels.

## Layout

- `src/{{ cookiecutter.package_name }}/`: the package.
- `tests/unit/`: fast tests of one piece each.
- `tests/functional/`: whole pipelines on tiny inputs, CPU only.
  {%- if cookiecutter.public_docs == "yes" %}
- `docs/`: the documentation, built by MkDocs.
- `docs_src/`: the code each how-to guide includes, run by the tests.
  {%- endif %}
  {%- if cookiecutter.dataset_registry == "yes" %}
- `datasets/registry.yaml`: the datasets this project uses, by benchmark,
  where its copy lives and which version. It starts empty.
  {%- endif %}
  {%- if cookiecutter.run_records == "yes" %}
- `src/{{ cookiecutter.package_name }}/sidecars.py`: the witness and metrics
  files that form a versioned run record; see `docs/run-records.md` in Foundry.
  {%- endif %}
- `scripts/publish.py`: the public export (`make publish`).
- `docs/adr/`: architecture decision records.
- `.dev-config/`: every lint, type and test configuration.
  {%- if cookiecutter.license != "none" %}

## Licence

[{{ cookiecutter.license }}](LICENSE).
{%- endif %}
