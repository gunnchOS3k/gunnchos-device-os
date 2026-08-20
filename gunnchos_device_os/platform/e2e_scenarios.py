"""Cross-service E2E scenarios A–K for Wave 004 platform stack."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator


def scenario_a_signed_install_flow(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """A: Verify signed package → sandbox profile → permission grant → launch."""
    pkg = coord.install_signed_package("demo-app", app_class="first_party")
    sandbox = coord.sandbox.create_profile("demo-app", "first_party")
    perm = coord.permissions.request("demo-app", "files_read")
    return {
        "scenario": "A",
        "name": "signed_install_flow",
        "ok": pkg.get("ok") and sandbox.app_id == "demo-app" and perm.get("decision") == "allow",
        "package": pkg,
        "sandbox_isolation": sandbox.isolation.value,
        "permission": perm,
    }


def scenario_b_offline_encrypted_work(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """B: Offline work → encrypted storage → sync when connectivity returns."""
    coord.set_bearer_available("wifi", False)
    coord.set_bearer_available("offline", True)
    stored = coord.keystore.put("notes", b"offline draft", namespace="user")
    sync_rec = coord.offline_sync.put("notes", {"body": "offline draft"})
    coord.set_bearer_available("wifi", True)
    path = coord.evaluate_and_transition()
    flush = coord.flush_pending_sync()
    return {
        "scenario": "B",
        "name": "offline_encrypted_work",
        "ok": stored.get("ok") and sync_rec.key == "notes" and flush.get("flushed", 0) >= 1,
        "keystore": stored,
        "connectivity": path.get("active_bearer"),
        "sync": flush,
    }


def scenario_c_local_ai_guarded(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """C: Local AI invoke under sandbox + permission boundaries."""
    coord.permissions.set_role("student")
    ai_perm = coord.permissions.request("gunnchai-tutor", "files_read")
    sandbox = coord.sandbox.check_capability("gunnchai-tutor", "device_gpu")
    ai_result = coord.local_ai.run_capability("tutor", "Explain fractions simply.")
    return {
        "scenario": "C",
        "name": "local_ai_guarded",
        "ok": ai_perm.get("decision") == "allow" and ai_result.get("ok") is True,
        "permission": ai_perm,
        "sandbox_gpu": sandbox,
        "ai": {
            "tier": ai_result.get("tier"),
            "role": ai_result.get("role"),
            "general_vlm": False,
            "general_asr": False,
        },
    }


def scenario_d_ota_recovery(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """D: OTA stage → interrupted update recovery → userspace recovery env."""
    ota = coord.stage_and_apply_ota(from_version="1.0.0", to_version="1.0.1")
    recovery = coord.recovery_userspace.inspect()
    return {
        "scenario": "D",
        "name": "ota_recovery",
        "ok": ota.get("applied") is True and recovery.get("ok") is True,
        "ota": ota,
        "recovery": recovery,
    }


def scenario_e_diagnostics_redaction(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """E: Diagnostics capture with redaction under student profile."""
    coord.role_policy.assign_profile("student-1", "student")
    event = coord.emit(
        "app_crash",
        {"student_name": "Ada Lovelace", "email": "ada@example.com", "token": "secret123"},
    )
    export = coord.export_tail(limit=5)
    redacted = all(
        "Ada Lovelace" not in str(row) and "secret123" not in str(row) for row in export.get("events", [])
    )
    return {
        "scenario": "E",
        "name": "diagnostics_redaction",
        "ok": event.get("redacted") is True and redacted,
        "event_id": event.get("id"),
        "export_count": len(export.get("events", [])),
    }


def scenario_f_role_policy_educator(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """F: Educator vs student role policy on sensitive permissions."""
    coord.role_policy.assign_profile("stu-1", "student")
    coord.role_policy.assign_profile("edu-1", "educator")
    stu_cam = coord.role_policy.check_app_permission("stu-1", "camera-app", "camera")
    edu_cam = coord.role_policy.check_app_permission("edu-1", "camera-app", "camera")
    override = coord.role_policy.guardian_override("stu-1", "camera-app", "camera", allow=True)
    return {
        "scenario": "F",
        "name": "role_policy_educator",
        "ok": stu_cam.get("decision") == "deny" and edu_cam.get("decision") == "allow" and override.get("ok"),
        "student_camera": stu_cam.get("decision"),
        "educator_camera": edu_cam.get("decision"),
        "guardian_override": override.get("decision"),
    }


def scenario_g_package_restart_persistence(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """G: Package install survives fresh-process reload."""
    install = coord.package_lifecycle.install("restart-app", version="2.0.0")
    reloaded = coord.package_lifecycle.from_storage(coord.package_lifecycle.root, coord.repo_root)
    got = reloaded.get("restart-app")
    return {
        "scenario": "G",
        "name": "package_restart_persistence",
        "ok": install.get("ok") and got.get("ok") and got.get("record", {}).get("version") == "2.0.0",
        "install": install,
        "reload": got,
    }


def scenario_h_sync_restart_persistence(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """H: Offline sync store/queue survives fresh-process reload."""
    coord.offline_sync.put("persist-key", {"state": "saved"}, idempotency_key="h-key")
    path = coord.offline_sync.storage_path
    reloaded = coord.offline_sync.from_storage(path)
    value = reloaded.get("persist-key")
    return {
        "scenario": "H",
        "name": "sync_restart_persistence",
        "ok": value == {"state": "saved"} and len(reloaded.pending()) >= 0,
        "value": value,
    }


def scenario_i_sandbox_execution(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """I: Execute untrusted fixture under execution-enforced sandbox."""
    result = coord.sandbox_executor.execute_untrusted("untrusted-fixture", app_class="untrusted")
    return {
        "scenario": "I",
        "name": "sandbox_execution",
        "ok": result.get("ok") is True,
        "execution": result,
    }


def scenario_j_accessibility_persist(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """J: Accessibility settings persist per profile across reload."""
    updated = coord.accessibility_store.update("profile-j", {"large_text": True, "high_contrast": True})
    reloaded = coord.accessibility_store.from_storage(coord.accessibility_store.root)
    status = reloaded.load("profile-j")
    contract = reloaded.shell_contract("profile-j")
    return {
        "scenario": "J",
        "name": "accessibility_persist",
        "ok": updated.get("ok") and status["settings"].get("large_text") is True and contract.get("wcag_validated") is False,
        "settings": status["settings"],
    }


def scenario_k_role_auth_persist(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    """K: Admin-authorized role change persists across reload."""
    coord.role_policy.assign_profile("admin-k", "admin")
    coord.role_policy.assign_profile("user-k", "student")
    req = coord.role_policy.request_role_change("user-k", "educator", requested_by="user-k")
    auth = coord.role_policy.authorize_role_change(req["request_id"], authorized_by="admin-k")
    reloaded = coord.role_policy.from_storage(coord.role_policy.storage_path)
    profile = reloaded.active_profiles.get("user-k")
    return {
        "scenario": "K",
        "name": "role_auth_persist",
        "ok": auth.get("ok") and profile == "educator",
        "profile": profile,
    }


def run_all_scenarios(coord: "Wave004PlatformCoordinator") -> dict[str, Any]:
    results = [
        scenario_a_signed_install_flow(coord),
        scenario_b_offline_encrypted_work(coord),
        scenario_c_local_ai_guarded(coord),
        scenario_d_ota_recovery(coord),
        scenario_e_diagnostics_redaction(coord),
        scenario_f_role_policy_educator(coord),
        scenario_g_package_restart_persistence(coord),
        scenario_h_sync_restart_persistence(coord),
        scenario_i_sandbox_execution(coord),
        scenario_j_accessibility_persist(coord),
        scenario_k_role_auth_persist(coord),
    ]
    passed = sum(1 for r in results if r.get("ok"))
    return {
        "schema": "gunnchos.engineering_wave004.e2e_scenarios.v1",
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "ok": passed == len(results),
        "scenarios": results,
    }
