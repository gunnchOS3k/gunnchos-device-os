"""Requirement-specific evaluators for NET-ORCH-026..035. No unconditional True."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from gunnchos_device_os.service_continuity_execution.adaptation import prove_low_bandwidth_adaptation
from gunnchos_device_os.service_continuity_execution.baselines import comparative_baselines
from gunnchos_device_os.service_continuity_execution.behavioral_negative_controls import (
    prove_behavioral_negative_controls,
)
from gunnchos_device_os.service_continuity_execution.cache import prove_persistent_cache_a_b_c
from gunnchos_device_os.service_continuity_execution.degraded_report import prove_degraded_mode_reporting
from gunnchos_device_os.service_continuity_execution.e2e_scenarios import run_e2e_scenarios_a_through_j
from gunnchos_device_os.service_continuity_execution.evaluator_integrity import inspect_evaluators
from gunnchos_device_os.service_continuity_execution.failure_injection import run_failure_injection_suite
from gunnchos_device_os.service_continuity_execution.local_infra import prove_local_infrastructure
from gunnchos_device_os.service_continuity_execution.metrics import compute_research_metrics
from gunnchos_device_os.service_continuity_execution.multipath import prove_application_multipath
from gunnchos_device_os.service_continuity_execution.prioritization import prove_traffic_prioritization
from gunnchos_device_os.service_continuity_execution.resume import prove_session_resume_a_b_c
from gunnchos_device_os.service_continuity_execution.satellite import prove_satellite_visibility
from gunnchos_device_os.service_continuity_execution.state_machine import prove_continuity_state_machine
from gunnchos_device_os.service_continuity_execution.sync import prove_opportunistic_sync
from gunnchos_device_os.service_continuity_execution.transition import prove_digital_bearer_transition

TARGET_REQUIREMENTS = (
    "NET-ORCH-026",
    "NET-ORCH-027",
    "NET-ORCH-028",
    "NET-ORCH-029",
    "NET-ORCH-030",
    "NET-ORCH-031",
    "NET-ORCH-032",
    "NET-ORCH-033",
    "NET-ORCH-034",
    "NET-ORCH-035",
)


def _result(req_id: str, ok: bool, note: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence or {}
    if ok and evidence:
        classification = "IMPLEMENTED_AND_VALIDATED"
    elif evidence:
        classification = "IMPLEMENTED_VALIDATION_OPEN"
    else:
        classification = "IMPLEMENTATION_OPEN"
        ok = False
    return {
        "requirement_id": req_id,
        "classification": classification,
        "ok": bool(ok and evidence),
        "note": note,
        "evaluator": "",
        "evidence": evidence,
    }


def _wrap(req_id: str, fn_name: str, proof: dict[str, Any], note: str) -> dict[str, Any]:
    ok = proof.get("ok") is True
    evidence = {k: v for k, v in proof.items() if k != "ok"}
    evidence["proof_ok"] = ok
    row = _result(req_id, ok, note, evidence=evidence)
    row["evaluator"] = fn_name
    return row


def evaluate_net_orch_026(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_satellite_visibility()
    # Full repaired contract predicates
    ok = proof.get("ok") is True and proof.get("SATELLITE_VISIBILITY_WINDOWS") is True
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-026", "evaluate_net_orch_026", proof, "Satellite visibility windows + freshness")


def evaluate_net_orch_027(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_local_infrastructure()
    ok = proof.get("ok") is True and proof.get("LOCAL_INFRA_CAPABILITY_GRAPH") is True
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-027", "evaluate_net_orch_027", proof, "Local infrastructure capability graph")


def evaluate_net_orch_028(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_digital_bearer_transition()
    ok = (
        proof.get("ok") is True
        and proof.get("TRANSITION_TRANSACTION_RUNTIME") is True
        and proof.get("TRANSITION_ROLLBACK_PROOF") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-028", "evaluate_net_orch_028", proof, "Bearer transition transaction + rollback")


def evaluate_net_orch_029(_ctx: Any = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="wave006-029-") as tmp:
        proof = prove_session_resume_a_b_c(Path(tmp))
    ok = (
        proof.get("ok") is True
        and proof.get("SESSION_RESUME_EXACTLY_ONCE") is True
        and proof.get("SESSION_DUPLICATE_RESUME_BLOCKED") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-029", "evaluate_net_orch_029", proof, "Durable checkpoint/resume exactly-once")


def evaluate_net_orch_030(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_application_multipath()
    ok = (
        proof.get("ok") is True
        and proof.get("APPLICATION_MULTIPATH_REAL_TRANSFER") is True
        and proof.get("MULTIPATH_PATH_FAILURE_CONTINUES") is True
        and proof.get("MULTIPATH_PAYLOAD_HASH_MATCH") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-030", "evaluate_net_orch_030", proof, "Application-level multipath real transfer")


def evaluate_net_orch_031(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_low_bandwidth_adaptation()
    ok = proof.get("ok") is True and proof.get("ADAPTATION_HYSTERESIS") is True and proof.get("ADAPTATION_RECOVERY") is True
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-031", "evaluate_net_orch_031", proof, "Stateful adaptation hysteresis/recovery")


def evaluate_net_orch_032(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_traffic_prioritization()
    ok = (
        proof.get("ok") is True
        and proof.get("TRAFFIC_SCHEDULER_RUNTIME") is True
        and proof.get("TRAFFIC_STARVATION_BOUNDED") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-032", "evaluate_net_orch_032", proof, "Constrained-capacity traffic scheduler")


def evaluate_net_orch_033(_ctx: Any = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="wave006-033-") as tmp:
        proof = prove_persistent_cache_a_b_c(Path(tmp))
    ok = (
        proof.get("ok") is True
        and proof.get("CACHE_TTL") is True
        and proof.get("CACHE_INTEGRITY") is True
        and proof.get("CACHE_SIZE_BUDGET") is True
        and proof.get("CACHE_NAMESPACE_ISOLATION") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-033", "evaluate_net_orch_033", proof, "Cache TTL/integrity/budget/namespace")


def evaluate_net_orch_034(_ctx: Any = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="wave006-034-") as tmp:
        proof = prove_opportunistic_sync(Path(tmp))
    ok = (
        proof.get("ok") is True
        and proof.get("SYNC_OPPORTUNITY_PLANNER") is True
        and proof.get("SYNC_MAX_BYTES_ENFORCED") is True
        and proof.get("SYNC_EXACTLY_ONCE") is True
    )
    proof = dict(proof)
    proof["ok"] = ok
    return _wrap("NET-ORCH-034", "evaluate_net_orch_034", proof, "SyncOpportunity planner")


def evaluate_net_orch_035(_ctx: Any = None) -> dict[str, Any]:
    proof = prove_degraded_mode_reporting()
    sm = prove_continuity_state_machine()
    ok = (
        proof.get("ok") is True
        and proof.get("DEGRADED_REPORT_CANONICAL") is True
        and proof.get("DEGRADED_REPORT_RUNTIME_CONSISTENT") is True
        and sm.get("ok") is True
    )
    proof = dict(proof)
    proof["state_machine"] = sm
    proof["ok"] = ok
    return _wrap("NET-ORCH-035", "evaluate_net_orch_035", proof, "Canonical degraded report + state machine")


EVALUATORS = {
    "NET-ORCH-026": evaluate_net_orch_026,
    "NET-ORCH-027": evaluate_net_orch_027,
    "NET-ORCH-028": evaluate_net_orch_028,
    "NET-ORCH-029": evaluate_net_orch_029,
    "NET-ORCH-030": evaluate_net_orch_030,
    "NET-ORCH-031": evaluate_net_orch_031,
    "NET-ORCH-032": evaluate_net_orch_032,
    "NET-ORCH-033": evaluate_net_orch_033,
    "NET-ORCH-034": evaluate_net_orch_034,
    "NET-ORCH-035": evaluate_net_orch_035,
}


def run_all_evaluators() -> dict[str, Any]:
    broken = os.environ.get("WAVE006_BROKEN_EVALUATOR")
    classification: dict[str, Any] = {}
    matrix = []
    for req_id in TARGET_REQUIREMENTS:
        fn = EVALUATORS[req_id]
        if broken and broken == req_id:
            row = {
                "requirement_id": req_id,
                "classification": "IMPLEMENTED_AND_VALIDATED",
                "ok": True,
                "note": "env broken evaluator",
                "evaluator": fn.__name__,
                "evidence": {},
            }
        else:
            row = fn()
            row["evaluator"] = fn.__name__
        classification[req_id] = row
        matrix.append(
            {
                "requirement_id": req_id,
                "evaluator": row.get("evaluator"),
                "classification": row.get("classification"),
                "ok": row.get("ok"),
                "evidence_keys": sorted((row.get("evidence") or {}).keys()),
            }
        )
    integrity = inspect_evaluators(EVALUATORS)
    validated = sum(
        1
        for r in classification.values()
        if r.get("classification") == "IMPLEMENTED_AND_VALIDATED" and r.get("ok") and r.get("evidence")
    )
    summary = {
        "total": len(TARGET_REQUIREMENTS),
        "validated": validated,
        "implementation_open": sum(1 for r in classification.values() if r.get("classification") == "IMPLEMENTATION_OPEN"),
        "implemented_validation_open": sum(
            1 for r in classification.values() if r.get("classification") == "IMPLEMENTED_VALIDATION_OPEN"
        ),
        "blocked_environment": 0,
        "blocked_external": 0,
    }
    e2e = run_e2e_scenarios_a_through_j()
    failures = run_failure_injection_suite()
    metrics = compute_research_metrics(e2e)
    baselines = comparative_baselines()
    behavioral = prove_behavioral_negative_controls()
    state_machine = prove_continuity_state_machine()
    from gunnchos_device_os.service_continuity_execution.completion_gate import evaluate_completion_gate

    gate = evaluate_completion_gate(classification, integrity=integrity)
    return {
        "classification": classification,
        "summary": summary,
        "matrix": {
            "schema": "gunnchos.engineering_wave006.requirement_evaluator_matrix.v1",
            "rows": matrix,
            "unconditional_true_classifiers": integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"],
            "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
            "target_requirements": list(TARGET_REQUIREMENTS),
        },
        "integrity": integrity,
        "e2e": e2e,
        "failure_injection": failures,
        "metrics": metrics,
        "baselines": baselines,
        "behavioral_negative_controls": behavioral,
        "state_machine": state_machine,
        "completion_gate": gate,
        "target_requirements": list(TARGET_REQUIREMENTS),
    }
