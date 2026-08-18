"""Generate service-continuity profiles and benchmark scores from existing code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.app_runtime import RUNTIME_CATALOG
from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    OrchestratorState,
    orchestrator_for_device,
)
from gunnchos_device_os.device_classes import get_device_class, list_device_classes
from gunnchos_device_os.edge_io_contract import get_contract as get_edge_io_contract
from gunnchos_device_os.gunnchai_integration import CLAIM_BOUNDARY as GUNNCHAI_CLAIM
from gunnchos_device_os.mode_manager import get_mode_policy
from gunnchos_device_os.ota_state_machine import ALLOWED_TRANSITIONS, OtaState
from gunnchos_device_os.radio_capability import radio_profile_from_device
from gunnchos_device_os.runtime_profiles import DeviceProfileId, RuntimeProfileController
from gunnchos_device_os.service_continuity.model import (
    CLAIM_BOUNDARY,
    RQ,
    SCHEMA_ID,
    THESIS,
    ContinuityLevel,
    RESEARCH_CLASS_MAP,
    ResearchDeviceClass,
)
from gunnchos_device_os.waike_integration import CLAIM_BOUNDARY as WAIKE_CLAIM
from gunnchos_device_os.waike_integration import list_offline_lessons

ROOT = Path(__file__).resolve().parents[2]


# Injected digital metrics — same corpus as tests/test_connectivity_orchestrator.py.
# These are scenario *inputs*, not measured RF.
def _good_wifi() -> BearerMetrics:
    return BearerMetrics(
        available=True,
        signal_dbm=-45.0,
        latency_ms=18.0,
        jitter_ms=3.0,
        loss_pct=0.2,
        cost_per_mb=0.0,
        energy_mw=400.0,
        security_score=0.8,
        user_preference=0.7,
    )


def _good_ethernet() -> BearerMetrics:
    return BearerMetrics(
        available=True,
        signal_dbm=None,
        latency_ms=5.0,
        jitter_ms=1.0,
        loss_pct=0.0,
        cost_per_mb=0.0,
        energy_mw=150.0,
        security_score=0.95,
        user_preference=0.9,
    )


def classify_continuity(
    orchestrator_state: str,
    *,
    offline_covers_workload: bool,
) -> str:
    """Map orchestrator state + offline coverage onto the four RQ1 levels."""
    if orchestrator_state == OrchestratorState.CONNECTED.value:
        return ContinuityLevel.TARGET.value
    if orchestrator_state in {
        OrchestratorState.DEGRADED.value,
        OrchestratorState.TRANSITIONING.value,
    }:
        return ContinuityLevel.DEGRADED.value
    if orchestrator_state == OrchestratorState.OFFLINE.value and offline_covers_workload:
        return ContinuityLevel.MIN_USEFUL.value
    return ContinuityLevel.FAILED.value


def _runtime_export(profile_id: str | None) -> dict[str, Any] | None:
    if not profile_id:
        return None
    ctl = RuntimeProfileController()
    applied = ctl.apply(profile_id)
    return {
        "profile_id": profile_id,
        "cpu_cap_percent": applied["power"]["cpu_cap_percent"],
        "gpu_cap_percent": applied["power"]["gpu_cap_percent"],
        "tdp_boost": applied["power"].get("tdp_boost", False),
        "battery_saver": applied["power"].get("battery_saver", False),
        "governor": applied["power"].get("governor"),
        "ai_tier": applied["ai"]["tier"],
        "ai_max_tokens_per_min": applied["ai"]["max_tokens_per_min"],
        "ai_allow_cloud": applied["ai"]["allow_cloud"],
        "display_surface": applied["display"]["surface"],
        "source": "gunnchos_device_os.runtime_profiles.PROFILE_SPECS",
    }


def _mode_export(mode_names: list[str]) -> list[dict[str, Any]]:
    rows = []
    for name in mode_names:
        policy = get_mode_policy(name)
        rows.append(
            {
                "mode": name,
                "allowed_apps": list(policy.get("allowed_apps") or []),
                "blocked_apps": list(policy.get("blocked_apps") or []),
                "network": policy.get("network"),
                "offline_lessons": bool(policy.get("offline_lessons", False)),
                "source": "config/modes.yaml",
            }
        )
    return rows


def _workload_covered(offline_capabilities: list[str], workload: str) -> bool:
    return workload in offline_capabilities


def _run_scenario(
    device_id: str,
    scenario_id: str,
    *,
    offline_capabilities: list[str],
    workload: str,
) -> dict[str, Any]:
    orch = orchestrator_for_device(device_id)
    supported = set(orch.profile_supported)

    if scenario_id == "wifi_nominal":
        if "wifi" in supported:
            orch.update_metrics(BearerKind.WIFI, _good_wifi())
        orch.evaluate()
    elif scenario_id == "dock_ethernet":
        if "ethernet" in supported:
            orch.update_metrics(BearerKind.ETHERNET, _good_ethernet())
            if "wifi" in supported:
                orch.update_metrics(BearerKind.WIFI, _good_wifi())
        elif "wifi" in supported:
            orch.update_metrics(BearerKind.WIFI, _good_wifi())
        orch.evaluate()
    elif scenario_id == "degraded_wifi":
        if "wifi" in supported:
            orch.update_metrics(BearerKind.WIFI, _good_wifi())
            orch.evaluate()
            orch.inject_fault("degrade_active")
            orch.evaluate()
        else:
            orch.evaluate()
    elif scenario_id == "jam_wifi_offline_fallback":
        if "wifi" in supported:
            orch.update_metrics(BearerKind.WIFI, _good_wifi())
            orch.evaluate()
        orch.inject_fault("jam_wifi")
        orch.evaluate()
    elif scenario_id == "force_offline":
        if "wifi" in supported:
            orch.update_metrics(BearerKind.WIFI, _good_wifi())
        orch.inject_fault("force_offline")
        orch.evaluate()
    else:
        raise ValueError(f"unknown scenario: {scenario_id}")

    snap = orch.snapshot()
    ranked = [
        {"bearer": name, "score": score}
        for name, score in snap["ranked"]
        if score != float("-inf")
    ]
    level = classify_continuity(
        snap["state"],
        offline_covers_workload=_workload_covered(offline_capabilities, workload),
    )
    return {
        "scenario_id": scenario_id,
        "workload": workload,
        "device_id": device_id,
        "orchestrator_state": snap["state"],
        "active_bearer": snap["active_bearer"],
        "ranked_finite_scores": ranked,
        "offline_covers_workload": _workload_covered(offline_capabilities, workload),
        "continuity_level": level,
        "supported_bearers": sorted(supported),
        "metric_source": "tests/test_connectivity_orchestrator.py injected corpus",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_profile(research_class: str) -> dict[str, Any]:
    if research_class not in RESEARCH_CLASS_MAP:
        raise ValueError(f"unknown research class: {research_class}")
    mapping = RESEARCH_CLASS_MAP[research_class]
    class_id = str(mapping["device_class_id"])
    dc = get_device_class(class_id)
    radio = radio_profile_from_device(str(mapping["hardware_profile_id"]))
    runtime_id = mapping.get("runtime_profile_id")
    nearest = mapping.get("nearest_runtime_profile_id")
    executable_runtime = runtime_id or nearest
    runtime = _runtime_export(str(executable_runtime) if executable_runtime else None)
    docked = None
    if mapping.get("docked_runtime_profile_id"):
        docked = _runtime_export(str(mapping["docked_runtime_profile_id"]))

    offline_caps = list(dc.get("offline_capabilities") or [])
    workloads = {
        "lessons": "offline_lessons",
        "writing": "offline_writing",
        "coding": "offline_coding",
        "games": "offline_games",
        "research": "offline_research_notebooks",
    }

    scenarios = []
    for sid in (
        "wifi_nominal",
        "dock_ethernet",
        "degraded_wifi",
        "jam_wifi_offline_fallback",
        "force_offline",
    ):
        # Primary workload: first listed offline capability, else coding.
        primary = offline_caps[0] if offline_caps else "offline_coding"
        scenarios.append(
            _run_scenario(
                class_id,
                sid,
                offline_capabilities=offline_caps,
                workload=primary,
            )
        )
    # Explicit failed-path: coding on wearable (capability absent).
    if research_class == ResearchDeviceClass.WEARABLE.value:
        scenarios.append(
            _run_scenario(
                class_id,
                "force_offline",
                offline_capabilities=offline_caps,
                workload="offline_coding",
            )
        )
        scenarios[-1]["scenario_id"] = "force_offline_coding_unsupported"

    levels_seen = sorted({row["continuity_level"] for row in scenarios})
    return {
        "research_class": research_class,
        "mapping": mapping,
        "device_class": {
            "id": class_id,
            "display_name": dc.get("display_name"),
            "ram_target_gb": dc.get("ram_target_gb"),
            "storage_class": dc.get("storage_class"),
            "performance_class": dc.get("performance_class"),
            "battery_class": dc.get("battery_class"),
            "thermal_class": dc.get("thermal_class"),
            "dock_support": dc.get("dock_support"),
            "supported_modes": list(dc.get("supported_modes") or []),
            "supported_app_packs": list(dc.get("supported_app_packs") or []),
            "offline_capabilities": offline_caps,
            "deploy_role": dc.get("deploy_role"),
            "accessibility_defaults": dc.get("accessibility_defaults"),
            "hardware_contract_assumptions": dc.get("hardware_contract_assumptions"),
            "source": "config/device_classes.yaml",
        },
        "runtime_undocked": runtime,
        "runtime_docked": docked,
        "radio": {
            "wifi_class": radio.wifi_class,
            "ethernet_dock": radio.ethernet_dock,
            "bluetooth": radio.bluetooth,
            "offline_capable": radio.offline_capable,
            "cellular_class": radio.cellular_class.value,
            "ntn_class": radio.ntn_class.value,
            "supported_bearers": radio.supported_bearer_names(),
            "source": "hardware_compat/device_profiles + radio_capability.py",
        },
        "modes": _mode_export(list(dc.get("supported_modes") or [])),
        "workload_offline_coverage": {
            name: cap in offline_caps for name, cap in workloads.items()
        },
        "benchmark_scenarios": scenarios,
        "continuity_levels_observed": levels_seen,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _bridges() -> dict[str, Any]:
    edge = get_edge_io_contract()
    return {
        "gunnchai": {
            "module": "gunnchos_device_os.gunnchai_integration",
            "claim_boundary": GUNNCHAI_CLAIM,
        },
        "waike": {
            "module": "gunnchos_device_os.waike_integration",
            "offline_packs": list_offline_lessons(),
            "claim_boundary": WAIKE_CLAIM,
        },
        "edge_io": {
            "module": "gunnchos_device_os.edge_io_contract",
            "metrics": list(edge.get("metrics") or []),
            "local_only_default": bool(
                (edge.get("session") or {}).get("local_only_default", True)
            ),
            "claim_boundary": "Digital contract + session gates; not physical Edge-IO accuracy.",
        },
        "first_party_runtime_catalog": [app.id for app in RUNTIME_CATALOG],
        "ota_states": [s.value for s in OtaState],
        "ota_transition_count": sum(len(v) for v in ALLOWED_TRANSITIONS.values()),
        "runtime_profile_ids": [p.value for p in DeviceProfileId],
        "device_class_ids": list_device_classes(),
    }


def build_bundle() -> dict[str, Any]:
    profiles = {
        cls.value: build_profile(cls.value) for cls in ResearchDeviceClass
    }
    body = {
        "schema": SCHEMA_ID,
        "thesis": THESIS,
        "rq": RQ,
        "claim_boundary": CLAIM_BOUNDARY,
        "STANDARDIZED_6G": False,
        "shipping_os": False,
        "physical_boot": False,
        "research_classes": [cls.value for cls in ResearchDeviceClass],
        "continuity_levels": [lvl.value for lvl in ContinuityLevel],
        "profiles": profiles,
        "bridges": _bridges(),
        "sources": [
            "config/device_classes.yaml",
            "gunnchos_device_os/runtime_profiles.py",
            "gunnchos_device_os/radio_capability.py",
            "gunnchos_device_os/connectivity_orchestrator.py",
            "tests/test_connectivity_orchestrator.py",
            "config/modes.yaml",
            "hardware_compat/device_profiles/*.yaml",
        ],
    }
    encoded = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    body["content_digest_sha256"] = hashlib.sha256(encoded).hexdigest()
    return body


def write_bundle(out_dir: Path | None = None) -> dict[str, Any]:
    out = out_dir or (ROOT / "artifacts" / "supervisor_ready")
    out.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle()
    path = out / "SERVICE_CONTINUITY_PROFILES.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    bundle["_written"] = str(path)
    return bundle
