"""Hardware profile dataclasses for compatibility layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DisplayCapabilities:
    size_inches: float | None = None
    resolution: str = ""
    external_display: bool = False
    touch: bool = False


@dataclass
class InputCapabilities:
    keyboard: bool = False
    touch: bool = False
    controller: bool = False
    stylus: bool = False
    voice_placeholder: bool = False


@dataclass
class PowerCapabilities:
    battery_class: str = ""
    school_day_target: bool = False


@dataclass
class ThermalCapabilities:
    thermal_class: str = ""
    throttle_policy: str = ""


@dataclass
class StorageCapabilities:
    storage_class: str = ""
    min_gb: int = 0


@dataclass
class NetworkCapabilities:
    wifi: str = ""
    offline_capable: bool = True
    ethernet_dock_optional: bool = False
    cellular: str = ""  # generic class tag only (e.g. simulated_generic)
    ntn: str = ""  # none | simulated


@dataclass
class DockCapabilities:
    supported: bool = False
    usb_c_dp_alt_mode: bool = False


@dataclass
class AccessibilityCapabilities:
    screen_reader_labels: bool = True
    controller_navigation: bool = False
    high_contrast: bool = False


@dataclass
class DeviceProfile:
    device_id: str
    display_name: str = ""
    display: DisplayCapabilities = field(default_factory=DisplayCapabilities)
    input: InputCapabilities = field(default_factory=InputCapabilities)
    power: PowerCapabilities = field(default_factory=PowerCapabilities)
    thermal: ThermalCapabilities = field(default_factory=ThermalCapabilities)
    storage: StorageCapabilities = field(default_factory=StorageCapabilities)
    memory_gb: int = 0
    network: NetworkCapabilities = field(default_factory=NetworkCapabilities)
    dock: DockCapabilities = field(default_factory=DockCapabilities)
    accessibility: AccessibilityCapabilities = field(default_factory=AccessibilityCapabilities)
    supported_modes: list[str] = field(default_factory=list)
    supported_journey_presets: list[str] = field(default_factory=list)
    supported_app_packs: list[str] = field(default_factory=list)
    known_gaps: list[str] = field(default_factory=list)
    hardware_repo_source_paths: list[str] = field(default_factory=list)
    claim_boundary: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompatibilityResult:
    compatible: bool
    status: str  # pass|warn|fail
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    recommended_fallbacks: list[str] = field(default_factory=list)
    hardware_assumptions: list[str] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)
    user_message: str = ""
    technical_log: str = ""
