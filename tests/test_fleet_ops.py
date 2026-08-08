"""Fleet ops simulation — enrollment, rings, canary, rollback, SLO stubs."""
from __future__ import annotations

from gunnchos_device_os.fleet_ops import (
    DeviceHealthState,
    FleetOpsSimulator,
    UpdateRing,
)
from gunnchos_device_os.security_event_log import clear_events, get_events


def setup_function():
    clear_events(reset_persistent=True)


def test_enroll_inventory_diagnostics():
    fleet = FleetOpsSimulator(org_id="gary-sim")
    out = fleet.enroll(
        "dev-1",
        cohort="school-a",
        ring=UpdateRing.CANARY,
        inventory={"sku_class": "student_14_5", "wifi": "wifi_6e"},
    )
    assert out["enrollment"] == "enrolled"
    assert out["mock"] is False
    inv = fleet.inventory_snapshot()
    assert inv["count"] == 1
    assert "dev-1" in inv["devices"]
    report = fleet.run_diagnostics("dev-1")
    assert report["checks"]["enrollment_active"] is True
    assert report["mock"] is False


def test_canary_abort_triggers_rollback():
    fleet = FleetOpsSimulator()
    fleet.canary_abort_threshold = 2
    fleet.enroll("c1", ring=UpdateRing.DEV)
    fleet.enroll("c2", ring=UpdateRing.DEV)
    fleet.enroll("c3", ring=UpdateRing.EARLY)
    start = fleet.start_rollout("0.2.0-canary", canary_percent=50)
    assert start["rollout_id"]
    assert len(start["canary_device_ids"]) >= 1
    # Fail canaries to abort
    first = start["canary_device_ids"][0]
    r1 = fleet.report_canary_result(first, success=False)
    assert r1["aborted"] is False
    # Ensure a second canary exists or reuse after assign
    if len(start["canary_device_ids"]) < 2:
        fleet.assign_ring("c2", UpdateRing.CANARY)
        fleet.devices["c2"].target_version = "0.2.0-canary"
        second = "c2"
    else:
        second = start["canary_device_ids"][1]
    r2 = fleet.report_canary_result(second, success=False)
    assert r2["aborted"] is True
    assert "rollback" in r2
    assert fleet.devices[first].current_version == "0.0.9-evt0"


def test_promote_rings_after_canary_success():
    fleet = FleetOpsSimulator()
    fleet.enroll("a", ring=UpdateRing.CANARY)
    fleet.start_rollout("0.2.0")
    fleet.report_canary_result("a", success=True)
    promo = fleet.promote_rings()
    assert promo["promoted"] is True
    assert fleet.devices["a"].ring == UpdateRing.EARLY


def test_health_security_telemetry_and_slo():
    fleet = FleetOpsSimulator()
    fleet.enroll("sec-1")
    fleet.update_health("sec-1", DeviceHealthState.DEGRADED, metrics={"loss_pct": 5})
    tel = fleet.record_security_telemetry(
        "sec-1",
        "policy_tamper_suspected",
        {"token": "secret-should-redact", "note": "test"},
    )
    assert tel["logged"] is True
    events = get_events()
    assert any("fleet_sec_" in e.get("event_type", "") for e in events)
    observed = fleet.observe_slo("enrollment_success_rate", 1.0)
    assert observed["status"] == "met_sim"
    report = fleet.slo_report()
    assert report["mock"] is False
    assert "not production" in report["note"].lower() or "stub" in report["note"].lower()


def test_claim_boundary_present():
    fleet = FleetOpsSimulator()
    snap = fleet.snapshot()
    assert "no remote mdm" in snap["claim_boundary"].lower()
    assert snap["mock"] is False
