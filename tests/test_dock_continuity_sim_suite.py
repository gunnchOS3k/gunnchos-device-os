"""Dock continuity simulation suite tests."""
from __future__ import annotations

from gunnchos_device_os.dock.continuity_sim_suite import (
    SCENARIOS,
    run_continuity_simulation_suite,
)
from gunnchos_device_os.dock.simulator import STATUS_PHYSICAL_PENDING, STATUS_SIM_PASS


def test_continuity_simulation_suite_passes_all_scenarios():
    report = run_continuity_simulation_suite()
    assert report["ok"] is True, report["scenarios"]
    assert report["scenario_count"] == len(SCENARIOS)
    assert STATUS_SIM_PASS in report["status_tokens"]
    assert STATUS_PHYSICAL_PENDING in report["status_tokens"]
    assert report["full_operational_product_claimed"] is False
    for row in report["scenarios"]:
        assert row["ok"] is True, row


def test_suite_covers_expected_scenario_names():
    report = run_continuity_simulation_suite()
    names = {r["scenario"] for r in report["scenarios"]}
    assert names == set(SCENARIOS)


def test_suite_covers_fault_injection_expansions():
    report = run_continuity_simulation_suite()
    names = {r["scenario"] for r in report["scenarios"]}
    assert "fault_mid_attach_power_loss" in names
    assert "fault_ethernet_drop_while_docked" in names
    assert "fault_snapshot_corruption_recovery" in names
    assert "fault_hot_unplug_during_restore" in names
    assert report["scenario_count"] >= 9
