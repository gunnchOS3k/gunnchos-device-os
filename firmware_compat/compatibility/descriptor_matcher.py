"""Match firmware descriptor paths to imported hardware repo artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IMPORTED = ROOT / "firmware_compat" / "imported_hardware_contracts"
DESCRIPTORS = IMPORTED / "descriptors"


def match_descriptors(device_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or {}
    sources = manifest.get("descriptor_sources") or {}
    matches: dict[str, Any] = {}
    missing: list[str] = []

    for kind in ("acpi", "devicetree"):
        rel = sources.get(kind) or f"firmware/descriptors/{kind}/{device_id}"
        candidates = [
            DESCRIPTORS / kind / f"{device_id}_dsdt.dsl" if kind == "acpi" else DESCRIPTORS / kind / f"{device_id}.dts",
            IMPORTED / rel,
            ROOT.parent / "gunnchos-hardware-industrial-design" / rel,
        ]
        found = next((p for p in candidates if p.exists()), None)
        if found:
            matches[kind] = {"path": str(found.relative_to(ROOT) if ROOT in found.parents else found), "exists": True}
        else:
            missing.append(kind)
            matches[kind] = {"path": rel, "exists": False}

    status = "pass" if not missing else ("warn" if any(matches[k]["exists"] for k in matches) else "fail")
    return {
        "device_id": device_id,
        "status": status,
        "matches": matches,
        "missing": missing,
        "claim_boundary": "Descriptor stub match — not physical-board validation",
    }
