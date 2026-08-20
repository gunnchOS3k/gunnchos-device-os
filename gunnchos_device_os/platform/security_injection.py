"""Security abuse and failure injection cases for Wave 004."""
from __future__ import annotations

import copy
import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator


INJECTION_CASES = (
    "tampered_package_signature",
    "revoked_signing_key",
    "permission_escalation",
    "sandbox_escape_attempt",
    "keystore_ciphertext_tamper",
    "offline_sync_conflict_storm",
    "ota_anti_rollback_attack",
    "ota_interrupted_update",
    "recovery_unverified_slot_select",
    "diagnostics_log_injection",
    "role_policy_guest_sensitive_grant",
    "connectivity_bearer_spoof",
    "package_tamper_after_install",
    "sync_queue_replay_idempotency",
    "sandbox_host_escape_script",
    "accessibility_profile_corruption",
    "role_self_escalation_attempt",
    "role_unauthorized_admin_grant",
)


def run_security_injections(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    cases.append(_tampered_package_signature(coord))
    cases.append(_revoked_signing_key(coord))
    cases.append(_permission_escalation(coord))
    cases.append(_sandbox_escape_attempt(coord))
    cases.append(_keystore_ciphertext_tamper(coord))
    cases.append(_offline_sync_conflict_storm(coord))
    cases.append(_ota_anti_rollback_attack(coord))
    cases.append(_ota_interrupted_update(coord))
    cases.append(_recovery_unverified_slot_select(coord))
    cases.append(_diagnostics_log_injection(coord))
    cases.append(_role_policy_guest_sensitive_grant(coord))
    cases.append(_connectivity_bearer_spoof(coord))
    cases.append(_package_tamper_after_install(coord))
    cases.append(_sync_queue_replay_idempotency(coord))
    cases.append(_sandbox_host_escape_script(coord))
    cases.append(_accessibility_profile_corruption(coord))
    cases.append(_role_self_escalation_attempt(coord))
    cases.append(_role_unauthorized_admin_grant(coord))
    blocked = sum(1 for c in cases if c.get("blocked") is True)
    return {
        "schema": "gunnchos.engineering_wave004.security_injection.v1",
        "total": len(cases),
        "blocked": blocked,
        "leaked": sum(1 for c in cases if c.get("blocked") is False),
        "ok": blocked == len(cases),
        "cases": cases,
    }


def _tampered_package_signature(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    signed = coord.build_signed_package()
    tampered = copy.deepcopy(signed["signed_apps"])
    tampered["digest_sha256"] = "0" * 64
    verify = coord.verify_signed_package(tampered)
    return {"case": "tampered_package_signature", "blocked": verify is False, "verify": verify}


def _revoked_signing_key(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    meta = coord.build_ota_metadata(to_version="9.9.9")
    fp = meta.get("signing_key_fingerprint", "")
    coord.ota_revoke_key(fp)
    stage = coord.ota_manager.stage_update(meta)
    return {"case": "revoked_signing_key", "blocked": stage.get("ok") is False, "error": stage.get("error")}


def _permission_escalation(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.permissions.set_role("guest")
    result = coord.permissions.request("malware", "screen_capture")
    blocked = result.get("decision") == "deny"
    return {"case": "permission_escalation", "blocked": blocked, "result": result}


def _sandbox_escape_attempt(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.sandbox.create_profile("evil", "untrusted")
    attempt = coord.sandbox.check_capability("evil", "system_service")
    return {
        "case": "sandbox_escape_attempt",
        "blocked": attempt.get("decision") == "deny",
        "attempt": attempt,
    }


def _keystore_ciphertext_tamper(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.keystore.put("secret", b"payload", namespace="test")
    rec = coord.keystore.blobs.get("test:secret")
    if rec:
        rec["ciphertext"] = rec["ciphertext"][:-4] + "XXXX"
        coord.keystore.store_path.write_text(json.dumps(coord.keystore.blobs), encoding="utf-8")
    got = coord.keystore.get("secret", namespace="test")
    return {"case": "keystore_ciphertext_tamper", "blocked": got.get("ok") is False, "error": got.get("error")}


def _offline_sync_conflict_storm(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    local = coord.offline_sync
    remote = type(local)(replica_id="remote-replica", storage_path=None)
    local.put("k1", {"v": 1})
    remote.put("k1", {"v": 2})
    merged = local.apply_remote(remote.pending()[0])
    return {
        "case": "offline_sync_conflict_storm",
        "blocked": merged.get("status") in ("resolved", "synced", "conflict"),
        "merge": merged,
    }


def _ota_anti_rollback_attack(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    bump = coord.build_ota_metadata(to_version="1.0.5")
    staged = coord.ota_manager.stage_update(bump)
    if staged.get("ok"):
        coord.ota_manager.commit_boot(staged["target_slot"], boot_succeeds=True)
    meta = coord.build_ota_metadata(to_version="0.0.1", anti_rollback_counter=0)
    stage = coord.ota_manager.stage_update(meta)
    return {
        "case": "ota_anti_rollback_attack",
        "blocked": stage.get("ok") is False,
        "error": stage.get("error"),
    }


def _ota_interrupted_update(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    meta = coord.build_ota_metadata(to_version="1.1.0")
    stage = coord.ota_manager.stage_update(meta, simulate_crash_before_commit=True)
    recover = coord.ota_manager.recover_from_interrupted_update()
    return {
        "case": "ota_interrupted_update",
        "blocked": recover.get("ok") is True,
        "stage": stage,
        "recover": recover,
    }


def _recovery_unverified_slot_select(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    result = coord.recovery_userspace.select_boot_slot(require_verified=True, corrupt_active=True)
    return {
        "case": "recovery_unverified_slot_select",
        "blocked": result.get("selected_verified") is True or result.get("ok") is False,
        "result": result,
    }


def _diagnostics_log_injection(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    event = coord.emit(
        "injection_test",
        {"message": "<script>alert(1)</script>", "password": "leak"},
    )
    export = coord.export_tail(limit=1)
    leaked = any("leak" in str(row) for row in export.get("events", []))
    return {"case": "diagnostics_log_injection", "blocked": not leaked and event.get("redacted"), "event": event}


def _role_policy_guest_sensitive_grant(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.role_policy.assign_profile("guest-1", "guest")
    result = coord.role_policy.check_app_permission("guest-1", "spy", "screen_capture")
    return {
        "case": "role_policy_guest_sensitive_grant",
        "blocked": result.get("decision") == "deny",
        "result": result,
    }


def _connectivity_bearer_spoof(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.set_bearer_available("wifi", False)
    coord.set_bearer_available("ethernet", False)
    coord.inject_spoofed_bearer("cellular", available=True, security_score=0.01)
    decision = coord.evaluate_and_transition(prefer_secure=True)
    blocked = decision.get("active_bearer") != "cellular"
    return {
        "case": "connectivity_bearer_spoof",
        "blocked": blocked,
        "decision": decision,
    }


def _package_tamper_after_install(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    install = coord.package_lifecycle.install("tamper-target")
    manifest_path = coord.package_lifecycle.installs_dir / "tamper-target" / "signed_manifest.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["digest_sha256"] = "deadbeef"
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
    verify = coord.package_lifecycle.get("tamper-target")
    return {
        "case": "package_tamper_after_install",
        "blocked": verify.get("ok") is False,
        "install_ok": install.get("ok"),
    }


def _sync_queue_replay_idempotency(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    first = coord.offline_sync.put("replay-key", {"n": 1}, idempotency_key="replay-001")
    second = coord.offline_sync.put("replay-key", {"n": 2}, idempotency_key="replay-001")
    blocked = first.version == second.version and first.value == second.value
    return {"case": "sync_queue_replay_idempotency", "blocked": blocked, "versions": (first.version, second.version)}


def _sandbox_host_escape_script(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    result = coord.sandbox_executor.execute_untrusted("escape-tester", app_class="untrusted")
    return {
        "case": "sandbox_host_escape_script",
        "blocked": result.get("ok") is True,
        "execution": {"ok": result.get("ok"), "backend": result.get("backend")},
    }


def _accessibility_profile_corruption(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    store_path = coord.accessibility_store._store_path()
    coord.accessibility_store.update("corrupt-me", {"large_text": True})
    store_path.write_text("{not-valid-json", encoding="utf-8")
    reloaded = coord.accessibility_store.from_storage(coord.accessibility_store.root)
    status = reloaded.load("corrupt-me")
    blocked = reloaded.corrupt is True and status.get("ok") is False
    return {"case": "accessibility_profile_corruption", "blocked": blocked, "status": status}


def _role_self_escalation_attempt(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.role_policy.assign_profile("escalator", "student")
    result = coord.role_policy.request_role_change("escalator", "admin", requested_by="escalator")
    return {
        "case": "role_self_escalation_attempt",
        "blocked": result.get("ok") is False,
        "error": result.get("error"),
    }


def _role_unauthorized_admin_grant(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    coord.role_policy.assign_profile("student-x", "student")
    coord.role_policy.assign_profile("student-y", "student")
    req = coord.role_policy.request_role_change("student-x", "educator", requested_by="student-x")
    denied = coord.role_policy.authorize_role_change(req["request_id"], authorized_by="student-y")
    return {
        "case": "role_unauthorized_admin_grant",
        "blocked": denied.get("ok") is False,
        "error": denied.get("error"),
    }
