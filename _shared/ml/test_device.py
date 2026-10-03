import pytest
import torch

from {{ ml_package }}.device import (
    DeviceUnavailableError,
    resolve_device,
)


def test_cpu_resolves() -> None:
    assert resolve_device("cpu") == torch.device("cpu")


def test_unknown_device_type_is_refused() -> None:
    with pytest.raises(ValueError, match="unsupported device type"):
        resolve_device("meta")


def test_missing_cuda_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(DeviceUnavailableError, match="0 CUDA device"):
        resolve_device("cuda")


def test_cuda_index_beyond_the_machine_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    with pytest.raises(DeviceUnavailableError, match="cuda:1 requested"):
        resolve_device("cuda:1")


def test_present_cuda_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 2)
    assert resolve_device("cuda:1") == torch.device("cuda:1")


def test_missing_mps_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    with pytest.raises(DeviceUnavailableError, match="MPS is off"):
        resolve_device("mps")


def test_mps_fallback_switch_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    with pytest.raises(DeviceUnavailableError, match="FALLBACK"):
        resolve_device("cpu")


@pytest.mark.gpu
def test_this_machine_has_its_gpu() -> None:
    # The smoke test before a real run: the GPU this machine is meant to
    # have is there and usable.
    kind = "cuda" if torch.cuda.is_available() else "mps"
    device = resolve_device(kind)
    assert torch.ones(2, device=device).sum().item() == 2
