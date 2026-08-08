"""Tests for dual-screen runtime workflow harness."""
from __future__ import annotations

from gunnchos_device_os.dual_screen_runtime import (
    TOKEN_DUAL_SCREEN_RUNTIME_PASS,
    DualScreenRuntimeHarness,
    run_dual_screen_runtime_workflows,
)


def test_dual_screen_runtime_pass():
    report = run_dual_screen_runtime_workflows()
    assert report["ok"] is True, report.get("fault_injection")
    assert report["token"] == TOKEN_DUAL_SCREEN_RUNTIME_PASS
    assert report["sequence"]["ok"] is True
    assert report["fault_injection"]["detected"] is True
    assert report["with_runtime_services"]["ok"] is True
    assert report["full_operational_product_claimed"] is False


def test_workflow_sequence_covers_all_types():
    harness = DualScreenRuntimeHarness()
    seq = harness.run_workflow_sequence()
    assert seq["ok"] is True
    assert len(seq["results"]) == 5
