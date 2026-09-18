"""Printer/IPP capability detection (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import shutil


@dataclass
class PeripheralCapabilityInventory:
    device_profile: str
    ipp_detect: bool = False
    scanner_detect: bool = False
    cups_pdf_virtual: bool = False
    peripherals: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "device_profile": self.device_profile,
            "ipp_detect": self.ipp_detect,
            "scanner_detect": self.scanner_detect,
            "cups_pdf_virtual": self.cups_pdf_virtual,
            "peripherals": self.peripherals,
            "notes": self.notes,
            "claim_boundary": "detection_scaffold_not_physical_print_pass",
        }


def detect_print_capabilities(device_profile: str = "office_dock") -> PeripheralCapabilityInventory:
    """Detect local print tooling presence without claiming IPP works."""
    inv = PeripheralCapabilityInventory(device_profile=device_profile)
    lpstat = shutil.which("lpstat")
    ipptool = shutil.which("ipptool")
    if lpstat:
        inv.peripherals.append({"type": "cups_client", "binary": lpstat, "available": True})
        inv.notes.append("cups_client_binary_present")
    if ipptool:
        inv.ipp_detect = True
        inv.peripherals.append({"type": "ipp_tool", "binary": ipptool, "available": True})
        inv.notes.append("ipptool_present_not_validated_against_printer")
    else:
        inv.notes.append("ipptool_absent")
    inv.cups_pdf_virtual = True
    inv.notes.append("cups_pdf_virtual_path_known_from_cont_ix")
    inv.scanner_detect = False
    inv.notes.append("sane_scanner_not_implemented")
    return inv
