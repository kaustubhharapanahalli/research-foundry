# research-foundry

Cookiecutter templates for every kind of repository a research project
needs, kept current with [cruft](https://cruft.github.io/cruft/).

A research project here is three repositories, plus any application it grows
into. Each is generated from one template in this repository, and all of them
share one base, so a project starts with the same toolchain, tests,
continuous integration (CI) and documentation as every other project.

| Template      | Generates          | Holds                                                                  |
| ------------- | ------------------ | ---------------------------------------------------------------------- |
| `methodology` | `<name>`           | The code: a Python package, optionally with PyTorch                    |
| `workspace`   | `<name>-workspace` | Research notes, theory, literature reviews, experiment configs         |
| `paper`       | `<name>-paper`     | The LaTeX paper; Overleaf is its main source                           |
| `software`    | `<name>`           | An application: backend, frontend, proxy, gateway and model components |

Detailed template guides describe every question and generated file set:

- [Methodology template](docs/templates/methodology.md)
- [Workspace template](docs/templates/workspace.md)
- [Paper template](docs/templates/paper.md)
- [Software template](docs/templates/software.md)

`methodology`, `workspace` and `paper` are complete. `software` has five
components:

- the Django backend;
- the Next.js frontend;
- the Caddy proxy, on by default;
- the LiteLLM model gateway, off by default
  ([ADR 0005](docs/adr/0005-proxy-and-gateway.md));
- a PyTorch model served by the backend, off by default
  ([ADR 0006](docs/adr/0006-ml-pytorch-in-software.md)).

Component names are `<role>-<stack>`. `desktop-electron` and `mobile-<stack>` are reserved, not built
([ADR 0004](docs/adr/0004-software-template-omissions.md)). See [`CHANGELOG.md`](CHANGELOG.md) for what each release adds.

A `methodology` or `software` project that goes public is two repositories:
the private one, with the agent files, and a public one that receives only
`make publish`'s export, one release commit at a time with no private
history ([ADR 0007](docs/adr/0007-public-export.md)).

## Standards and skills

The templates encode written standards, and the skills apply them:

- [`standards/`](standards) holds the numbered rules, each with its reason,
  its source and the check that enforces it. They cover
  [public documentation](standards/public-documentation.md),
  [coding](standards/coding.md), [testing](standards/testing.md) and
  [security](standards/security.md).
- [`skills/`](skills) holds the agent skills that apply those rules. A skill
  cites rule numbers and never restates a rule. They live here, not in
  generated projects, and each person installs them once:

  ```bash
  make install-skills              # into ~/.claude/skills
  make install-skills ARGS=--check # what is missing, out of date or edited
  ```

  An installed copy edited in place is never overwritten: `--adopt` copies
  the edit back here, `--force` discards it. A skill of the same name that
  foundry did not install is never touched.

  The skills so far are `public-docs`, `publish`, `template-update`,
  `ci-local`, `paper-build` and `release`. Coding, testing and security skills
  will be added when Foundry has accepted standards for them.

## Using a template

Generate a project non-interactively from the packaged templates:

```bash
uvx research-foundry new <template>
```

To install the command first instead:

```bash
pip install research-foundry
research-foundry new <template>
```

Use `research-foundry templates` to list the template names and
`research-foundry questions <template>` to inspect their answers. Every new
project records its template release for later checks and updates:

```bash
research-foundry check <project-path>
research-foundry update <project-path>
```

As an alternative, cruft can generate directly from the public repository:

```bash
uvx cruft create https://github.com/kaustubhharapanahalli/research-foundry --directory methodology
```

Later, from inside the generated project:

```bash
uvx cruft check    # is the project behind its template?
uvx cruft update   # bring the template's changes in
```

Plain cookiecutter works too, and asks which template you want:

```bash
uvx cookiecutter https://github.com/kaustubhharapanahalli/research-foundry
```

## MCP server

Run the Model Context Protocol (MCP) server over standard input and output:

```bash
research-foundry mcp
```

It exposes `list_templates`, `describe_questions`, `plan_project`,
`create_project`, `check_project` and `update_project`. Planning renders only
inside a temporary directory. Creation and update refuse to write until their
`confirm` argument is `true`.

## How the shared base works

Cookiecutter has no inheritance between templates. It does let a template
include files from a `templates/` folder beside it. In this repository every
template's `templates/` folder is a link to [`_shared/`](_shared), and a
template file that should come from the base is one line:

```jinja
{% include "base/editorconfig" -%}
```

So a shared file exists once. A change to it reaches every template at the
next release, and every existing project through `cruft update`. The tests
check that every include resolves and that no shared file goes unused. The
decision and its alternatives are in
[ADR 0001](docs/adr/0001-cookiecutter-cruft-shared-base.md).

## Working on this repository

Everything runs through `make`:

```bash
make install   # locked toolchain and the git hook
make lint      # every static check, as .pre-commit-config.yaml defines them
make test      # unit and functional tests
make ci        # exactly what GitHub CI runs
```

Tool configuration lives in [`.dev-config/`](.dev-config). research-foundry
runs on Python 3.12 and newer and is tested on Python 3.12, 3.13 and 3.14.
Generated projects require Python 3.12 or newer and default to running Python
3.14. Dependencies are managed with `uv add` only.

## Trying the templates

Two targets generate real projects from this repository, without a network:

```bash
make throwaway VARIANT=software-everything   # one project, path printed
make template-matrix                          # every template, every tree
```

`make throwaway` makes one project from a named variant in
[`tools/variants.py`](tools/variants.py), the same list the heavy tests
run. It uses `cruft create` from this repository at HEAD, so a setup test
can have a real project offline. `ARGS="--into <dir> --ref <ref>"` places
it and picks the commit, and `ARGS=--working-tree` takes uncommitted
changes instead. An answer the template does not ask at that commit is
refused. Delete the directory when done.

`make template-matrix` finds, for each template, the answers whose values
change which files a project gets, and runs every combination of them.
Each combination is generated, then runs `make install`, `make ci`, and a
`cruft update` that must carry a shared change in. Combinations a
template's own hook refuses are listed with its reason and not run. Each
project is deleted afterwards. The report and step logs stay in
`build/template-matrix/`. It takes hours; `TEMPLATES=workspace,paper`
narrows it, `WHERE=ml_pytorch=yes` keeps the combinations with that answer,
and `OUT=<dir>` writes the report somewhere else.

## Citing research-foundry

If you build on research-foundry or publish work made with its templates, please cite it.

GitHub's **Cite this repository** button in the repository sidebar reads
`CITATION.cff` and offers APA and BibTeX citations.

```bibtex
@software{research_foundry,
  author = {Harapanahalli, Kaustubh},
  title = {research-foundry},
  version = {0.1.0},
  url = {https://github.com/kaustubhharapanahalli/research-foundry},
  license = {Apache-2.0},
  doi = {10.5281/zenodo.23123933}
}
```

The DOI is Zenodo's concept DOI: it names research-foundry as a whole and
resolves to the latest archived version.

`CITATION.cff` is the source, and a test keeps this entry in step with it.

## Licence

[Apache-2.0](LICENSE).
