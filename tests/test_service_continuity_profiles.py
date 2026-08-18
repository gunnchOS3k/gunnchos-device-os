"""RQ1 service-continuity profiles generated from existing Device OS modules."""
from __future__ import annotations

from gunnchos_device_os.connectivity_orchestrator import OrchestratorState
from gunnchos_device_os.device_classes import get_device_class
from gunnchos_device_os.service_continuity import (
    RESEARCH_CLASS_MAP,
    ContinuityLevel,
    ResearchDeviceClass,
    build_bundle,
    build_profile,
    classify_continuity,
)


def test_four_research_classes_map_to_existing_yaml():
    assert set(RESEARCH_CLASS_MAP) == {c.value for c in ResearchDeviceClass}
    for research, mapping in RESEARCH_CLASS_MAP.items():
        dc = get_device_class(str(mapping["device_class_id"]))
        assert dc["id"] == mapping["device_class_id"], research
        assert not get_device_class(dc["id"]).get("invented")


def test_classify_continuity_uses_orchestrator_states():
    assert (
        classify_continuity(OrchestratorState.CONNECTED.value, offline_covers_workload=False)
        == ContinuityLevel.TARGET.value
    )
    assert (
        classify_continuity(OrchestratorState.DEGRADED.value, offline_covers_workload=True)
        == ContinuityLevel.DEGRADED.value
    )
    assert (
        classify_continuity(OrchestratorState.OFFLINE.value, offline_covers_workload=True)
        == ContinuityLevel.MIN_USEFUL.value
    )
    assert (
        classify_continuity(OrchestratorState.OFFLINE.value, offline_covers_workload=False)
        == ContinuityLevel.FAILED.value
    )


def test_bundle_metrics_come_from_device_class_yaml():
    bundle = build_bundle()
    assert bundle["shipping_os"] is False
    assert bundle["physical_boot"] is False
    assert bundle["STANDARDIZED_6G"] is False
    desk = bundle["profiles"]["desk"]
    yaml_ram = get_device_class("student_14_5")["ram_target_gb"]
    assert desk["device_class"]["ram_target_gb"] == yaml_ram
    assert desk["runtime_undocked"]["cpu_cap_percent"] == 70
    assert desk["runtime_undocked"]["source"].endswith("PROFILE_SPECS")


def test_wifi_nominal_desk_is_target():
    desk = build_profile("desk")
    wifi = next(s for s in desk["benchmark_scenarios"] if s["scenario_id"] == "wifi_nominal")
    assert wifi["continuity_level"] == ContinuityLevel.TARGET.value
    assert wifi["metric_source"].startswith("tests/test_connectivity_orchestrator.py")


def test_wearable_coding_offline_is_failed():
    wearable = build_profile("wearable")
    assert "offline_coding" not in wearable["device_class"]["offline_capabilities"]
    row = next(
        s
        for s in wearable["benchmark_scenarios"]
        if s["scenario_id"] == "force_offline_coding_unsupported"
    )
    assert row["continuity_level"] == ContinuityLevel.FAILED.value
    assert row["offline_covers_workload"] is False


def test_wearable_runtime_gap_is_documented_not_invented():
    wearable = build_profile("wearable")
    assert wearable["mapping"]["runtime_profile_id"] is None
    assert wearable["runtime_undocked"]["profile_id"] == "handheld_hybrid"
    assert "runtime_gap" in wearable["mapping"]
