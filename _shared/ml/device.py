"""Resolve the device a run asked for, or refuse. Never fall back."""

import os

import torch


class DeviceUnavailableError(RuntimeError):
    """The requested device does not exist on this machine."""


_KNOWN = ("cpu", "cuda", "mps")


def resolve_device(requested: str) -> torch.device:
    """Return the requested device, or raise if this machine lacks it.

    A run that silently moves to another device produces a result nobody
    asked for, so every missing device is an error.

    Args:
        requested: A device string such as ``"cpu"``, ``"cuda:1"`` or
            ``"mps"``.

    Returns:
        The device, checked against this machine.

    Raises:
        ValueError: If the device type is not cpu, cuda or mps.
        DeviceUnavailableError: If the device is missing, or if
            ``PYTORCH_ENABLE_MPS_FALLBACK=1`` would move unsupported MPS
            operations to the CPU without saying so.

    Example:
        >>> resolve_device("cpu")
        device(type='cpu')
    """
    device = torch.device(requested)
    if device.type not in _KNOWN:
        raise ValueError(f"unsupported device type {device.type!r}")
    if os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1":
        raise DeviceUnavailableError(
            "PYTORCH_ENABLE_MPS_FALLBACK=1 silently runs unsupported MPS "
            "operations on the CPU; unset it"
        )
    if device.type == "cuda":
        count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        index = device.index or 0
        if index >= count:
            raise DeviceUnavailableError(
                f"{requested} requested, but this machine has {count} "
                "CUDA device(s)"
            )
    if device.type == "mps" and not torch.backends.mps.is_available():
        raise DeviceUnavailableError(f"{requested} requested, but MPS is off")
    return device
