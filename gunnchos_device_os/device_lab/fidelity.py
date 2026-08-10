"""Fidelity levels VF0–VF6 and honesty dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class FidelityLevel(str, Enum):
    VF0_VISUAL = "VF0"
    VF1_SOFTWARE = "VF1"
    VF2_PERIPHERAL = "VF2"
    VF3_MODELED = "VF3"
    VF4_CALIBRATED = "VF4"
    VF5_HIL = "VF5"
    VF6_PHYSICAL = "VF6"


class HonestyStatus(str, Enum):
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    VIRTUAL = "VIRTUAL"
    SIMULATED = "SIMULATED"
    MODELED = "MODELED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    PHYSICAL_PENDING = "PHYSICAL_PENDING"
    NOT_YET_CALIBRATED = "NOT_YET_CALIBRATED"


@dataclass
class SubsystemFidelity:
    name: str
    level: FidelityLevel
    status: HonestyStatus
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level.value,
            "status": self.status.value,
            "notes": self.notes,
        }


@dataclass
class FidelityDashboard:
    """Machine-readable + UI-facing honesty panel for a Lab run."""

    software: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "SOFTWARE_FIDELITY", FidelityLevel.VF1_SOFTWARE, HonestyStatus.HIGH,
            "Real gunnchOS APIs/services under BEHAVIORAL_DEVICE_PROFILE",
        )
    )
    ui: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "UI_FIDELITY", FidelityLevel.VF1_SOFTWARE, HonestyStatus.HIGH,
        )
    )
    workflow: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "WORKFLOW_FIDELITY", FidelityLevel.VF1_SOFTWARE, HonestyStatus.PARTIAL,
            "E4/D6 only when independently earned",
        )
    )
    storage: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "STORAGE_FIDELITY", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.VIRTUAL,
        )
    )
    network: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "NETWORK_POLICY", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.SIMULATED,
        )
    )
    display: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "DISPLAY", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.VIRTUAL,
        )
    )
    dock: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "DOCK", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.VIRTUAL,
            "Virtual peripheral lifecycle; not physical SI",
        )
    )
    audio: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "AUDIO", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.VIRTUAL,
        )
    )
    rings: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "RING_SPATIAL_ACCURACY", FidelityLevel.VF2_PERIPHERAL, HonestyStatus.SIMULATED,
        )
    )
    cpu: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "CPU_PERFORMANCE", FidelityLevel.VF3_MODELED, HonestyStatus.MODELED,
        )
    )
    gpu: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "GPU_PERFORMANCE", FidelityLevel.VF3_MODELED, HonestyStatus.MODELED,
        )
    )
    npu: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "NPU_PERFORMANCE", FidelityLevel.VF3_MODELED, HonestyStatus.MODELED,
        )
    )
    battery: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "BATTERY", FidelityLevel.VF3_MODELED, HonestyStatus.MODELED,
        )
    )
    thermal: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "THERMAL", FidelityLevel.VF3_MODELED, HonestyStatus.MODELED,
        )
    )
    rf: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "RF", FidelityLevel.VF3_MODELED, HonestyStatus.SIMULATED,
        )
    )
    physical_correlation: SubsystemFidelity = field(
        default_factory=lambda: SubsystemFidelity(
            "PHYSICAL_CORRELATION", FidelityLevel.VF6_PHYSICAL,
            HonestyStatus.NOT_YET_CALIBRATED,
            "VF4/VF5/VF6 PHYSICAL_PENDING until EVT",
        )
    )
    vf0_physical_twin: HonestyStatus = HonestyStatus.PARTIAL
    silicon_exact_emulation: bool = False
    behavioral_device_profile: bool = True

    def to_dict(self) -> dict[str, Any]:
        subs = [
            self.software, self.ui, self.workflow, self.storage, self.network,
            self.display, self.dock, self.audio, self.rings, self.cpu, self.gpu,
            self.npu, self.battery, self.thermal, self.rf, self.physical_correlation,
        ]
        return {
            "schema": "gunnchos.device_lab.fidelity_dashboard.v1",
            "subsystems": [s.to_dict() for s in subs],
            "VF0_PHYSICAL_TWIN": self.vf0_physical_twin.value,
            "SILICON_EXACT_EMULATION": self.silicon_exact_emulation,
            "BEHAVIORAL_DEVICE_PROFILE": self.behavioral_device_profile,
            "VF4": "PHYSICAL_PENDING",
            "VF5": "PHYSICAL_PENDING",
            "VF6": "PHYSICAL_PENDING",
        }

    def assert_honest(self) -> list[str]:
        """Return list of honesty violations (empty = ok)."""
        violations: list[str] = []
        for s in (self.cpu, self.gpu, self.npu, self.battery, self.thermal):
            if s.status == HonestyStatus.VERIFIED and s.level == FidelityLevel.VF3_MODELED:
                violations.append(f"{s.name}: modeled labeled as verified")
            if s.status.value == "PHYSICAL_MEASURED" or "PHYSICAL_MEASURED" in s.notes:
                violations.append(f"{s.name}: modeled labeled physical")
        if self.physical_correlation.status not in {
            HonestyStatus.NOT_YET_CALIBRATED, HonestyStatus.PHYSICAL_PENDING, HonestyStatus.UNAVAILABLE
        }:
            if self.physical_correlation.status == HonestyStatus.VERIFIED:
                violations.append("physical_correlation claimed verified without EVT")
        if self.silicon_exact_emulation:
            violations.append("SILICON_EXACT_EMULATION must be false in v0.1")
        return violations
