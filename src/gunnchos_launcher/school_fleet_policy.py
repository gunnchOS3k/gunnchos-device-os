"""School fleet policy stub."""
from __future__ import annotations


def fleet_status(school_id: str = "gary_demo") -> dict:
    return {
        "school_id": school_id,
        "devices_enrolled": 120,
        "devices_online": 98,
        "policy_version": "fleet-v0-mock",
        "child_safety_defaults": True,
    }
