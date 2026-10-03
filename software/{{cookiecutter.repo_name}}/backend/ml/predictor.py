"""Serve the model inside the web process: loaded once, run without gradients.

No weights, no predictions: a missing or unreadable weights file is an
error, never an untrained model answering in its place. The device is the
one asked for or an error (``device``), and PyTorch's threads are held to a
budget (``threads``), since every web worker would otherwise take every CPU.
"""

from pathlib import Path

import torch

from ml.device import resolve_device
from ml.model import Scorer
from ml.threads import apply_thread_budget


class ModelUnavailableError(RuntimeError):
    """No weights are configured, or the file is not there."""


class Predictor:
    """A model in evaluation mode on one device."""

    def __init__(self, model: Scorer, device: torch.device) -> None:
        """Move ``model`` to ``device`` and put it in evaluation mode."""
        self.device = device
        self.model = model.to(device).eval()

    @classmethod
    def load(cls, weights: str, device: str, threads: int) -> "Predictor":
        """Load weights saved with ``torch.save(model.state_dict(), path)``.

        Args:
            weights: Path to the weights file.
            device: The device to serve on, such as ``"cpu"``.
            threads: PyTorch threads for this process, at least 1.

        Returns:
            A predictor holding the loaded model.

        Raises:
            ModelUnavailableError: If ``weights`` is empty or not a file.
            DeviceUnavailableError: If the device is not on this machine.
            CpuBudgetError: If ``threads`` exceeds this process's CPUs.
        """
        if not weights:
            raise ModelUnavailableError(
                "ML_WEIGHTS names no weights file, and an untrained model "
                "is not served"
            )
        path = Path(weights)
        if not path.is_file():
            raise ModelUnavailableError(f"ML_WEIGHTS={weights} is not a file")
        apply_thread_budget(threads, 0)
        resolved = resolve_device(device)
        model = Scorer()
        model.load_state_dict(
            torch.load(path, map_location=resolved, weights_only=True)
        )
        return cls(model, resolved)

    def predict(self, rows: list[list[float]]) -> list[float]:
        """Score each row.

        Args:
            rows: Rows of :data:`ml.model.FEATURES` values each.

        Returns:
            One score per row, in order.
        """
        with torch.inference_mode():
            batch = torch.tensor(rows, dtype=torch.float32, device=self.device)
            return [float(score) for score in self.model(batch).cpu()]
