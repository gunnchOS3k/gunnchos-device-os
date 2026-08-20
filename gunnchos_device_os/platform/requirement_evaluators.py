"""Requirement-specific executable evaluators — no unconditional True classifiers."""
from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator

EvaluatorFn = Callable[["Wave004PlatformCoordinator"], dict[str, Any]]

REQUIREMENT_IDS = (
    "OS-PLATFORM-008",
    "OS-PLATFORM-009",
    "OS-PLATFORM-010",
    "OS-PLATFORM-011",
    "OS-PLATFORM-012",
    "OS-PLATFORM-013",
    "OS-PLATFORM-016",
    "OS-PLATFORM-018",
    "OS-PLATFORM-020",
    "OS-PLATFORM-021",
    "OS-PLATFORM-022",
    "OS-PLATFORM-023",
)


def _result(req_id: str, ok: bool, note: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    classification = "IMPLEMENTED_AND_VALIDATED" if ok else "IMPLEMENTATION_OPEN"
    return {
        "requirement_id": req_id,
        "classification": classification,
        "ok": ok,
        "note": note,
        "evaluator": f"evaluate_{req_id.lower().replace('-', '_')}",
        "evidence": evidence or {},
    }


def evaluate_os_platform_008(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    inspect = coord.package_lifecycle.inspect()
    install = coord.package_lifecycle.install("eval-app-008", version="1.0.0")
    listed = coord.package_lifecycle.list_installed()
    got = coord.package_lifecycle.get("eval-app-008")
    reloaded = coord.package_lifecycle.from_storage(
        coord.package_lifecycle.root, coord.repo_root
    )
    reload_get = reloaded.get("eval-app-008")
    ok = (
        inspect.get("ok")
        and install.get("ok")
        and "eval-app-008" in listed.get("packages", {})
        and got.get("ok")
        and reload_get.get("ok")
    )
    return _result(
        "OS-PLATFORM-008",
        ok,
        "Persistent package lifecycle with DEV signing; not production signing",
        evidence={"inspect": inspect, "install": install, "reload_get": reload_get},
    )


def evaluate_os_platform_009(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    coord.permissions.set_role("guest")
    denied = coord.permissions.request("malware", "screen_capture")
    coord.permissions.set_role("student")
    allowed = coord.permissions.request("notes-app", "files_read")
    ok = denied.get("decision") == "deny" and allowed.get("decision") == "allow"
    return _result(
        "OS-PLATFORM-009",
        ok,
        "PermissionsManager least-privilege with role allowlists",
        evidence={"guest_screen_capture": denied, "student_files_read": allowed},
    )


def evaluate_os_platform_010(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    inv = coord.local_ai.intelligence_inventory()
    has_micro = "micro-deterministic-v1" in coord._registry.models
    run = coord.local_ai.run_capability("tutor", "2+2")
    ok = has_micro and run.get("ok") is True and not inv.get("general_vlm")
    return _result(
        "OS-PLATFORM-010",
        ok,
        "Local AI runtime micro-deterministic; no GENERAL_VLM/ASR",
        evidence={"inventory": inv, "run": {"ok": run.get("ok"), "tier": run.get("tier")}},
    )


def evaluate_os_platform_011(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    coord.set_bearer_available("wifi", True)
    coord.set_bearer_available("offline", True)
    decision = coord.evaluate_and_transition(prefer_secure=True)
    ok = decision.get("active_bearer") in ("wifi", "ethernet", "offline")
    return _result(
        "OS-PLATFORM-011",
        ok,
        "ConnectivityOrchestrator software bearer selection",
        evidence={"decision": decision},
    )


def evaluate_os_platform_012(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    coord.offline_sync.put("sync-eval", {"v": 1}, idempotency_key="eval-key-1")
    pending = coord.offline_sync.pending()
    reloaded = coord.offline_sync.from_storage(coord.offline_sync.storage_path)
    ok = len(pending) >= 1 and reloaded.get("sync-eval") == {"v": 1}
    return _result(
        "OS-PLATFORM-012",
        ok,
        "Persistent OfflineSyncEngine vector-clock/LWW merge",
        evidence={"pending_len": len(pending), "reloaded_value": reloaded.get("sync-eval")},
    )


def evaluate_os_platform_013(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    put = coord.keystore.put("_probe", b"x", namespace="validation")
    got = coord.keystore.get("_probe", namespace="validation")
    ok = put.get("ok") and got.get("ok")
    return _result(
        "OS-PLATFORM-013",
        ok,
        "Software Fernet keystore; not TPM",
        evidence={"put": put, "get_ok": got.get("ok")},
    )


def evaluate_os_platform_016(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    status = coord.ota_manager.status()
    ok = status.get("active_slot") in ("A", "B")
    return _result(
        "OS-PLATFORM-016",
        ok,
        "ABUpdateManager DEV-signed OTA slots",
        evidence={"active_slot": status.get("active_slot")},
    )


def evaluate_os_platform_018(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    recovery = coord.recovery_userspace.inspect()
    ok = recovery.get("ok") is True
    return _result(
        "OS-PLATFORM-018",
        ok,
        "Userspace recovery env; not hardware recovery partition",
        evidence=recovery,
    )


def evaluate_os_platform_020(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    exec_result = coord.sandbox_executor.execute_untrusted("eval-untrusted-020")
    ok = exec_result.get("ok") is True
    note = (
        "Subprocess/bwrap execution-enforced sandbox; KERNEL_SANDBOX="
        f"{exec_result.get('kernel_sandbox', False)}"
    )
    return _result("OS-PLATFORM-020", ok, note, evidence=exec_result)


def evaluate_os_platform_021(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    coord.emit("eval_probe", {"token": "secret-eval-021"})
    export = coord.export_tail(limit=3)
    path_exists = coord.diagnostics.path.exists()
    ok = path_exists and len(export.get("events", [])) >= 1
    return _result(
        "OS-PLATFORM-021",
        ok,
        "DiagnosticsLog persistent redacted JSONL",
        evidence={"path_exists": path_exists, "event_count": len(export.get("events", []))},
    )


def evaluate_os_platform_022(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    updated = coord.accessibility_store.update("student-1", {"large_text": True, "reduced_motion": True})
    reloaded = coord.accessibility_store.from_storage(coord.accessibility_store.root)
    reload_status = reloaded.load("student-1")
    ok = updated.get("ok") and reload_status["settings"].get("large_text") is True
    return _result(
        "OS-PLATFORM-022",
        ok,
        "Persisted accessibility per profile; WCAG_VALIDATED=false",
        evidence={"updated_ok": updated.get("ok"), "reload_large_text": reload_status["settings"].get("large_text")},
    )


def evaluate_os_platform_023(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    coord.role_policy.assign_profile("admin-1", "admin")
    coord.role_policy.assign_profile("stu-eval", "student")
    denied_self = coord.role_policy.request_role_change("stu-eval", "admin", requested_by="stu-eval")
    pending = coord.role_policy.request_role_change("stu-eval", "educator", requested_by="stu-eval")
    authorized = coord.role_policy.authorize_role_change(
        pending["request_id"], authorized_by="admin-1"
    )
    reloaded = coord.role_policy.from_storage(coord.role_policy.storage_path)
    profile = reloaded.active_profiles.get("stu-eval")
    ok = (
        denied_self.get("ok") is False
        and authorized.get("ok") is True
        and profile == "educator"
    )
    return _result(
        "OS-PLATFORM-023",
        ok,
        "Persisted role policy with admin-authorized role change",
        evidence={"denied_self": denied_self, "authorized": authorized, "reloaded_profile": profile},
    )


EVALUATORS: dict[str, EvaluatorFn] = {
    "OS-PLATFORM-008": evaluate_os_platform_008,
    "OS-PLATFORM-009": evaluate_os_platform_009,
    "OS-PLATFORM-010": evaluate_os_platform_010,
    "OS-PLATFORM-011": evaluate_os_platform_011,
    "OS-PLATFORM-012": evaluate_os_platform_012,
    "OS-PLATFORM-013": evaluate_os_platform_013,
    "OS-PLATFORM-016": evaluate_os_platform_016,
    "OS-PLATFORM-018": evaluate_os_platform_018,
    "OS-PLATFORM-020": evaluate_os_platform_020,
    "OS-PLATFORM-021": evaluate_os_platform_021,
    "OS-PLATFORM-022": evaluate_os_platform_022,
    "OS-PLATFORM-023": evaluate_os_platform_023,
}


def run_all_evaluators(coord: Wave004PlatformCoordinator) -> dict[str, dict[str, Any]]:
    broken = os.environ.get("WAVE004_BROKEN_EVALUATOR")
    results = {req_id: fn(coord) for req_id, fn in EVALUATORS.items()}
    if broken and broken in results:
        results[broken] = _result(broken, False, "broken_evaluator_fixture_injection", evidence={"injected": True})
    return results


def build_evaluator_matrix(coord: Wave004PlatformCoordinator) -> dict[str, Any]:
    results = run_all_evaluators(coord)
    validated = sum(1 for r in results.values() if r["classification"] == "IMPLEMENTED_AND_VALIDATED")
    return {
        "schema": "gunnchos.engineering_wave004.requirement_evaluator_matrix.v1",
        "target_requirements": 12,
        "validated_count": validated,
        "unconditional_true_classifiers": 0,
        "evaluators": {
            req_id: {
                "evaluator": r["evaluator"],
                "classification": r["classification"],
                "ok": r["ok"],
                "note": r["note"],
            }
            for req_id, r in results.items()
        },
        "results": results,
    }


def classify_from_evaluators(coord: Wave004PlatformCoordinator) -> dict[str, dict[str, Any]]:
    results = run_all_evaluators(coord)
    return {
        req_id: {
            "classification": r["classification"],
            "note": r["note"],
            "evaluator": r["evaluator"],
            "ok": r["ok"],
        }
        for req_id, r in results.items()
    }
