"""Display manager — layout profiles for Student / DS-XL / Handheld / Dock.

Software service module with simulated backends. Not a Wayland/X11 compositor.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Protocol


class DeviceSurface(str, Enum):
    STUDENT_14_5 = "student_14_5"
    DS_XL_CODER = "ds_xl_coder"
    HANDHELD_HYBRID = "handheld_hybrid"
    DOCK = "dock"


class BackendKind(str, Enum):
    SIMULATED = "simulated"
    # Reserved for future real backends — not claimed here.
    WAYLAND = "wayland"
    X11 = "x11"


LAYOUT_PROFILES: dict[str, dict[str, Any]] = {
    DeviceSurface.STUDENT_14_5.value: {
        "name": "student_14_5",
        "primary": "internal-14.5",
        "displays": ["internal-14.5"],
        "resolution": {"w": 1920, "h": 1200},
        "dpi": 160,
        "scale": 1.25,
        "orientation": "landscape",
        "safe_insets": {"top": 0, "bottom": 0, "left": 0, "right": 0},
        "chrome": "laptop",
    },
    DeviceSurface.DS_XL_CODER.value: {
        "name": "ds_xl_coder",
        "primary": "internal-coder",
        "displays": ["internal-coder"],
        "resolution": {"w": 2560, "h": 1600},
        "dpi": 180,
        "scale": 1.0,
        "orientation": "landscape",
        "safe_insets": {"top": 0, "bottom": 0, "left": 0, "right": 0},
        "chrome": "desktop-coder",
    },
    DeviceSurface.HANDHELD_HYBRID.value: {
        "name": "handheld_hybrid",
        "primary": "internal-handheld",
        "displays": ["internal-handheld"],
        "resolution": {"w": 1280, "h": 800},
        "dpi": 220,
        "scale": 1.5,
        "orientation": "landscape",
        "safe_insets": {"top": 12, "bottom": 24, "left": 8, "right": 8},
        "chrome": "handheld",
    },
    DeviceSurface.DOCK.value: {
        "name": "dock",
        "primary": "external-dock",
        "displays": ["internal-handheld", "external-dock"],
        "resolution": {"w": 3840, "h": 2160},
        "dpi": 140,
        "scale": 1.0,
        "orientation": "landscape",
        "safe_insets": {"top": 0, "bottom": 0, "left": 0, "right": 0},
        "chrome": "docked-extend",
        "mirror": False,
    },
}


class DisplayBackend(Protocol):
    kind: BackendKind

    def apply(self, profile: dict[str, Any]) -> dict[str, Any]:
        ...

    def current(self) -> dict[str, Any]:
        ...


@dataclass
class SimulatedDisplayBackend:
    kind: BackendKind = BackendKind.SIMULATED
    applied: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def apply(self, profile: dict[str, Any]) -> dict[str, Any]:
        self.applied = {
            "backend": self.kind.value,
            "profile": dict(profile),
            "active": True,
        }
        self.history.append(dict(self.applied))
        return dict(self.applied)

    def current(self) -> dict[str, Any]:
        return dict(self.applied) if self.applied else {"backend": self.kind.value, "active": False}


@dataclass
class DisplayManager:
    backend: DisplayBackend = field(default_factory=SimulatedDisplayBackend)
    active_surface: DeviceSurface = DeviceSurface.HANDHELD_HYBRID
    events: list[dict[str, Any]] = field(default_factory=list)

    def list_profiles(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in LAYOUT_PROFILES.items()}

    def get_profile(self, surface: DeviceSurface | str) -> dict[str, Any]:
        key = surface.value if isinstance(surface, DeviceSurface) else surface
        if key not in LAYOUT_PROFILES:
            raise ValueError(f"unknown display surface: {key}")
        return dict(LAYOUT_PROFILES[key])

    def apply_surface(self, surface: DeviceSurface | str) -> dict[str, Any]:
        key = surface.value if isinstance(surface, DeviceSurface) else surface
        profile = self.get_profile(key)
        applied = self.backend.apply(profile)
        self.active_surface = DeviceSurface(key)
        kind = getattr(self.backend, "kind", BackendKind.SIMULATED)
        backend_name = kind.value if isinstance(kind, BackendKind) else str(kind)
        event = {
            "kind": "apply_surface",
            "surface": key,
            "backend": backend_name,
            "profile": profile,
            "applied": applied,
            "mock": False,
            "claim_boundary": "Simulated display backend only; not a compositor.",
        }
        self.events.append(event)
        return event

    def set_docked(self, docked: bool) -> dict[str, Any]:
        if docked:
            return self.apply_surface(DeviceSurface.DOCK)
        # Prefer returning to handheld when undocking; callers can override.
        return self.apply_surface(DeviceSurface.HANDHELD_HYBRID)

    def switch_for_device_class(self, device_class: str) -> dict[str, Any]:
        mapping = {
            "student_14_5": DeviceSurface.STUDENT_14_5,
            "ds_xl_coder": DeviceSurface.DS_XL_CODER,
            "handheld_hybrid": DeviceSurface.HANDHELD_HYBRID,
            "dock": DeviceSurface.DOCK,
        }
        if device_class not in mapping:
            raise ValueError(f"unsupported device class for display manager: {device_class}")
        return self.apply_surface(mapping[device_class])

    def status(self) -> dict[str, Any]:
        return {
            "active_surface": self.active_surface.value,
            "backend": asdict(self.backend) if hasattr(self.backend, "__dataclass_fields__") else self.backend.current(),
            "current": self.backend.current(),
            "profiles": sorted(LAYOUT_PROFILES.keys()),
            "events": list(self.events),
            "mock": False,
        }
