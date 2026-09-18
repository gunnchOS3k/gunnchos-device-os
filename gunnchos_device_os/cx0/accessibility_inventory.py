"""Accessibility + peripheral capability inventory export (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

DEFAULT_FEATURES = [
    "screen_reader_hook",
    "magnifier",
    "high_contrast",
    "large_text",
    "keyboard_only",
    "captions",
    "reduce_motion",
]


@dataclass
class AccessibilityCapabilityInventory:
    device_profile: str
    features: List[dict] = field(default_factory=list)
    atspi_available: bool = False
    evidence_tier: str = "digital"

    def to_dict(self) -> dict:
        return {
            "device_profile": self.device_profile,
            "features": self.features,
            "atspi_available": self.atspi_available,
            "evidence_tier": self.evidence_tier,
            "claim_boundary": "inventory_scaffold_not_human_a11y_pass",
        }


def export_accessibility_inventory(device_profile: str = "handheld_student") -> AccessibilityCapabilityInventory:
    features = [{"name": n, "supported_digitally": True, "human_verified": False} for n in DEFAULT_FEATURES]
    return AccessibilityCapabilityInventory(
        device_profile=device_profile,
        features=features,
        atspi_available=False,
        evidence_tier="digital",
    )
