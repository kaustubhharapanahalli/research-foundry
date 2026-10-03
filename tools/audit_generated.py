"""Generate, lock, and audit every heavy-test project variant.

Examples:
--------
Run the generated-project audit from the repository root::

    uv run python -m tools.audit_generated
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from tools import audit
from tools.throwaway import ROOT, generate
from tools.variants import VARIANTS


def main() -> int:
    """Generate and lock each named heavy variant, then audit every lock.

    Returns:
    -------
    int
        Non-zero if generation, locking, or auditing fails.
    """
    prefix = "foundry-audit-generated-"
    with tempfile.TemporaryDirectory(prefix=prefix) as name:
        temporary = Path(name)
        generated = temporary / "generated"
        for variant, (template, answers) in sorted(VARIANTS.items()):
            project = generate(
                template,
                answers,
                into=generated / variant,
                source=ROOT,
            )
            print(f"Locking {variant}: {project}")
            locked = subprocess.run(["uv", "lock"], cwd=project, check=False)
            if locked.returncode:
                return locked.returncode
        return audit.main(
            [
                "--root",
                str(ROOT),
                "--generated",
                str(generated),
                "--report",
                str(ROOT / "build" / "audit-report.md"),
            ]
        )


if __name__ == "__main__":
    sys.exit(main())
