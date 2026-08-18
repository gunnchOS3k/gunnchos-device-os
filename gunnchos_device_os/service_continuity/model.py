"""RQ1 Service-Continuity Profile Model.

Unifies the four research device classes (desk / mobile-docked / local-creation /
wearable) with existing `config/device_classes.yaml` IDs, runtime profiles,
radio capability, and the connectivity orchestrator.

Levels min-useful / degraded / target / failed are classified from
`OrchestratorState` plus per-class `offline_capabilities` — not invented RF
numbers. Injected bearer metrics are the digital test corpus already used by
`tests/test_connectivity_orchestrator.py`.

Paper I infrastructure only. Not a shipping OS. Not physical boot.
"""
from __future__ import annotations

from enum import Enum

CLAIM_BOUNDARY = (
    "Digital service-continuity profile model. Metrics are exported from "
    "existing device class YAML, runtime profiles, radio capability, and "
    "orchestrator scores on labeled injected scenarios. Not live RF, not "
    "carrier attach, not a shipping OS, not physical boot evidence."
)

THESIS = "Resilience-Aware Service Continuity in Heterogeneous 6G Networks"
RQ = "RQ1"


class ContinuityLevel(str, Enum):
    TARGET = "target"
    DEGRADED = "degraded"
    MIN_USEFUL = "min_useful"
    FAILED = "failed"


class ResearchDeviceClass(str, Enum):
    DESK = "desk"
    MOBILE_DOCKED = "mobile-docked"
    LOCAL_CREATION = "local-creation"
    WEARABLE = "wearable"


# Research class → existing config/runtime IDs (no new SKUs).
RESEARCH_CLASS_MAP: dict[str, dict[str, str | None]] = {
    ResearchDeviceClass.DESK.value: {
        "device_class_id": "student_14_5",
        "runtime_profile_id": "student_14_5",
        "docked_runtime_profile_id": "dock",
        "hardware_profile_id": "student_14_5",
    },
    ResearchDeviceClass.MOBILE_DOCKED.value: {
        "device_class_id": "handheld_hybrid",
        "runtime_profile_id": "handheld_hybrid",
        "docked_runtime_profile_id": "dock",
        "hardware_profile_id": "handheld_hybrid",
    },
    ResearchDeviceClass.LOCAL_CREATION.value: {
        "device_class_id": "ds_xl_coder",
        "runtime_profile_id": "ds_xl_coder",
        "docked_runtime_profile_id": "dock",
        "hardware_profile_id": "ds_xl_coder",
    },
    ResearchDeviceClass.WEARABLE.value: {
        "device_class_id": "wearables_arena_set",
        # runtime_profiles.DeviceProfileId has no wearable entry.
        "runtime_profile_id": None,
        "nearest_runtime_profile_id": "handheld_hybrid",
        "docked_runtime_profile_id": None,
        "hardware_profile_id": "wearables_arena_set",
        "runtime_gap": (
            "runtime_profiles.PROFILE_SPECS has student/ds_xl/handheld/dock only; "
            "wearable uses handheld_hybrid as nearest executable profile."
        ),
    },
}

SCHEMA_ID = "gunnchos.service_continuity_profile.v1"
