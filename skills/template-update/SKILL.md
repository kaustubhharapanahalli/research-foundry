---
name: template-update
description: Bring a project generated from foundry up to a newer foundry release with cruft - check, update, resolve the .rej files, run the project's own CI and record the change. Use when make template-check reports the project is behind, when a foundry release changes a shared standard, or when asked to "update from the template" or "pull the template changes".
---

# Template update

foundry's ADR 0001 (`docs/adr/0001-cookiecutter-cruft-shared-base.md`) says
why projects are made with cruft and how a shared change reaches them. The
same ADR holds the versioning rules. This skill applies them to one project
at a time.

## Steps

1. **Start clean.** `cruft update` refuses a working tree with changes.
   Commit or set aside the project's own work first.
2. **See how far behind it is.** Run `make template-check` and report its
   output. It reads foundry over the network.
3. **Update to a release, not to a branch head:**

   ```bash
   uvx --from cruft==2.16.0 cruft update --skip-apply-ask --checkout <tag>
   ```

   A paper repository has one branch, because Overleaf's git bridge has
   none, so the update is applied on it directly.

4. **Resolve every `.rej` file.** Each is a hunk cruft could not apply. Apply
   it by hand where the project's own edit and the template's change can both
   stand. Where they conflict, keep the project's edit only with a reason in
   the commit message. Then delete the `.rej` file. Never commit one.
5. **Run `make install` and `make ci`.** Report their exact output. A new
   standard can fail code that passed before; fix the code, not the check.
6. **Commit the update on its own**, with the foundry version in the message
   and one line per change the project felt.

## Refusals

Do not finish the update, and say why, when:

- a `.rej` file is left;
- `make ci` fails;
- the update would remove a test or weaken a check the project relies on.
  That needs the owner's recorded yes.
