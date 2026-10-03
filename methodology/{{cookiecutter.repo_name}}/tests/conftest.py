"""Markers by folder{% if cookiecutter.ml_pytorch == "yes" %}, and PyTorch state restored after every test{% endif %}."""

{% if cookiecutter.ml_pytorch == "yes" %}from collections.abc import Iterator
{% endif %}from pathlib import Path

import pytest
{%- if cookiecutter.ml_pytorch == "yes" %}
import torch
{%- endif %}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests unit or functional from their folder; doctests are unit."""
    for item in items:
        parts = Path(str(item.path)).parts
        if "functional" in parts:
            item.add_marker(pytest.mark.functional)
        else:
            item.add_marker(pytest.mark.unit)
{%- if cookiecutter.ml_pytorch == "yes" %}


@pytest.fixture(autouse=True)
def _restore_torch_state() -> Iterator[None]:
    # seed_everything changes process-wide settings; one test's
    # deterministic mode must not leak into the next.
    deterministic = torch.are_deterministic_algorithms_enabled()
    threads = torch.get_num_threads()
    yield
    torch.use_deterministic_algorithms(deterministic)
    torch.set_num_threads(threads)
{%- endif %}
