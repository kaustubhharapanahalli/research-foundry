"""Seed twice with the same integer, and draw the same numbers twice.

The "Repeat a run exactly" guide includes this file, and a test runs it.
"""

import torch

from {{ cookiecutter.package_name }}.seeding import seed_everything


def main() -> None:
    """Draw three numbers twice, from the same seed, and compare them."""
    seed_everything(7)
    first = torch.rand(3)
    seed_everything(7)
    second = torch.rand(3)
    print(torch.equal(first, second))


if __name__ == "__main__":
    main()
