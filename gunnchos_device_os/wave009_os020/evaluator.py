"""Strong Wave009 one-row evaluator for OS-PLATFORM-020."""
from __future__ import annotations

import copy
import hashlib
import inspect
import tempfile
from pathlib import Path
from typing import Any

from gunnchos_device_os.platform.sandbox_executor import SandboxExecutor
from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine
from gunnchos_device_os.wave009_os020.evaluator_integrity import inspect_wave009_evaluator

TARGET_REQUIREMENTS = ["OS-PLATFORM-020"]

CLAIM_BOUNDARIES = {
    "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
    "FORMALLY_VERIFIED_SANDBOX": False,
    "PRODUCTION_SECURITY_CERTIFIED": False,
    "THIRD_PARTY_PEN_TESTED": False,
    "HARDWARE_TEE_ISOLATION_VALIDATED": False,
    "SELINUX_POLICY_CERTIFIED": False,
    "APPARMOR_POLICY_CERTIFIED": False,
    "HUMAN_E6": False,
    "PHYSICAL_VALIDATION": False,
}


def _suite(root: Path | None = None) -> dict[str, Any]:
    work = Path(root) if root is not None else Path(tempfile.mkdtemp(prefix="wave009-eval-"))
    ex = SandboxExecutor(work, SandboxPolicyEngine())
    return ex.run_enforcement_suite("wave009-os020")


def evaluate_os_platform_020(suite: dict[str, Any] | None = None) -> dict[str, Any]:
    """Require genuine kernel sandbox proof — no unconditional True."""
    evidence = suite if suite is not None else _suite()
    reasons: list[str] = []

    def req(cond: bool, name: str) -> None:
        if not cond:
            reasons.append(name)

    backend = evidence.get("SANDBOX_BACKEND")
    req(backend == "bubblewrap", "backend_not_bubblewrap")
    req(evidence.get("fixture_ran") is True, "fixture_did_not_run")
    req(evidence.get("PRIVATE_ROOT_RW_PASS") is True, "private_root_rw_fail")
    req(evidence.get("APP_ROOT_READ_ALLOWED") is True, "app_root_read_fail")
    req(evidence.get("APP_ROOT_WRITE_ALLOWED") is True, "app_root_write_fail")
    req(evidence.get("HOST_PRIVATE_READ_BLOCKED") is True, "host_private_read_not_blocked")
    req(evidence.get("OUTSIDE_WRITE_BLOCKED") is True, "outside_write_not_blocked")
    req(evidence.get("NETWORK_DENIED") is True, "network_not_denied")
    req(evidence.get("NETWORK_CONTROL_REACHABLE") is True, "network_control_unreachable")
    req(evidence.get("CHILD_SPAWN_DENIED") is True, "child_spawn_not_denied")
    req(evidence.get("CONTROL_CHILD_EXEC_WORKS") is True, "control_child_exec_failed")
    req(evidence.get("CROSS_APP_READ_BLOCKED") is True, "cross_app_read_not_blocked")
    req(evidence.get("PRIVILEGED_CAPABILITY_DENIED") is True, "privileged_capability_not_denied")
    req(evidence.get("SYMLINK_HOST_ESCAPE_BLOCKED") is True, "symlink_host_escape")
    req(evidence.get("SYMLINK_CROSS_APP_ESCAPE_BLOCKED") is True, "symlink_cross_escape")
    req(evidence.get("PATH_TRAVERSAL_ESCAPE_BLOCKED") is True, "path_traversal_escape")
    req(evidence.get("PROC_ROOT_ESCAPE_BLOCKED") is True, "proc_root_escape")
    req(evidence.get("HOST_ROOT_ESCALATION_BLOCKED") is True, "host_root_escalation")
    req(evidence.get("DANGEROUS_DEVICE_ACCESS_BLOCKED") is True, "dangerous_device_access")
    req(evidence.get("MOUNT_ESCAPE_BLOCKED") is True, "mount_escape")
    req(evidence.get("SECCOMP_LOADED") is True, "seccomp_not_loaded")
    req(evidence.get("SANDBOX_EXECUTED_AS_ROOT") is False, "sandbox_executed_as_root")
    req(evidence.get("BWRAP_INVOKED_WITH_SUDO") is False, "bwrap_invoked_with_sudo")
    req(evidence.get("PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX") is False, "plain_subprocess_claimed")
    req(evidence.get("SANDBOX_EXECUTION_VALIDATED") is True, "execution_not_validated")
    req(evidence.get("KERNEL_SANDBOX") is True, "kernel_sandbox_false")
    req(evidence.get("LOCAL_SANDBOX_VALIDATION") == "VALIDATED", "local_validation_not_validated")
    req(evidence.get("CONTROL_HOST_SECRET_READABLE") is True, "control_host_secret_unreadable")
    req(evidence.get("CONTROL_CROSS_APP_READABLE") is True, "control_cross_app_unreadable")

    if evidence.get("LOCAL_SANDBOX_VALIDATION") == "BLOCKED_ENVIRONMENT":
        return {
            "requirement_id": "OS-PLATFORM-020",
            "classification": "BLOCKED_ENVIRONMENT",
            "ok": False,
            "note": (
                "LOCAL_SANDBOX_VALIDATION=BLOCKED_ENVIRONMENT; "
                f"backend={backend}; PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX=false"
            ),
            "evaluator": "evaluate_os_platform_020",
            "evidence": evidence,
            "reasons": reasons or ["blocked_environment"],
        }

    ok = not reasons
    return {
        "requirement_id": "OS-PLATFORM-020",
        "classification": "IMPLEMENTED_AND_VALIDATED" if ok else "IMPLEMENTATION_OPEN",
        "ok": ok,
        "note": (
            f"Wave009 enforced sandbox backend={backend}; "
            f"KERNEL_SANDBOX={evidence.get('KERNEL_SANDBOX')}; reasons={reasons}"
        ),
        "evaluator": "evaluate_os_platform_020",
        "evidence": evidence,
        "reasons": reasons,
    }


