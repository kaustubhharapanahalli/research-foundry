# lib/domain

Rules of the application's domain that two or more features share, as pure
functions: no React, no `fetch`, no DOM. A rule only one feature uses lives
in that feature's `model/` folder instead.

Tested in `tests/unit/lib/domain/`.
