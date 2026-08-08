"""OTA update/rollback state machine — happy path + fault injection."""
from __future__ import annotations

import pytest

from gunnchos_device_os.ota_state_machine import (
    Fault,
    OtaState,
    OtaStateMachine,
    Slot,
    UpdatePackage,
)
from gunnchos_device_os.identity import sha256_text


def _pkg(version: str = "0.2.0", **kwargs) -> UpdatePackage:
    defaults = dict(
        version=version,
        target_slot=Slot.B,
        digest_sha256=sha256_text(version),
        signature_valid=True,
        security_version=1,
    )
    defaults.update(kwargs)
    return UpdatePackage(**defaults)


def test_happy_path_commits_to_new_slot():
    sm = OtaStateMachine()
    result = sm.run_happy_path(_pkg())
    assert result["state"] == OtaState.COMMITTED.value
    assert result["active_slot"] == Slot.B.value
    assert result["slots"]["b"]["version"] == "0.2.0"
    assert result["slots"]["b"]["successful"] is True
    assert result["mock"] is False


def test_already_current_returns_idle():
    sm = OtaStateMachine()
    r = sm.check_for_update(_pkg(version="0.1.0"))
    assert r["update_available"] is False
    assert sm.state == OtaState.IDLE


def test_anti_rollback_security_version():
    sm = OtaStateMachine()
    sm.slots["a"].security_version = 5
    r = sm.check_for_update(_pkg(security_version=2))
    assert r["state"] == OtaState.FAILED.value
    assert r["last_error"] == "anti_rollback_security_version"


def test_fault_download_corrupt():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.inject_fault(Fault.DOWNLOAD_CORRUPT)
    r = sm.download()
    assert r["state"] == OtaState.FAILED.value
    assert r["last_error"] == "download_corrupt"


def test_fault_signature_invalid():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.inject_fault(Fault.SIGNATURE_INVALID)
    r = sm.verify()
    assert r["state"] == OtaState.FAILED.value
    assert "signature" in r["last_error"]


def test_fault_signature_via_package_flag():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg(signature_valid=False))
    sm.download()
    r = sm.verify()
    assert r["state"] == OtaState.FAILED.value


def test_fault_stage_io():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.verify()
    sm.inject_fault(Fault.STAGE_IO_ERROR)
    r = sm.stage()
    assert r["last_error"] == "stage_io_error"


def test_fault_apply_timeout():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.verify()
    sm.stage()
    sm.inject_fault(Fault.APPLY_TIMEOUT)
    r = sm.apply()
    assert r["last_error"] == "apply_timeout"


def test_fault_reboot_abort():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.verify()
    sm.stage()
    sm.apply()
    sm.inject_fault(Fault.REBOOT_ABORT)
    r = sm.simulate_reboot()
    assert r["last_error"] == "reboot_abort"


def test_health_check_failure_rolls_back():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.verify()
    sm.stage()
    sm.apply()
    sm.simulate_reboot()
    assert sm.active_slot == Slot.B
    r = sm.health_check(healthy=False)
    assert r["state"] == OtaState.ROLLED_BACK.value
    assert r["active_slot"] == Slot.A.value


def test_fault_health_check_inject():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.download()
    sm.verify()
    sm.stage()
    sm.apply()
    sm.simulate_reboot()
    sm.inject_fault(Fault.HEALTH_CHECK_FAIL)
    r = sm.health_check(healthy=True)
    assert r["state"] == OtaState.ROLLED_BACK.value


def test_illegal_transition_raises():
    sm = OtaStateMachine()
    with pytest.raises(RuntimeError):
        sm.download()


def test_retargets_active_slot_package_to_inactive():
    sm = OtaStateMachine()
    r = sm.check_for_update(_pkg(target_slot=Slot.A))
    assert r["package"]["target_slot"] == Slot.B.value


def test_rollback_from_failed():
    sm = OtaStateMachine()
    sm.check_for_update(_pkg())
    sm.inject_fault(Fault.DOWNLOAD_CORRUPT)
    sm.download()
    assert sm.state == OtaState.FAILED
    r = sm.rollback()
    assert r["state"] == OtaState.ROLLED_BACK.value


def test_reset_to_idle_after_commit():
    sm = OtaStateMachine()
    sm.run_happy_path(_pkg())
    r = sm.reset_to_idle()
    assert r["state"] == OtaState.IDLE.value
    assert r["pending"] is None


def test_history_records_transitions():
    sm = OtaStateMachine()
    sm.run_happy_path(_pkg("0.3.0"))
    states = [e.to_state for e in sm.history]
    assert OtaState.COMMITTED.value in states
    assert len(sm.history) >= 8
