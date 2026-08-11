"""Virtual/destructive tests for A/B update, rollback, anti-rollback,
interrupted-update recovery, factory reset, recovery mode, and the
lost/revoked device path. All state lives under tmp_path — no real disk."""
from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.ab_update import ABUpdateManager, build_update_metadata

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def mgr(tmp_path):
    m = ABUpdateManager(REPO_ROOT, tmp_path / "device_state.json")
    m.init_device("dev-test-001")
    return m


def _metadata(counter: int = 1, to_version: str = "1.1.0", image_hash: str = "abc123"):
    return build_update_metadata(
        REPO_ROOT,
        realm_id="EVT_ENGINEERING_IMAGE",
        from_version="1.0.0",
        to_version=to_version,
        image_hash=image_hash,
        anti_rollback_counter=counter,
    )


def test_init_device_starts_on_slot_a(mgr):
    state = mgr.status()
    assert state["active_slot"] == "A"
    assert state["slots"]["A"]["status"] == "active"
    assert state["slots"]["B"]["status"] == "empty"


def test_stage_and_commit_update_flips_active_slot(mgr):
    meta = _metadata()
    staged = mgr.stage_update(meta)
    assert staged["ok"] is True
    assert staged["target_slot"] == "B"

    boot = mgr.commit_boot("B", boot_succeeds=True)
    assert boot["ok"] is True
    state = mgr.status()
    assert state["active_slot"] == "B"
    assert state["slots"]["B"]["version"] == "1.1.0"
    assert state["slots"]["A"]["status"] == "previous"


def test_signature_tamper_rejected(mgr):
    meta = _metadata()
    meta["to_version"] = "9.9.9-tampered"  # mutate after signing
    result = mgr.stage_update(meta)
    assert result["ok"] is False
    assert result["error"] == "signature_verification_failed"


def test_anti_rollback_violation_rejected(mgr):
    ok_update = mgr.stage_update(_metadata(counter=5))
    assert ok_update["ok"] is True
    mgr.commit_boot("B", boot_succeeds=True)

    downgrade = mgr.stage_update(_metadata(counter=2, to_version="0.9.0"))
    assert downgrade["ok"] is False
    assert downgrade["error"] == "anti_rollback_violation"


def test_revoked_signing_key_rejected(mgr):
    from gunnchos_device_os.release_engineering import dev_keys

    fp = dev_keys.dev_public_key_fingerprint(REPO_ROOT)
    mgr.revoke_key(fp, reason="key_compromise_drill")
    result = mgr.stage_update(_metadata())
    assert result["ok"] is False
    assert result["error"] == "signing_key_revoked"


def test_boot_failure_triggers_auto_rollback_after_max_attempts(mgr):
    mgr.stage_update(_metadata())
    for _ in range(3):
        result = mgr.commit_boot("B", boot_succeeds=False)
    assert result["auto_rollback_triggered"] is True
    state = mgr.status()
    assert state["active_slot"] == "A"
    assert state["slots"]["B"]["status"] == "unbootable"


def test_both_slots_unbootable_enters_recovery_mode(mgr):
    # Slot B never receives a real version, so rollback has nothing to fall
    # back to once A also exhausts its boot attempts.
    for _ in range(3):
        result = mgr.commit_boot("A", boot_succeeds=False)
    assert result["recovery_mode"] is True
    assert mgr.status()["recovery_mode"] is True


def test_interrupted_update_is_recovered_not_silently_booted(mgr):
    crash = mgr.stage_update(_metadata(), simulate_crash_before_commit=True)
    assert crash["ok"] is False
    assert crash["interrupted"] is True

    state = mgr.status()
    assert state["slots"]["B"]["in_progress"] is True

    boot_attempt = mgr.commit_boot("B", boot_succeeds=True)
    assert boot_attempt["ok"] is False
    assert boot_attempt["error"] == "slot_incomplete_run_recovery_first"

    recovery = mgr.recover_from_interrupted_update()
    assert recovery["recovered_slots"] == ["B"]
    state = mgr.status()
    assert state["slots"]["B"]["status"] == "corrupt_recovered"
    assert state["active_slot"] == "A"  # untouched


def test_manual_rollback_requires_bootable_previous_slot(mgr):
    result = mgr.manual_rollback()
    assert result["ok"] is False  # B has never had a real version

    mgr.stage_update(_metadata())
    mgr.commit_boot("B", boot_succeeds=True)
    rollback = mgr.manual_rollback()
    assert rollback["ok"] is True
    assert rollback["active_slot"] == "A"


def test_factory_reset_preserves_only_selected_keys(mgr):
    result = mgr.factory_reset(preserve_keys=["accounts"])
    assert result["ok"] is True
    assert result["preserved_keys"] == ["accounts"]
    assert set(result["wiped_keys"]) == {"apps", "settings"}
    state = mgr.status()
    assert "apps" not in state["user_data"]
    assert "accounts" in state["user_data"]


def test_recovery_mode_reports_recovery_realm_policy(mgr):
    result = mgr.enter_recovery_mode(reason="manual_service_request")
    assert result["ok"] is True
    assert result["recovery_mode"] is True
    assert result["recovery_behavior"]["recovery_partition_required"] is True
    assert result["allowed_capabilities"]["debug_access_allowed"] is False

    exited = mgr.exit_recovery_mode()
    assert exited["recovery_mode"] is False


def test_lost_device_path_blocks_updates_until_recovered(mgr):
    mgr.mark_device_lost(reason="reported_stolen")
    blocked = mgr.stage_update(_metadata())
    assert blocked["ok"] is False
    assert blocked["error"] == "device_marked_lost_updates_refused"

    wipe = mgr.execute_remote_wipe()
    assert wipe["ok"] is True
    state = mgr.status()
    assert state["remote_wipe_requested"] is False
    assert state["user_data"] == {}

    recovered = mgr.recover_lost_device(ownership_proof="signed_owner_challenge_response")
    assert recovered["ok"] is True
    allowed_again = mgr.stage_update(_metadata())
    assert allowed_again["ok"] is True


def test_recover_lost_device_requires_proof(mgr):
    mgr.mark_device_lost(reason="reported_stolen")
    result = mgr.recover_lost_device(ownership_proof="")
    assert result["ok"] is False
