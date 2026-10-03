"""The example model: one score per row of features.

Replace it with the project's own network. Keep it an ``nn.Module`` whose
weights are saved as a ``state_dict``: ``torch.load`` reads those with
``weights_only=True``, which refuses anything but tensors and plain values.
"""

import torch
from torch import Tensor, nn

#: How many features each row has.
FEATURES = 4


class Scorer(nn.Module):
    """Map each row of :data:`FEATURES` values to a score between 0 and 1."""

    def __init__(self, features: int = FEATURES) -> None:
        """Start with random weights for ``features`` inputs."""
        super().__init__()
        self.linear = nn.Linear(features, 1)

    def forward(self, rows: Tensor) -> Tensor:
        """Return one score per row.

        Args:
            rows: A ``(batch, features)`` tensor.

        Returns:
            A ``(batch,)`` tensor of scores in (0, 1).
        """
        scores: Tensor = torch.sigmoid(self.linear(rows)).squeeze(-1)
        return scores
