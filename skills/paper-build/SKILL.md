---
name: paper-build
description: Build a foundry-generated paper - fetch the venue kit, make pdf, make check, and the arXiv copy - and explain each refusal. Use when building or checking a paper, before sharing a draft, before an arXiv upload, or when asked to "build the paper", "check the paper" or "make the arXiv version".
---

# Paper build

The targets are the paper template's own; each has a one-line description
after `##` in its `Makefile`. Foundry's ADR 0009
(`docs/adr/0009-paper-and-workspace-layout.md`) records the layout and build
choices. Overleaf is the paper's main source, so this skill never rewrites a
file Overleaf may also have edited.

## Steps

1. **`make install`** once, for the text checks.
2. **`make venue`**, for a venue that has a kit. It fetches the style files
   into `venue/`. Commit `venue/` so Overleaf has it. For ICML, it fetches
   the kit for `venue_year` from ICML's site and refuses, leaving no partial
   `venue/icml<year>/`, when that year's kit is not published or does not
   unpack. When ICML support was added on 2026-10-08, the latest published
   kit was 2026 (`docs/templates/paper.md`). Never rename one year's kit as
   another's. Set `venue_year` to a published year and draft against it:

   ```bash
   cruft update --variables-to-update '{"venue_year": "2026"}'
   ```

3. **`make pdf`** builds `build/paper.pdf` with latexmk. An undefined
   reference or citation fails it.
4. **`make check`** builds, then refuses overfull lines and ChkTeX warnings
   in the paper's own files. Fix an overfull line by rewriting it. Never
   shrink the font or the spacing.
5. **`make ci`** is what CI runs: the text checks and `make check`.
6. **For arXiv: `make arxiv`**, then **`make arxiv-verify`**. The first
   writes a cleaned copy to `build/arxiv`; the second compiles that copy on
   its own, as arXiv does.

Without TeX on the machine, use the `-container` targets
(`make ci-container`, `make arxiv-container`). They run the pinned TeX Live
image.

## Numbers and citations

- Every number in the text is `\rnum{label}` from `generated/numbers.tex`,
  never a typed literal. The project's own tooling generates it from verified
  results (ADR 0009).
- The bibliography is `references.bib` (ADR 0009).

## Refusals

Do not call the paper ready, and say which step stopped it, when `make check`
or `make arxiv-verify` fails. Report the exact lines from `build/paper.log`.

When `make venue` refuses because the year's kit is not published, report its
message. Do not fetch a kit from anywhere else.
