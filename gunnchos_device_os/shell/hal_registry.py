"""HAL capability registry with provenance labels (Wave 002 / OS-PLATFORM-002)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from gunnchos_device_os.dock.capabilities import load_capabilities


class CapabilityProvenance(str, Enum):
    REAL_DEVICE_OBSERVED = "REAL_DEVICE_OBSERVED"
    HOST_OBSERVED = "HOST_OBSERVED"
    EMULATED = "EMULATED"
    MODELED = "MODELED"
    UNAVAILABLE = "UNAVAILABLE"


CLAIM_BOUNDARY = (
    "Software HAL registry with explicit provenance. Not firmware drivers, "
    "not silicon-verified hardware abstraction."
)


DEFAULT_CAPABILITIES: list[dict[str, Any]] = [
    {
        "id": "display.internal",
        "category": "display",
        "provenance": CapabilityProvenance.MODELED.value,
        "notes": "Layout profiles from display_manager",
    },
    {
        "id": "display.external_dock",
        "category": "display",
        "provenance": CapabilityProvenance.EMULATED.value,
        "notes": "Dock hotplug simulated; DS-XL guest evidence linked when present",
    },
    {
        "id": "input.touch",
        "category": "input",
        "provenance": CapabilityProvenance.MODELED.value,
    },
    {
        "id": "input.gamepad",
        "category": "input",
        "provenance": CapabilityProvenance.MODELED.value,
    },
    {
        "id": "input.keyboard_mouse",
        "category": "input",
        "provenance": CapabilityProvenance.HOST_OBSERVED.value,
        "notes": "Dev host keyboard/mouse during lab sessions",
    },
    {
        "id": "input.ring",
        "category": "input",
        "provenance": CapabilityProvenance.EMULATED.value,
        "notes": "Authenticated ring protocol; PHYSICAL_RING_CLAIMED=false",
    },
    {
        "id": "identity.local_store",
        "category": "identity",
        "provenance": CapabilityProvenance.HOST_OBSERVED.value,
    },
    {
        "id": "continuity.local_checkpoint",
        "category": "continuity",
        "provenance": CapabilityProvenance.MODELED.value,
    },
    {
        "id": "pixel.adb_client",
        "category": "connectivity",
        "provenance": CapabilityProvenance.UNAVAILABLE.value,
        "notes": "Populated at runtime when adb authorized",
    },
]


@dataclass
class HalCapabilityRegistry:
    capabilities: dict[str, dict[str, Any]] = field(default_factory=dict)
    dock_descriptors: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            for row in DEFAULT_CAPABILITIES:
                cap_id = row["id"]
                kwargs = {k: v for k, v in row.items() if k != "id"}
                self.register(cap_id, **kwargs)
        if not self.dock_descriptors:
            self.dock_descriptors = load_capabilities()

    def register(
        self,
        capability_id: str,
        *,
        category: str = "general",
        provenance: str | CapabilityProvenance = CapabilityProvenance.MODELED,
        notes: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prov = provenance.value if isinstance(provenance, CapabilityProvenance) else provenance
        if prov not in {p.value for p in CapabilityProvenance}:
            raise ValueError(f"invalid provenance: {prov}")
        row = {
            "id": capability_id,
            "category": category,
            "provenance": prov,
            "notes": notes,
            "metadata": dict(metadata or {}),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.capabilities[capability_id] = row
        return row

    def set_provenance(self, capability_id: str, provenance: CapabilityProvenance) -> dict[str, Any]:
        if capability_id not in self.capabilities:
            raise KeyError(capability_id)
        self.capabilities[capability_id]["provenance"] = provenance.value
        return self.capabilities[capability_id]

    def get(self, capability_id: str) -> dict[str, Any] | None:
        return self.capabilities.get(capability_id)

    def available(self, capability_id: str) -> bool:
        row = self.get(capability_id)
        return row is not None and row["provenance"] != CapabilityProvenance.UNAVAILABLE.value

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        return [dict(v) for v in self.capabilities.values() if v.get("category") == category]

    def status(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for row in self.capabilities.values():
            p = row["provenance"]
            counts[p] = counts.get(p, 0) + 1
        return {
            "total": len(self.capabilities),
            "by_provenance": counts,
            "dock_classes": len(self.dock_descriptors.get("dock_classes", [])),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "capabilities": {k: dict(v) for k, v in self.capabilities.items()},
            "dock_descriptors": dict(self.dock_descriptors),
            "status": self.status(),
        }
