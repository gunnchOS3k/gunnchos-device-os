"""Expanded dock continuity simulation scenarios (software-only)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.dock.continuity import DockContinuityEngine
from gunnchos_device_os.dock.simulator import STATUS_PHYSICAL_PENDING, STATUS_SIM_PASS
from gunnchos_device_os.identity import sha256_json


SCENARIOS = (
    "attach_extend_undock",
    "mirror_then_degraded",
    "multi_attach_cycle",
    "unsafe_undock_flag",
    "save_identity_network_ai_roundtrip",
)


def _scenario_attach_extend_undock() -> dict[str, Any]:
    eng = DockContinuityEngine()
    eng.apps = ["launcher", "notes"]
    eng.save_blob = {"slot": 1, "progress": 10}
    checksum = sha256_json(eng.save_blob)
    eng.attach("sim-extend", external_display=True, ethernet=True, audio_dock=True)
    assert eng.layout_profile == "docked-extend"
    eng.safe_undock()
    ok = (
        eng.docked is False
        and eng.apps == ["launcher", "notes"]
        and sha256_json(eng.save_blob) == checksum
        and eng.network_route == "wlan"
        and eng.audio_route == "internal"
    )
    return {"scenario": "attach_extend_undock", "ok": ok, "engine": eng}


def _scenario_mirror_then_degraded() -> dict[str, Any]:
    eng = DockContinuityEngine()
    eng.attach("sim-mirror", external_display=False)
    assert eng.layout_profile == "docked-mirror"
    eng.enter_degraded_mode("hdmi_unplug")
    ok = eng.degraded is True and eng.layout_profile == "degraded-internal-only"
    eng.safe_undock()
    return {"scenario": "mirror_then_degraded", "ok": ok, "engine": eng}


def _scenario_multi_attach_cycle() -> dict[str, Any]:
    eng = DockContinuityEngine()
    eng.save_blob = {"slot": 2, "progress": 55}
    checksum = sha256_json(eng.save_blob)
    for i in range(3):
        eng.attach(f"sim-cycle-{i}", external_display=True)
        eng.safe_undock()
    ok = sha256_json(eng.save_blob) == checksum and eng.docked is False
    return {"scenario": "multi_attach_cycle", "ok": ok, "cycles": 3, "engine": eng}


def _scenario_unsafe_undock_flag() -> dict[str, Any]:
    eng = DockContinuityEngine()
    eng.attach("sim-unsafe")
    eng.detach(safe=False)
    ok = "unsafe_undock_observed" in eng.errors and eng.docked is False
    return {"scenario": "unsafe_undock_flag", "ok": ok, "engine": eng}


def _scenario_save_identity_network_ai_roundtrip() -> dict[str, Any]:
    eng = DockContinuityEngine()
    eng.apps = ["launcher", "media", "campus"]
    eng.identity = {"user": "fleet-student", "auth": "device-bound"}
    eng.save_blob = {"slot": 4, "progress": 90, "chapter": "finale"}
    eng.set_ai_privacy(local_only=True, cloud_export=False, retain_prompts=False)
    checksum = sha256_json(eng.save_blob)
    eng.attach("sim-roundtrip", ethernet=True, audio_dock=True, power_passthrough=True)
    assert eng.network_route == "ethernet-via-dock"
    snap = eng.snapshot_session()
    eng.apps = ["tampered"]
    eng.identity = {"user": "x"}
    eng.save_blob = {"slot": 0}
    eng.ai_privacy = {"local_only": False, "cloud_export": True}
    eng.restore_from_snapshot(snap)
    eng.safe_undock()
    ok = (
        eng.apps == ["launcher", "media", "campus"]
        and eng.identity["user"] == "fleet-student"
        and sha256_json(eng.save_blob) == checksum
        and eng.ai_privacy.get("cloud_export") is False
        and eng.network_route == "wlan"
    )
    return {"scenario": "save_identity_network_ai_roundtrip", "ok": ok, "engine": eng}


_RUNNERS = {
    "attach_extend_undock": _scenario_attach_extend_undock,
    "mirror_then_degraded": _scenario_mirror_then_degraded,
    "multi_attach_cycle": _scenario_multi_attach_cycle,
    "unsafe_undock_flag": _scenario_unsafe_undock_flag,
    "save_identity_network_ai_roundtrip": _scenario_save_identity_network_ai_roundtrip,
}


def run_continuity_simulation_suite() -> dict[str, Any]:
    results = []
    for name in SCENARIOS:
        outcome = _RUNNERS[name]()
        eng: DockContinuityEngine = outcome.pop("engine")
        results.append(
            {
                "scenario": outcome["scenario"],
                "ok": outcome["ok"],
                "extra": {k: v for k, v in outcome.items() if k not in ("scenario", "ok")},
                "event_kinds": [e["kind"] for e in eng.events],
                "errors": list(eng.errors),
            }
        )
    all_ok = all(r["ok"] for r in results)
    tokens = [STATUS_SIM_PASS if all_ok else "DOCK_CONTINUITY_SIMULATION_FAIL", STATUS_PHYSICAL_PENDING]
    return {
        "schema": "gunnchos.dock.continuity_simulation_suite.v1",
        "ok": all_ok,
        "scenarios": results,
        "scenario_count": len(results),
        "status_tokens": tokens,
        "claim_boundary": (
            "Software dock continuity simulation suite only. "
            "PHYSICAL_DOCK_EVIDENCE_PENDING until real-device evidence is attached."
        ),
        "full_operational_product_claimed": False,
    }
