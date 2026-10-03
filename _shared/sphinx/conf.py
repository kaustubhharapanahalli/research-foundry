"""Sphinx configuration for the {{ cookiecutter.project_name }} documentation.

It applies foundry's public documentation standard; the rule each setting
serves is named beside it. This file comes from the template: change it
there and run ``cruft update``, not here.
"""

# Sphinx reads these lower-case names, including ``copyright``.
# pylint: disable=invalid-name,redefined-builtin

from importlib.metadata import version as installed_version

project = "{{ cookiecutter.project_name }}"
author = "{{ cookiecutter.author_name }}"
copyright = "{% now 'utc', '%Y' %}, {{ cookiecutter.author_name }}"
release = installed_version("{{ cookiecutter.repo_name }}")
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

# PD11: every cross-reference must resolve. make docs adds -W.
nitpicky = True
# ADRs are internal documents with full OKF frontmatter (PD16).
exclude_patterns = ["_build", "adr"]
templates_path = ["_templates"]

# PD3: the reference is generated from the package, so nothing is left out.
autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# PD4 and PD5: Google docstrings, with PyTorch's Shape section.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_custom_sections = ["Shape"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
{%- if cookiecutter.get("ml_pytorch") == "yes" %}
    "numpy": ("https://numpy.org/doc/stable", None),
    "torch": ("https://docs.pytorch.org/docs/stable", None),
{%- endif %}
}

# PD3: make docs-coverage fails on any undocumented module or object.
coverage_modules = ["{{ cookiecutter.package_name }}"]
coverage_show_missing_items = True
coverage_statistics_to_stdout = False

github_owner = "{{ cookiecutter.github_owner }}"
github_repo = "{{ cookiecutter.repo_name }}"
html_theme = "pydata_sphinx_theme"
html_title = project
html_theme_options = {
    "github_url": f"https://github.com/{github_owner}/{github_repo}",
}