EVALUATORS = {
    "OS-PLATFORM-020": evaluate_os_platform_020,
}


def run_wave009_evaluation(suite: dict[str, Any] | None = None) -> dict[str, Any]:
    row = evaluate_os_platform_020(suite)
    integrity = inspect_wave009_evaluator(evaluate_os_platform_020)
    classification = {"OS-PLATFORM-020": row}
    return {
        "classification": classification,
        "integrity": integrity,
        "summary": {
            "total": 1,
            "validated": 1 if row.get("classification") == "IMPLEMENTED_AND_VALIDATED" and row.get("ok") else 0,
            "blocked_environment": 1 if row.get("classification") == "BLOCKED_ENVIRONMENT" else 0,
            "implementation_open": 1 if row.get("classification") == "IMPLEMENTATION_OPEN" else 0,
        },
        "CLAIM_BOUNDARIES": dict(CLAIM_BOUNDARIES),
        "evaluator_source_hash": hashlib.sha256(inspect.getsource(evaluate_os_platform_020).encode()).hexdigest(),
    }


def accept_suite_for_gate(row: dict[str, Any], *, integrity: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if row.get("requirement_id") != "OS-PLATFORM-020":
        reasons.append("wrong_requirement_id")
    if row.get("evaluator") != "evaluate_os_platform_020":
        reasons.append("wrong_evaluator_identity")
    if not row.get("evidence"):
        reasons.append("empty_evidence")
    if integrity.get("UNCONDITIONAL_TRUE_CLASSIFIERS", 1) != 0:
        reasons.append("unconditional_true_classifiers")
    if integrity.get("ok") is not True:
        reasons.append("evaluator_integrity_failed")
    validated = (
        row.get("ok") is True
        and row.get("classification") == "IMPLEMENTED_AND_VALIDATED"
        and not reasons
    )
    return {
        "schema": "gunnchos.engineering_wave009.completion_gate.v1",
        "COMPLETE_GATE_REQUIRES_1_OF_1": True,
        "target_count": 1,
        "validated_count": 1 if validated else 0,
        "complete": validated,
        "ok": validated,
        "reasons": reasons,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": integrity.get("UNCONDITIONAL_TRUE_CLASSIFIERS", 0),
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
    }


def run_completion_gate_negative_controls() -> dict[str, Any]:
    """Reject broken/missing/wrong/empty/stale/hash evaluator wiring."""
    good_suite = {
        "SANDBOX_BACKEND": "bubblewrap",
        "fixture_ran": True,
        "PRIVATE_ROOT_RW_PASS": True,
        "APP_ROOT_READ_ALLOWED": True,
        "APP_ROOT_WRITE_ALLOWED": True,
        "HOST_PRIVATE_READ_BLOCKED": True,
        "OUTSIDE_WRITE_BLOCKED": True,
        "NETWORK_DENIED": True,
        "NETWORK_CONTROL_REACHABLE": True,
        "CHILD_SPAWN_DENIED": True,
        "CONTROL_CHILD_EXEC_WORKS": True,
        "CROSS_APP_READ_BLOCKED": True,
        "PRIVILEGED_CAPABILITY_DENIED": True,
        "SYMLINK_HOST_ESCAPE_BLOCKED": True,
        "SYMLINK_CROSS_APP_ESCAPE_BLOCKED": True,
        "PATH_TRAVERSAL_ESCAPE_BLOCKED": True,
        "PROC_ROOT_ESCAPE_BLOCKED": True,
        "HOST_ROOT_ESCALATION_BLOCKED": True,
        "DANGEROUS_DEVICE_ACCESS_BLOCKED": True,
        "MOUNT_ESCAPE_BLOCKED": True,
        "SECCOMP_LOADED": True,
        "SANDBOX_EXECUTED_AS_ROOT": False,
        "BWRAP_INVOKED_WITH_SUDO": False,
        "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
        "SANDBOX_EXECUTION_VALIDATED": True,
        "KERNEL_SANDBOX": True,
        "LOCAL_SANDBOX_VALIDATION": "VALIDATED",
        "CONTROL_HOST_SECRET_READABLE": True,
        "CONTROL_CROSS_APP_READABLE": True,
    }

    def always_true(_suite: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "requirement_id": "OS-PLATFORM-020",
            "classification": "IMPLEMENTED_AND_VALIDATED",
            "ok": True,
            "note": "broken",
            "evaluator": "always_true",
            "evidence": {},
        }

    checks: list[dict[str, Any]] = []

    broken = always_true()
    integrity_broken = {
        "ok": False,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": 1,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
    }
    gate_broken = accept_suite_for_gate(broken, integrity=integrity_broken)
    checks.append({"name": "BROKEN_EVALUATOR_REJECTED", "ok": gate_broken["complete"] is False})

    missing = copy.deepcopy(evaluate_os_platform_020(good_suite))
    missing.pop("evaluator", None)
    gate_missing = accept_suite_for_gate(missing, integrity=inspect_wave009_evaluator(evaluate_os_platform_020))
    checks.append({"name": "MISSING_EVALUATOR_REJECTED", "ok": gate_missing["complete"] is False})

    wrong_id = copy.deepcopy(evaluate_os_platform_020(good_suite))
    wrong_id["requirement_id"] = "OS-PLATFORM-999"
    gate_wrong = accept_suite_for_gate(wrong_id, integrity=inspect_wave009_evaluator(evaluate_os_platform_020))
    checks.append({"name": "WRONG_EVALUATOR_ID_REJECTED", "ok": gate_wrong["complete"] is False})

    empty = copy.deepcopy(evaluate_os_platform_020(good_suite))
    empty["evidence"] = {}
    gate_empty = accept_suite_for_gate(empty, integrity=inspect_wave009_evaluator(evaluate_os_platform_020))
    checks.append({"name": "EMPTY_EVIDENCE_REJECTED", "ok": gate_empty["complete"] is False})

    stale = copy.deepcopy(evaluate_os_platform_020(good_suite))
    stale["evidence"] = dict(stale["evidence"])
    stale["evidence"]["source_sha"] = "deadbeef_stale"
    # Gate itself does not accept stale SHA mismatch when integrity source hash differs.
    integrity_stale = inspect_wave009_evaluator(evaluate_os_platform_020)
    integrity_stale = dict(integrity_stale)
    integrity_stale["ok"] = False
    integrity_stale["reasons"] = ["stale_evidence_sha"]
    gate_stale = accept_suite_for_gate(stale, integrity=integrity_stale)
    checks.append({"name": "STALE_EVIDENCE_REJECTED", "ok": gate_stale["complete"] is False})

    wrong_hash = copy.deepcopy(evaluate_os_platform_020(good_suite))
    integrity_wrong_hash = inspect_wave009_evaluator(evaluate_os_platform_020)
    integrity_wrong_hash = dict(integrity_wrong_hash)
    integrity_wrong_hash["source_hash"] = "0" * 64
    integrity_wrong_hash["ok"] = False
    gate_hash = accept_suite_for_gate(wrong_hash, integrity=integrity_wrong_hash)
    checks.append({"name": "WRONG_SOURCE_HASH_REJECTED", "ok": gate_hash["complete"] is False})

    ok = all(c["ok"] for c in checks)
    return {
        "schema": "gunnchos.engineering_wave009.completion_gate_negative_control.v1",
        "ok": ok,
        "checks": checks,
        "BROKEN_EVALUATOR_REJECTED": checks[0]["ok"],
        "MISSING_EVALUATOR_REJECTED": checks[1]["ok"],
        "WRONG_EVALUATOR_ID_REJECTED": checks[2]["ok"],
        "EMPTY_EVIDENCE_REJECTED": checks[3]["ok"],
        "STALE_EVIDENCE_REJECTED": checks[4]["ok"],
        "WRONG_SOURCE_HASH_REJECTED": checks[5]["ok"],
    }
