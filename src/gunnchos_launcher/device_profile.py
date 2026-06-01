"""Device profiles for gunnchOS launcher (synthetic / research prototype)."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

DeviceId = Literal["student_14_5", "handheld_hybrid", "ds_xl_coder", "arena_wearables"]
ModeId = Literal["school", "developer", "play", "research_measurement", "fleet_admin"]

DEVICES: list[DeviceId] = ["student_14_5", "handheld_hybrid", "ds_xl_coder", "arena_wearables"]
MODES: list[ModeId] = ["school", "developer", "play", "research_measurement", "fleet_admin"]

TIER_MAP: dict[DeviceId, str] = {
    "student_14_5": "community_baseline",
    "handheld_hybrid": "community_baseline",
    "ds_xl_coder": "research_lab",
    "arena_wearables": "research_lab",
}


@dataclass
class DeviceProfile:
    device: DeviceId
    mode: ModeId
    tier: str
    offline_ready: bool = True
    wifi_generation: str = "Wi-Fi 6E/7"
    urllc_measurement_capable: bool = True
    edge_ai_capable: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def get_profile(device: str, mode: str) -> dict:
    if device not in DEVICES:
        raise ValueError(f"Unknown device: {device}")
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    return DeviceProfile(
        device=device,  # type: ignore
        mode=mode,  # type: ignore
        tier=TIER_MAP.get(device, "community_baseline"),  # type: ignore
    ).to_dict()


def list_devices() -> list[str]:
    return list(DEVICES)


def list_modes() -> list[str]:
    return list(MODES)
