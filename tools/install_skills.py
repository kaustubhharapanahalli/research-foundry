"""Compatibility entry point for the packaged skill installer.

Examples:
    >>> callable(main)
    True
"""

# This wrapper intentionally re-exports the package's complete public surface.
# pylint: disable=duplicate-code

import sys

from research_foundry.skills import (
    MANIFEST,
    MODES,
    SKILLS,
    Report,
    destination,
    main,
    run,
)

__all__ = [
    "MANIFEST",
    "MODES",
    "Report",
    "SKILLS",
    "destination",
    "main",
    "run",
]

if __name__ == "__main__":
    sys.exit(main())
