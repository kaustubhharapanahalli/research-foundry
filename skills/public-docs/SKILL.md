---
name: public-docs
description: Write and review the public documentation of a foundry-generated repository - API docstrings, the Sphinx reference, how-to guides, tutorials and the project files - to the public documentation standard (PD1-PD17). Use when adding or changing a public symbol, writing a docs page, deprecating anything, preparing a release, or asked to "document this", "write the docs" or "review the docs" in a repository that publishes them.
---

# Public documentation

The rules are in `standards/public-documentation.md` in foundry, numbered
PD1–PD17. This skill applies them and cites them. It does not restate them.
If this file and the standard disagree, the standard wins. Then fix this file.

## Which skill

- **This skill:** anything a reader outside the project sees. That includes
  docstrings of public symbols, `docs/` pages built by Sphinx, `docs_src/`, and
  the project files listed in PD14.
- **`docs-review`:** internal documents, meaning design documents, ADRs and
  agent-readable pages with full OKF frontmatter. An ADR in a public repository
  is still `docs-review`'s.
- **`publish`:** removes the agent files (PD17) when the public copy is made.
  This skill only checks that none is there.

## When writing

1. **Name the kind first (PD1).** Before writing a page, say which kind it is:
   a tutorial, a how-to guide, reference or an explanation. If it is two
   kinds, make two pages.
2. **Docstrings (PD2, PD4–PD7).** Start with a one-line summary in the
   imperative mood. Then add `Args:`, `Returns:`, `Raises:`, `Shape:` for
   tensors, and `Example:`. Use `r"""` wherever there is a backslash. Run
   every example before you write its output into the docstring, then copy the
   output exactly. Never write output you did not see.
3. **How-to code (PD8).** Put the code in `docs_src/<topic>.py` and include it
   with `literalinclude`. Add what it prints to `EXPECTED` in
   `tests/functional/test_docs_src.py`; the test refuses a script without
   an entry.
4. **Changes (PD10).** Add `versionadded` or `versionchanged` with the version
   in `pyproject.toml`'s next release. A deprecation names the reason, the
   replacement, the version that deprecates it and the version that removes
   it, at least two releases later. It also raises a `FutureWarning` in code.
5. **Frontmatter (PD16).** Public pages carry `title` and `description` only.

## When reviewing

Run these first, and report their exact output:

```bash
make lint            # PD2, PD4, PD6: Ruff D rules, line length
make test            # PD7, PD8: doctests and docs_src scripts
make docs            # PD11: -W -n, so any warning fails
make docs-coverage   # PD3: every public symbol in the reference
```

`make docs-linkcheck` (PD12) needs the network. Run it when you have network
access. If you don't, say it was not run.

Then read for what no tool checks: the page's kind (PD1), shapes (PD5), the
style (PD15) and both versions on a deprecation (PD10).

Report each finding with:

- its rule number;
- the file and line;
- what a reader would get wrong because of it.

## Refusals

Do not mark docs work done, and say which rule stops it, when:

- a public symbol has no docstring (PD2) or is missing from the reference
  (PD3);
- an example's output was not produced by running it (PD7);
- a deprecation is missing a version (PD10);
- `make docs` has a warning (PD11);
- an agent file is in a repository that is, or is about to become, public
  (PD17).

Never silence a warning, add to `nitpick_ignore`, or add a symbol to the
coverage ignore list to get a build through. Each of those needs the owner's
recorded yes and a reason written next to it.
