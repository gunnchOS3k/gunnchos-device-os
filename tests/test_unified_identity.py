"""Unified identity — account/session/device binding."""
from __future__ import annotations

import pytest

from gunnchos_device_os.unified_identity import (
    AccountStatus,
    BindingState,
    SessionState,
    UnifiedIdentityService,
)


def _setup():
    svc = UnifiedIdentityService()
    acct = svc.create_account("Ada", "ada@school.example", roles=["student"])
    dev = svc.register_device("student_14_5", label="Ada's laptop")
    binding = svc.bind_device(acct.account_id, dev.device_id, trust_level="school")
    return svc, acct, dev, binding


def test_create_account_hashes_email():
    svc = UnifiedIdentityService()
    acct = svc.create_account("Ada", "Ada@School.Example")
    assert "ada@" not in acct.email_hash
    assert len(acct.email_hash) == 64
    assert acct.status == AccountStatus.ACTIVE


def test_duplicate_account_raises():
    svc = UnifiedIdentityService()
    svc.create_account("Ada", "ada@school.example", account_id="acct-1")
    with pytest.raises(ValueError):
        svc.create_account("Ada2", "other@x.com", account_id="acct-1")


def test_bind_requires_existing_account_and_device():
    svc = UnifiedIdentityService()
    with pytest.raises(KeyError):
        svc.bind_device("missing", "d1")
    svc.create_account("A", "a@x.com", account_id="a1")
    with pytest.raises(KeyError):
        svc.bind_device("a1", "missing")


def test_session_requires_binding():
    svc = UnifiedIdentityService()
    acct = svc.create_account("A", "a@x.com")
    dev = svc.register_device("handheld_hybrid")
    with pytest.raises(PermissionError):
        svc.issue_session(acct.account_id, dev.device_id)


def test_issue_and_validate_session():
    svc, acct, dev, _binding = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000_000, ttl_ms=60_000)
    assert issued["token"]
    assert issued["token_hash"] != issued["token"]
    stored = svc.sessions[issued["session_id"]]
    assert stored.token_hash == issued["token_hash"]
    ok = svc.validate_session(
        issued["session_id"],
        issued["token"],
        device_id=dev.device_id,
        now_ms=1_010_000,
    )
    assert ok["valid"] is True
    assert ok["roles"] == ["student"]
    assert ok["mock"] is False


def test_session_device_mismatch():
    svc, acct, dev, _ = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000)
    bad = svc.validate_session(issued["session_id"], issued["token"], device_id="other", now_ms=1_000)
    assert bad["valid"] is False
    assert bad["reason"] == "device_mismatch"


def test_session_expiry():
    svc, acct, dev, _ = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000, ttl_ms=100)
    expired = svc.validate_session(issued["session_id"], issued["token"], now_ms=2_000)
    assert expired["valid"] is False
    assert expired["reason"] == "expired"
    assert svc.sessions[issued["session_id"]].state == SessionState.EXPIRED


def test_bad_token_rejected():
    svc, acct, dev, _ = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000)
    bad = svc.validate_session(issued["session_id"], "not-the-token", now_ms=1_000)
    assert bad["reason"] == "bad_token"


def test_unbind_revokes_sessions():
    svc, acct, dev, binding = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000)
    svc.unbind_device(binding.binding_id)
    assert binding.state == BindingState.REVOKED
    result = svc.validate_session(issued["session_id"], issued["token"], now_ms=1_000)
    assert result["valid"] is False
    assert result["reason"] in ("revoked", "binding_revoked")


def test_revoke_session():
    svc, acct, dev, _ = _setup()
    issued = svc.issue_session(acct.account_id, dev.device_id, now_ms=1_000)
    svc.revoke_session(issued["session_id"])
    result = svc.validate_session(issued["session_id"], issued["token"], now_ms=1_000)
    assert result["reason"] == "revoked"


def test_suspended_account_cannot_bind():
    svc = UnifiedIdentityService()
    acct = svc.create_account("A", "a@x.com", account_id="a1")
    dev = svc.register_device("dock")
    acct.status = AccountStatus.SUSPENDED
    with pytest.raises(PermissionError):
        svc.bind_device("a1", dev.device_id)


def test_idempotent_rebind():
    svc, acct, dev, binding = _setup()
    again = svc.bind_device(acct.account_id, dev.device_id)
    assert again.binding_id == binding.binding_id


def test_bindings_for_account_and_status():
    svc, acct, _dev, _ = _setup()
    bindings = svc.bindings_for_account(acct.account_id)
    assert len(bindings) == 1
    st = svc.status()
    assert st["accounts"] == 1
    assert st["bindings"] == 1
    assert st["mock"] is False
