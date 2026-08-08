"""Permissions manager — API, least privilege, expiry."""
from __future__ import annotations

import pytest

from gunnchos_device_os.permissions_manager import Decision, Permission, PermissionsManager


def test_deny_by_default_without_grant():
    pm = PermissionsManager(role="student")
    result = pm.check("notes", Permission.CAMERA)
    assert result["decision"] == Decision.DENY.value
    assert result["mock"] is False


def test_student_cannot_request_outside_allowlist():
    pm = PermissionsManager(role="student")
    result = pm.request("notes", Permission.LOCATION, explicit_user_grant=True)
    assert result["decision"] == Decision.DENY.value
    assert result["reason"] == "outside_role_allowlist"


def test_sensitive_requires_explicit_grant_for_student():
    pm = PermissionsManager(role="student")
    # files_write is sensitive and in student allowlist
    denied = pm.request("notes", Permission.FILES_WRITE, explicit_user_grant=False)
    assert denied["decision"] == Decision.DENY.value
    allowed = pm.request("notes", Permission.FILES_WRITE, explicit_user_grant=True)
    assert allowed["decision"] == Decision.ALLOW.value
    assert pm.check("notes", Permission.FILES_WRITE)["decision"] == Decision.ALLOW.value


def test_non_sensitive_network_for_student():
    pm = PermissionsManager(role="student")
    result = pm.request("browser", Permission.NETWORK)
    assert result["decision"] == Decision.ALLOW.value
    pm.assert_allowed("browser", Permission.NETWORK)


def test_assert_allowed_raises():
    pm = PermissionsManager(role="guest")
    with pytest.raises(PermissionError):
        pm.assert_allowed("cam", Permission.CAMERA)


def test_guest_least_privilege_report_flags_overreach_path():
    pm = PermissionsManager(role="guest")
    # Guest cannot get camera via allowlist
    pm.request("spy", Permission.CAMERA, explicit_user_grant=True)
    report = pm.least_privilege_report("spy")
    assert Permission.CAMERA.value not in [h["permission"] for h in report["held"] if h["decision"] == "allow"]
    assert report["mock"] is False


def test_admin_can_hold_ai_cloud_export():
    pm = PermissionsManager(role="admin")
    result = pm.request("tutor", Permission.AI_CLOUD_EXPORT, explicit_user_grant=True)
    assert result["decision"] == Decision.ALLOW.value


def test_revoke_and_expiry(monkeypatch):
    pm = PermissionsManager(role="student")
    # Grant with TTL
    clock = {"t": 1_000_000}

    def fake_time():
        return clock["t"]

    monkeypatch.setattr("gunnchos_device_os.permissions_manager.time.time", lambda: clock["t"] / 1000.0)
    pm.request("notes", Permission.NETWORK, ttl_ms=1000)
    assert pm.check("notes", Permission.NETWORK)["decision"] == Decision.ALLOW.value
    clock["t"] = 1_002_000
    assert pm.check("notes", Permission.NETWORK)["decision"] == Decision.DENY.value
    assert pm.check("notes", Permission.NETWORK)["reason"] == "grant_expired"
    pm.request("notes", Permission.NETWORK)
    pm.revoke("notes", Permission.NETWORK)
    assert pm.check("notes", Permission.NETWORK)["decision"] == Decision.DENY.value


def test_ai_local_cannot_cloud_export():
    pm = PermissionsManager(role="ai_local")
    result = pm.request("gunnchai", Permission.AI_CLOUD_EXPORT, explicit_user_grant=True)
    assert result["decision"] == Decision.DENY.value
