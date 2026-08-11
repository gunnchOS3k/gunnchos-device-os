"""Scenario catalog and Golden Journey mapping."""
from __future__ import annotations

SCENARIO_CATALOG = [
    "dock_attach",
    "dock_detach",
    "display_disconnect",
    "display_reconnect",
    "bad_wifi",
    "offline",
    "packet_loss",
    "network_restore",
    "low_storage",
    "removable_storage_remove",
    "ring_low_confidence",
    "ring_wrong_target",
    "ring_packet_loss",
    "ring_drift_simulated",
    "ai_cloud_denied",
    "ai_model_unavailable",
    "app_crash",
    "update_failure",
    # Journey scenarios
    "LAB-SCENARIO-OFFICE-DOCK",
    "LAB-SCENARIO-DSXL-DUALSCREEN",
    "LAB-SCENARIO-RING-REAL-INPUT",
    "LAB-SCENARIO-LOCAL-AI-TUTOR",
    "LAB-SCENARIO-STUDENT-DAY",
    "LAB-SCENARIO-HANDHELD-PLAY-DOCK",
    "LAB-SCENARIO-UPDATE-ROLLBACK",
]

JOURNEY_SCENARIO_MAP = {
    "GOLDEN-01": {
        "scenario": "LAB-SCENARIO-STUDENT-DAY",
        "profile": "student_14_5",
    },
    "GOLDEN-04": {
        "scenario": "LAB-SCENARIO-OFFICE-DOCK",
        "profile": "handheld_docked",
    },
    "GOLDEN-05": {
        "scenario": "LAB-SCENARIO-HANDHELD-PLAY-DOCK",
        "profile": "handheld_hybrid",
    },
    "GOLDEN-06": {
        "scenario": "LAB-SCENARIO-DSXL-DUALSCREEN",
        "profile": "dsxl_coder",
    },
    "GOLDEN-07": {
        "scenario": "LAB-SCENARIO-RING-REAL-INPUT",
        "profile": "edge_io_rings",
        "companion_profile": "student_14_5",
    },
    "GOLDEN-08": {
        "scenario": "LAB-SCENARIO-LOCAL-AI-TUTOR",
        "profile": "student_14_5",
    },
    "GOLDEN-09": {
        "scenario": "LAB-SCENARIO-UPDATE-ROLLBACK",
        "profile": "student_14_5",
    },
}
