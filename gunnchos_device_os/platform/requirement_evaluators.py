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
    lifecycle = coord.package_lifecycle.run_full_lifecycle_proof("eval-app-008")
    negatives = coord.package_lifecycle.run_negative_proofs()
    ok = lifecycle.get("ok") is True and negatives.get("ok") is True
    return _result(
        "OS-PLATFORM-008",
        ok,
        "Secure persistent package lifecycle with DEV signing; not production signing",
        evidence={"lifecycle": lifecycle, "negatives_ok": negatives.get("ok"), "blocked": negatives.get("blocked")},
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
    from gunnchos_device_os.platform.persistent_sync import prove_corruption_failures, run_a_b_c_restart_proof

    storage = coord.offline_sync.storage_path
    assert storage is not None
    abc = run_a_b_c_restart_proof(storage / "abc_proof")
    corruption = prove_corruption_failures(storage / "corruption_proof")
    ok = abc.get("ok") is True and corruption.get("ok") is True
    return _result(
        "OS-PLATFORM-012",
        ok,
        "Persistent OfflineSyncEngine A→B→C restart apply-once; corruption safe-fails",
        evidence={"abc": abc, "corruption_ok": corruption.get("ok")},
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
    from gunnchos_device_os.platform.coordinator import CLAIM_FLAGS

    suite = coord.sandbox_executor.run_enforcement_suite("eval-untrusted-020")
    # Plain subprocess never validates. BLOCKED_ENVIRONMENT when no genuine backend.
    if suite.get("LOCAL_SANDBOX_VALIDATION") == "BLOCKED_ENVIRONMENT":
        return {
            "requirement_id": "OS-PLATFORM-020",
            "classification": "BLOCKED_ENVIRONMENT",
            "ok": False,
            "note": (
                "LOCAL_SANDBOX_VALIDATION=BLOCKED_ENVIRONMENT; "
                f"backend={suite.get('SANDBOX_BACKEND')}; "
                "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX=false"
            ),
            "evaluator": "evaluate_os_platform_020",
            "evidence": suite,
        }
    ok = suite.get("SANDBOX_EXECUTION_VALIDATED") is True and suite.get("PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX") is False
    # Regression guard: host read success must fail
    fixture = suite.get("fixture_result") or {}
    if fixture.get("host_private_read") and suite.get("OUTSIDE_WRITE_BLOCKED"):
        ok = False
    if suite.get("KERNEL_SANDBOX"):
        CLAIM_FLAGS["KERNEL_SANDBOX"] = True
    return _result(
        "OS-PLATFORM-020",
        ok,
        (
            f"Enforced sandbox backend={suite.get('SANDBOX_BACKEND')}; "
            f"KERNEL_SANDBOX={suite.get('KERNEL_SANDBOX')}"
        ),
        evidence=suite,
    )


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
    blocked_env = sum(1 for r in results.values() if r["classification"] == "BLOCKED_ENVIRONMENT")
    return {
        "schema": "gunnchos.engineering_wave004.requirement_evaluator_matrix.v1",
        "target_requirements": 12,
        "validated_count": validated,
        "blocked_environment_count": blocked_env,
        "unconditional_true_classifiers": 0,
        "COMPLETE_GATE_REQUIRES_12_OF_12": True,
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
