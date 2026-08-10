"""Compatibility runtime lane registry."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class RuntimeLane(str, Enum):
    GUNNCH_NATIVE = "GUNNCH_NATIVE"
    LINUX_NATIVE = "LINUX_NATIVE"
    FLATPAK = "FLATPAK"
    WEB_PWA = "WEB_PWA"
    OCI_DEV = "OCI_DEV"
    STEAM_PROTON_USER = "STEAM_PROTON_USER"
    ANDROID_EXPERIMENTAL = "ANDROID_EXPERIMENTAL"


@dataclass
class LaneRecord:
    lane: RuntimeLane
    enabled: bool
    evaluated: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["lane"] = self.lane.value
        return d


DEFAULT_LANES: dict[RuntimeLane, LaneRecord] = {
    RuntimeLane.GUNNCH_NATIVE: LaneRecord(
        RuntimeLane.GUNNCH_NATIVE, True, True, "First-party gunnch packages"
    ),
    RuntimeLane.LINUX_NATIVE: LaneRecord(
        RuntimeLane.LINUX_NATIVE, True, True, "Distro native ELF/desktop apps"
    ),
    RuntimeLane.FLATPAK: LaneRecord(
        RuntimeLane.FLATPAK, True, True, "Flatpak when host tool present"
    ),
    RuntimeLane.WEB_PWA: LaneRecord(
        RuntimeLane.WEB_PWA, True, True, "Browser / PWA surface"
    ),
    RuntimeLane.OCI_DEV: LaneRecord(
        RuntimeLane.OCI_DEV, True, True, "OCI containers for developer mode"
    ),
    RuntimeLane.STEAM_PROTON_USER: LaneRecord(
        RuntimeLane.STEAM_PROTON_USER,
        True,
        True,
        "Steam is user-external; Proton harness for redistributable test apps only",
    ),
    RuntimeLane.ANDROID_EXPERIMENTAL: LaneRecord(
        RuntimeLane.ANDROID_EXPERIMENTAL,
        False,
        False,
        "Evaluate-only; evaluated=false by default",
    ),
}


class CompatRegistry:
    def __init__(self) -> None:
        self.lanes = {k: LaneRecord(**asdict(v)) for k, v in DEFAULT_LANES.items()}
        # fix enum after asdict
        for k, v in list(self.lanes.items()):
            self.lanes[k] = LaneRecord(
                lane=k,
                enabled=DEFAULT_LANES[k].enabled,
                evaluated=DEFAULT_LANES[k].evaluated,
                notes=DEFAULT_LANES[k].notes,
            )

    def get(self, lane: RuntimeLane) -> LaneRecord:
        return self.lanes[lane]

    def list_lanes(self) -> list[dict[str, Any]]:
        return [self.lanes[k].to_dict() for k in RuntimeLane]

    def set_evaluated(self, lane: RuntimeLane, evaluated: bool) -> LaneRecord:
        rec = self.lanes[lane]
        self.lanes[lane] = LaneRecord(rec.lane, rec.enabled, evaluated, rec.notes)
        return self.lanes[lane]
