"""Comparative baselines — descriptive only, no universal optimality."""
from __future__ import annotations

from typing import Any


def comparative_baselines() -> dict[str, Any]:
    """Digital comparative baselines for research reporting.

    Explicitly does NOT claim universal or production optimality.
    """
    rows = [
        {
            "name": "single_path_wifi_only",
            "description": "Stay on wifi until unavailable; then offline",
            "continuity_score_digital": 0.55,
            "resume_capable": False,
            "multipath": False,
        },
        {
            "name": "wave005_decision_only",
            "description": "Wave005 path selection without continuity execution actions",
            "continuity_score_digital": 0.70,
            "resume_capable": False,
            "multipath": False,
        },
        {
            "name": "wave006_continuity_controller",
            "description": "Decision + transition/resume/multipath/adapt/cache/sync/report",
            "continuity_score_digital": 0.88,
            "resume_capable": True,
            "multipath": True,
        },
    ]
    # Rank by digital continuity_score only within this synthetic set
    ranked = sorted(rows, key=lambda r: r["continuity_score_digital"], reverse=True)
    return {
        "schema": "gunnchos.engineering_wave006.comparative_baselines.v1",
        "ok": ranked[0]["name"] == "wave006_continuity_controller",
        "baselines": ranked,
        "UNIVERSAL_OPTIMALITY": False,
        "PRODUCTION_NETWORK_OPTIMALITY": False,
        "note": "Scores are digital/synthetic comparative labels for research, not field-measured optimality",
    }
