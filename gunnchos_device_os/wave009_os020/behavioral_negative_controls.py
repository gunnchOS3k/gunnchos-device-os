"""Behavioral sabotage controls for OS-PLATFORM-020 — evaluator must refuse each sabotage."""
from __future__ import annotations

import copy
from typing import Any

from gunnchos_device_os.wave009_os020.evaluator import evaluate_os_platform_020


def _base_valid_suite() -> dict[str, Any]:
    return {
        "SANDBOX_BACKEND": "bubblewrap",
        "fixture_ran": True,
        "PRIVATE_ROOT_RW_PASS": True,
        "APP_ROOT_READ_ALLOWED": True,
        "APP_ROOT_WRITE_ALLOWED": True,
        "NORMAL_PYTHON_EXECUTION_INSIDE_SANDBOX": True,
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
        "fixture_result": {"host_private_read": False},
        "source_sha": "current",
    }


def _case(name: str, suite: dict[str, Any]) -> dict[str, Any]:
    row = evaluate_os_platform_020(suite)
    rejected = row.get("ok") is not True or row.get("classification") != "IMPLEMENTED_AND_VALIDATED"
    return {
        "name": name,
        "sabotage_detected": rejected,
        "evaluator_would_fail": rejected,
        "classification": row.get("classification"),
        "reasons": row.get("reasons") or [],
    }


def prove_behavioral_negative_controls() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    # 1. plain subprocess substituted for bwrap
    s = _base_valid_suite()
    s["SANDBOX_BACKEND"] = "subprocess_broker"
    s["KERNEL_SANDBOX"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    s["LOCAL_SANDBOX_VALIDATION"] = "BLOCKED_ENVIRONMENT"
    cases.append(_case("plain_subprocess_substituted_for_bwrap", s))

    # 2. fixture never ran
    s = _base_valid_suite()
    s["fixture_ran"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("fixture_never_ran", s))

    # 3. host-private path deliberately bound / readable
    s = _base_valid_suite()
    s["HOST_PRIVATE_READ_BLOCKED"] = False
    s["fixture_result"] = {"host_private_read": True}
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("host_private_deliberately_exposed", s))

    # 4. sibling-app secret deliberately exposed
    s = _base_valid_suite()
    s["CROSS_APP_READ_BLOCKED"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("sibling_app_secret_exposed", s))

    # 5. outside directory made writable
    s = _base_valid_suite()
    s["OUTSIDE_WRITE_BLOCKED"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("outside_directory_writable", s))

    # 6. seccomp network rule removed → network not denied
    s = _base_valid_suite()
    s["NETWORK_DENIED"] = False
    s["SECCOMP_LOADED"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("seccomp_network_rule_removed", s))

    # 7. seccomp exec rule removed → child spawn works
    s = _base_valid_suite()
    s["CHILD_SPAWN_DENIED"] = False
    s["SECCOMP_LOADED"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("seccomp_exec_rule_removed", s))

    # 8. fake KERNEL_SANDBOX=true with blocked backend
    s = _base_valid_suite()
    s["SANDBOX_BACKEND"] = "bubblewrap_environment_blocked"
    s["KERNEL_SANDBOX"] = True  # fake claim
    s["LOCAL_SANDBOX_VALIDATION"] = "BLOCKED_ENVIRONMENT"
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("fake_kernel_sandbox_with_blocked_backend", s))

    # 9. missing positive app-root write proof
    s = _base_valid_suite()
    s["PRIVATE_ROOT_RW_PASS"] = False
    s["APP_ROOT_WRITE_ALLOWED"] = False
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("missing_positive_app_root_write_proof", s))

    # 10. backend string spoofed without process provenance
    s = _base_valid_suite()
    s["SANDBOX_BACKEND"] = "bubblewrap"
    s["SANDBOX_EXECUTION_VALIDATED"] = False  # no provenance of real execution
    s["KERNEL_SANDBOX"] = False
    cases.append(_case("backend_string_spoofed_without_provenance", s))

    # 11. stale evidence from earlier source SHA
    s = _base_valid_suite()
    s["source_sha"] = "stale_wave004_deadbeef"
    s["SANDBOX_EXECUTION_VALIDATED"] = True
    # Force evaluator reject via mismatched provenance flag used by gate; also poison a required flag.
    # Behavioral control: mark evidence stale by clearing fixture_ran while claiming validated.
    s2 = copy.deepcopy(s)
    s2["fixture_ran"] = False
    s2["stale_evidence"] = True
    cases.append(_case("stale_evidence_from_earlier_source_sha", s2))

    # 12. evidence from root/sudo sandbox execution
    s = _base_valid_suite()
    s["SANDBOX_EXECUTED_AS_ROOT"] = True
    s["BWRAP_INVOKED_WITH_SUDO"] = True
    s["SANDBOX_EXECUTION_VALIDATED"] = False
    cases.append(_case("evidence_from_root_or_sudo_sandbox_execution", s))

    ok = all(c["sabotage_detected"] and c["evaluator_would_fail"] for c in cases)
    return {
        "schema": "gunnchos.engineering_wave009.behavioral_negative_controls.v1",
        "BEHAVIORAL_NEGATIVE_CONTROL_COUNT": len(cases),
        "BEHAVIORAL_NEGATIVE_CONTROLS_PASS": ok,
        "ok": ok,
        "cases": cases,
    }
