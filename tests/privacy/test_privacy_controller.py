"""Enforceable privacy controller — youth gates, DSAR, sensors, redaction."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.diagnostics_log import redact
from gunnchos_device_os.permissions_manager import Permission, PermissionsManager
from gunnchos_device_os.privacy.controller import PrivacyController
from gunnchos_device_os.privacy.store import PrivacyStore
from gunnchos_device_os.privacy_security_model import request_delete, request_export
from gunnchos_device_os.consent_policy import set_consent


def _ctrl(tmp_path: Path) -> PrivacyController:
    return PrivacyController(store=PrivacyStore(path=tmp_path / "store.json"))


def test_child_cannot_opt_in_telemetry(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("kid", "child")
    denied = ctrl.set_consent("kid", "opt_in_aggregate", "child")
    assert denied["denied"] is True
    assert denied["consent_state"] == "denied"
    tel = ctrl.record_telemetry("kid", {"action": "open_app"})
    assert tel["accepted"] is False


def test_child_sensors_require_guardian(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("kid", "child")
    for sensor in ("voice", "vision", "screen", "ring"):
        result = ctrl.request_sensor("kid", sensor, explicit_user_grant=True)
        assert result["decision"] == "deny"
        assert result["reason"] == "guardian_required"
    ring = ctrl.pair_ring("kid", "ring-dev-001", authenticated=True)
    assert ring["denied"] is True
    allowed = ctrl.request_sensor("kid", "voice", guardian_grant=True, explicit_user_grant=True)
    # child role allowlist still excludes microphone
    assert allowed["decision"] == "deny"
    assert allowed["reason"] == "outside_role_allowlist"


def test_adult_export_delete_wipes(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("ada", "adult")
    ctrl.set_consent("ada", "opt_in_aggregate", "adult")
    assert ctrl.record_telemetry("ada", {"action": "boot"})["accepted"] is True
    assert ctrl.store_ai_memory("ada", {"fact": "ofdm"})["stored"] is True
    assert ctrl.game_save("ada", "beatlink-party", {"score": 1})["saved"] is True
    assert ctrl.waike_progress("ada", "wireless_basics_101", 3)["pii"] is False
    export_path = tmp_path / "ada_export.json"
    exported = ctrl.export("ada", export_path)
    assert exported["mock"] is False
    assert export_path.exists()
    text = export_path.read_text(encoding="utf-8")
    assert "beatlink-party" in text
    deleted = ctrl.delete("ada", dest=tmp_path / "ada_delete.json")
    assert deleted["deleted"] is True
    assert deleted["wiped"]["telemetry"] >= 1
    again = ctrl.store.export_user("ada")
    assert again["deleted"] is True
    assert again["surfaces"]["telemetry"] == []


def test_ai_cloud_denied_for_youth_and_local_controller(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("kid", "child")
    cloud = ctrl.store_ai_memory("kid", {"prompt": "secret homework"}, cloud=True)
    assert cloud["denied"] is True
    local = ctrl.store_ai_memory("kid", {"topic": "photosynthesis"}, cloud=False)
    assert local["stored"] is True


def test_minimization_blocks_private_payload(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("ada", "adult")
    ctrl.set_consent("ada", "opt_in_aggregate", "adult")
    blocked = ctrl.record_telemetry("ada", {"private_payload": "nope"})
    assert blocked["accepted"] is False


def test_log_redaction_strips_email_in_values():
    out = redact({"note": "contact ada@example.com", "password": "x"})
    assert out["password"] == "[REDACTED]"
    assert "[REDACTED_EMAIL]" in out["note"]
    assert "ada@example.com" not in out["note"]


def test_request_export_delete_are_not_placeholders(tmp_path: Path, monkeypatch):
    from gunnchos_device_os import privacy_security_model as psm

    monkeypatch.setattr(psm, "DEFAULT_STORE", tmp_path / "store.json")
    exported = request_export("u1", dest=tmp_path / "u1.json")
    assert exported["mock"] is False
    assert exported["status"] == "exported"
    assert "placeholder" not in exported["path"]
    deleted = request_delete("u1", dest=tmp_path / "u1_del.json")
    assert deleted["mock"] is False
    assert deleted["status"] == "deleted"


def test_consent_child_opt_in_persists_denied():
    result = set_consent("child-1", "opt_in_research", "child")
    assert result["mock"] is False
    assert result["denied"] is True
    assert result["consent_state"] == "denied"


def test_child_role_allowlist():
    pm = PermissionsManager(role="child")
    cam = pm.request("app", Permission.CAMERA, explicit_user_grant=True)
    assert cam["decision"] == "deny"
    net = pm.request("app", Permission.NETWORK, explicit_user_grant=True)
    assert net["decision"] == "deny"
    files = pm.request("app", Permission.FILES_READ)
    assert files["decision"] == "allow"


def test_retention_drops_session_only_child_telemetry(tmp_path: Path):
    ctrl = _ctrl(tmp_path)
    ctrl.create_profile("kid", "child")
    # force-append telemetry despite policy for retention test
    ctrl.store.append("kid", "telemetry", {"event": {"action": "x"}}, profile_type="child")
    dropped = ctrl.apply_retention("kid")
    assert dropped["dropped"]["telemetry"] >= 1
    assert ctrl.store.export_user("kid")["surfaces"]["telemetry"] == []
