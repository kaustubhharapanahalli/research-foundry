---
title: Check the install
description: Confirm that the package imports, and print its version.
---

# Check the install

After `make install`, run:

```bash
uv run python docs_src/check_install.py
```

It prints the installed version, such as `0.1.0`. An `ImportError` means
the environment is not installed: run `make install` again.

```{literalinclude} ../../docs_src/check_install.py
:language: python
```
