"""Boot failure injection modes for Gate 1 software-path tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FailureMode(str, Enum):
    NONE = "none"
    MISSING_SERVICE = "missing_service"
    CORRUPTED_MANIFEST = "corrupted_manifest"
    STALE_IMAGE = "stale_image"
    UNSUPPORTED_ARCH = "unsupported_arch"
    FAILED_HEALTH_CHECK = "failed_health_check"


@dataclass
class InjectedFailure:
    label: str | None
    missing_services: set[str] = field(default_factory=set)
    failed_health_checks: set[str] = field(default_factory=set)
    corrupt_manifest: bool = False
    stale_image: bool = False
    unsupported_arch: bool = False


def apply_failure(mode: FailureMode | str | None) -> InjectedFailure:
    if mode is None or mode == "" or mode == FailureMode.NONE or mode == "none":
        return InjectedFailure(label=None)
    if isinstance(mode, str):
        mode = FailureMode(mode)
    if mode is FailureMode.MISSING_SERVICE:
        return InjectedFailure(label=mode.value, missing_services={"display-manager"})
    if mode is FailureMode.CORRUPTED_MANIFEST:
        return InjectedFailure(label=mode.value, corrupt_manifest=True)
    if mode is FailureMode.STALE_IMAGE:
        return InjectedFailure(label=mode.value, stale_image=True)
    if mode is FailureMode.UNSUPPORTED_ARCH:
        return InjectedFailure(label=mode.value, unsupported_arch=True)
    if mode is FailureMode.FAILED_HEALTH_CHECK:
        return InjectedFailure(
            label=mode.value, failed_health_checks={"networkd"}
        )
    raise ValueError(f"unknown failure mode: {mode}")
