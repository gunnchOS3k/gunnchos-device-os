"""Full-ecosystem topology helpers for gunnchctl ecosystem (honest scaffold depth)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.device_lab.profiles import list_profiles, load_profile

MEMBER_PROFILES = (
    "student_14_5",
    "dsxl_coder",
    "handheld_hybrid",
    "handheld_docked",
    "dock",
    "edge_io_rings",
)


def ecosystem_topology() -> dict[str, Any]:
    """Return member-device topology for full_ecosystem — not a simultaneous soak."""
    members: list[dict[str, Any]] = []
    for pid in MEMBER_PROFILES:
        if pid not in list_profiles():
            members.append({"profile_id": pid, "present": False})
            continue
        p = load_profile(pid)
        members.append(
            {
                "profile_id": pid,
                "present": True,
                "product": p.get("product"),
                "ram_gb": (p.get("ram") or {}).get("gb"),
                "compute_mpn": (p.get("compute") or {}).get("mpn")
                or (p.get("exact_mpns") or {}).get("compute"),
            }
        )
    return {
        "ok": all(m.get("present") for m in members),
        "schema": "gunnchos.device_lab.ecosystem_topology.v1",
        "aggregate_profile": "full_ecosystem",
        "members": members,
        "simultaneous_soak": False,
        "ECO_001_depth": "smoke_topology_only",
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        "SILICON_EXACT_EMULATION": False,
        "note": (
            "Topology listing only — ECO-001 smoke does not claim multi-device "
            "simultaneous execution or LAB-FUTURE-003 soak."
        ),
    }
