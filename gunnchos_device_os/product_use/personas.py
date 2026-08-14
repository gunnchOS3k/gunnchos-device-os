"""PRODUCT-USE-RC-001 persona definitions (G11–G15) mapped to Device Lab profiles."""
from __future__ import annotations

from typing import Any

# Labels are evidence classes — never invent silicon precision.
MEASUREMENT_LABELS = (
    "HOST_OBSERVED",
    "GUEST_OBSERVED",
    "VIRTUAL_CONSTRAINED",
    "MODELED_TARGET_RANGE",
)

PERSONAS: dict[str, dict[str, Any]] = {
    "G11": {
        "id": "G11",
        "name": "Student",
        "token": "STUDENT_DIGITAL_PICKUP_AND_USE_READY",
        "profile_id": "student_14_5",
        "terminal_allowed": False,
        "primary_apps": [
            "waike_learning",
            "gunnchai",
            "browser",
            "document",
            "spreadsheet",
            "pdf",
            "game_accepted_main",
        ],
        "waike_role": "learner",
        "network": ["wifi", "offline", "reconnect"],
        "dock": False,
        "ring": True,
        "game_source": "ACCEPTED_MAIN",
        "beatlink_usage": "BRANCH_EVIDENCE_ONLY_UNTIL_MERGE",
        "ai_source": "gunnchai_main",
    },
    "G12": {
        "id": "G12",
        "name": "Office",
        "token": "OFFICE_DIGITAL_PICKUP_AND_USE_READY",
        "profile_id": "dsxl_coder",
        "terminal_allowed": False,
        "primary_apps": [
            "browser",
            "document",
            "spreadsheet",
            "presentation",
            "pdf",
            "files",
            "gunnchai",
            "notes",
        ],
        "waike_role": None,
        "network": ["ethernet_dock", "wifi", "offline", "reconnect"],
        "dock": True,
        "ring": False,
        "game_source": None,
        "ai_source": "gunnchai_main",
    },
    "G13": {
        "id": "G13",
        "name": "Teacher",
        "token": "TEACHER_DIGITAL_PICKUP_AND_USE_READY",
        "profile_id": "student_14_5",
        "terminal_allowed": False,
        "primary_apps": ["waike_learning", "gunnchai", "presentation", "files"],
        "waike_role": "teacher",
        "network": ["wifi", "offline"],
        "dock": False,
        "ring": False,
        "game_source": None,
        "ai_source": "gunnchai_main",
        "REAL_TEACHER_E6": False,
        "instructor_keys_must_not_leak_to_student": True,
    },
    "G14": {
        "id": "G14",
        "name": "Builder",
        "token": "BUILDER_DIGITAL_PICKUP_AND_USE_READY",
        "profile_id": "dsxl_coder",
        "terminal_allowed": True,
        "primary_apps": ["editor", "terminal", "git", "gunnchai", "gunnchsdk", "device_lab"],
        "waike_role": None,
        "network": ["wifi", "ethernet_dock"],
        "dock": False,
        "ring": False,
        "dual_display_required": True,
        "game_source": None,
        "ai_source": "gunnchai_main",
    },
    "G15": {
        "id": "G15",
        "name": "Creative",
        "token": "CREATIVE_DIGITAL_PICKUP_AND_USE_READY",
        "profile_id": "dsxl_coder",
        "terminal_allowed": False,
        "primary_apps": ["creator_studio", "gunnchai", "media", "export"],
        "waike_role": None,
        "network": ["wifi", "offline"],
        "dock": True,
        "ring": False,
        "game_source": None,
        "ai_source": "gunnchai_main",
        "toy_drawing_surface_forbidden_as_final_proof": True,
    },
}


def persona_table_skeleton() -> list[dict[str, Any]]:
    """Honest empty journey table — fill only with reproducible evidence."""
    rows = []
    for pid, p in PERSONAS.items():
        rows.append(
            {
                "persona": pid,
                "name": p["name"],
                "profile": p["profile_id"],
                "boot": "NOT_RUN",
                "launcher": "NOT_RUN",
                "apps": "NOT_RUN",
                "network": "NOT_RUN",
                "primary_task": "NOT_RUN",
                "artifact": "NOT_RUN",
                "save": "NOT_RUN",
                "reboot": "NOT_RUN",
                "resume": "NOT_RUN",
                "offline": "NOT_RUN",
                "reconnect": "NOT_RUN",
                "AI": "NOT_RUN",
                "WAIKE": "NOT_RUN" if p.get("waike_role") else "N/A",
                "dock": "NOT_RUN" if p.get("dock") else "N/A",
                "Ring": "NOT_RUN" if p.get("ring") else "N/A",
                "game": "NOT_RUN" if p.get("game_source") else "N/A",
                "developer_intervention": "UNKNOWN",
                "terminal": "FORBIDDEN" if not p["terminal_allowed"] else "ALLOWED_NOT_RUN",
                "S0": 0,
                "S1": 0,
                "S2": 0,
                "evidence": "NONE",
                "token_earned": False,
                "token_id": p["token"],
                "VISUAL_MODEL_REVIEW": "UNAVAILABLE",
            }
        )
    return rows
