"""Runtime service architecture — matrix, supervisor, APIs, faults."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.runtime import RuntimeSupervisor, service_matrix
from gunnchos_device_os.runtime.catalog import REQUIRED_SERVICE_IDS


def test_service_matrix_covers_all_required_services():
    matrix = service_matrix()
    assert matrix["all_present"] is True
    assert matrix["missing"] == []
    assert matrix["count"] == len(REQUIRED_SERVICE_IDS)
    assert matrix["token"] == "GUNNCHOS_RUNTIME_SERVICE_MATRIX_DIGITAL_PASS"
    assert matrix["full_operational_product_claimed"] is False
    ids = {row["service_id"] for row in matrix["services"]}
    assert ids == set(REQUIRED_SERVICE_IDS)


def test_supervisor_starts_all_services_in_dep_order(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    result = sup.start_all()
    assert not result["faulted"]
    assert set(result["started"]) == set(REQUIRED_SERVICE_IDS)
    # deps before dependents
    order = {sid: i for i, sid in enumerate(result["order"])}
    assert order["hal"] < order["input"]
    assert order["input"] < order["ring"]
    assert order["display"] < order["dock"]
    assert order["dock"] < order["continuity"]
    assert order["identity"] < order["permissions"]
    assert order["permissions"] < order["sandbox"]
    assert order["identity"] < order["privacy"]
    assert order["permissions"] < order["privacy"]
    assert order["diagnostics"] < order["privacy"]
    assert order["diagnostics"] < order["updater"]
    assert order["updater"] < order["recovery"]
    assert order["profile_manager"] < order["ai_interface"]
    assert order["connectivity"] < order["fleet_agent"]
    assert result["full_operational_product_claimed"] is False


def test_supervisor_api_and_persistence_roundtrip(tmp_path: Path):
    root = tmp_path / "runtime"
    sup = RuntimeSupervisor(persistence_root=root)
    sup.start_all()
    profiles = sup.call("hal", "list_profiles")
    assert "Student14" in profiles
    acct = sup.call("identity", "create_account", display_name="Ada", email="ada@example.com")
    device = "dev-runtime-1"
    binding = sup.call(
        "identity",
        "bind_device",
        account_id=acct["account_id"],
        device_id=device,
        device_class="ds_xl_coder",
    )
    assert binding["device_id"] == device
    sess = sup.call(
        "identity",
        "issue_session",
        account_id=acct["account_id"],
        device_id=device,
    )
    valid = sup.call(
        "identity",
        "validate_session",
        session_id=sess["session_id"],
        token=sess["token"],
        device_id=device,
    )
    assert valid["valid"] is True
    # persistence files written
    assert (root / "identity.json").exists()
    loaded = json.loads((root / "identity.json").read_text(encoding="utf-8"))
    assert loaded["service_id"] == "identity"


def test_fault_injection_and_restart(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    status = sup.inject_fault("display", "backend_glitch", "simulated")
    assert status["restart_count"] >= 1
    assert status["state"] == "running"
    assert any(e["event"] == "fault" for e in sup.events)


def test_sandbox_permissions_fleet_ai_paths(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    profile = sup.call("sandbox", "create_profile", app_id="notes", app_class="third_party")
    assert profile["app_id"] == "notes"
    denied = sup.call("sandbox", "check_capability", app_id="notes", capability="system_service")
    assert denied["decision"] == "deny"
    enroll = sup.call("fleet_agent", "enroll", enrollment_token="DEV_ENROLLMENT_TOKEN")
    assert enroll["enrolled"] is True
    reject = sup.call("fleet_agent", "enroll", enrollment_token="PROD_SECRET")
    assert reject["enrolled"] is False
    hb = sup.call("fleet_agent", "heartbeat")
    assert hb["ok"] is True
    tutor = sup.call("ai_interface", "tutor_start", profile="student", topic="math")
    assert tutor["privacy_mode"] == "local_only"
    a11y = sup.call("a11y", "apply", overrides={"high_contrast": True})
    assert a11y["high_contrast"] is True


def test_updater_ota_via_runtime(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    result = sup.call("updater", "run_ota", target_version="0.1.1")
    assert result["state"] == "committed"
    slots = sup.call("updater", "slots")
    assert slots["active_slot"] in ("a", "b")


def test_continuity_and_dock_via_runtime(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    attach = sup.call("continuity", "attach", dock_id="rt-dock")
    assert attach["kind"] == "attach"
    report = sup.call("continuity", "report")
    assert report["docked"] is True
    detach = sup.call("continuity", "detach", safe=True)
    assert detach["safe"] is True


def test_matrix_report_write(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    path = sup.write_matrix_report(tmp_path / "matrix_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["matrix"]["token"] == "GUNNCHOS_RUNTIME_SERVICE_MATRIX_DIGITAL_PASS"


def test_stop_all(tmp_path: Path):
    sup = RuntimeSupervisor(persistence_root=tmp_path / "runtime")
    sup.start_all()
    stopped = sup.stop_all()
    assert len(stopped["stopped"]) == len(REQUIRED_SERVICE_IDS)
