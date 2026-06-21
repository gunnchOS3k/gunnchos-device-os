"""Tests for hardware boot readiness."""
from gunnchos_device_os.hardware_boot_readiness import evaluate_boot_readiness


def test_boot_readiness_all_devices():
    for did in ("student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"):
        r = evaluate_boot_readiness(did)
        assert r["boot_ready_simulated"] is True
        assert "simulated" in r["claim_boundary"].lower() or r["status"] == "simulated"
