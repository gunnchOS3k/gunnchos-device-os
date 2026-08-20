"""Strict Wave006 completion gate + negative-control injections."""
from __future__ import annotations

import copy
import os
from typing import Any, Callable

from gunnchos_device_os.service_continuity_execution.evaluators import (
    EVALUATORS,
    TARGET_REQUIREMENTS,
    run_all_evaluators,
)
from gunnchos_device_os.service_continuity_execution.evaluator_integrity import inspect_evaluators

EXPECTED = set(TARGET_REQUIREMENTS)


def evaluate_completion_gate(
    classification: dict[str, dict[str, Any]],
    *,
    evaluators: dict[str, Callable[..., Any]] | None = None,
    integrity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """COMPLETE only when all 10 rows independently earn IMPLEMENTED_AND_VALIDATED."""
    mapping = evaluators if evaluators is not None else dict(EVALUATORS)
    integrity = integrity if integrity is not None else inspect_evaluators(mapping)
    ids = set(classification.keys())
    reasons: list[str] = []
    if len(TARGET_REQUIREMENTS) != 10:
        reasons.append("target_count_not_10")
    if len(mapping) != 10:
        reasons.append("evaluator_map_count_not_10")
    if len(classification) != 10:
        reasons.append("result_count_not_10")
    if ids != EXPECTED:
        missing = sorted(EXPECTED - ids)
        unexpected = sorted(ids - EXPECTED)
        if missing:
            reasons.append(f"missing_ids:{missing}")
        if unexpected:
            reasons.append(f"unexpected_ids:{unexpected}")

    validated = 0
    for req_id in TARGET_REQUIREMENTS:
        row = classification.get(req_id)
        if row is None:
            reasons.append(f"missing_row:{req_id}")
            continue
        ev_name = row.get("evaluator")
        expected_fn = mapping.get(req_id)
        expected_name = getattr(expected_fn, "__name__", None) if expected_fn else None
        if expected_fn is None:
            reasons.append(f"missing_evaluator:{req_id}")
        elif ev_name != expected_name:
            reasons.append(f"evaluator_mismatch:{req_id}:{ev_name}!={expected_name}")
        if not row.get("evidence"):
            reasons.append(f"empty_evidence:{req_id}")
        if row.get("ok") is not True:
            reasons.append(f"ok_false:{req_id}")
        if row.get("classification") != "IMPLEMENTED_AND_VALIDATED":
            reasons.append(f"not_validated:{req_id}:{row.get('classification')}")
        else:
            if row.get("ok") is True and row.get("evidence"):
                validated += 1

    unconditional = int(integrity.get("UNCONDITIONAL_TRUE_CLASSIFIERS", 0))
    if unconditional != 0:
        reasons.append(f"unconditional_true_classifiers:{unconditional}")
    if integrity.get("ok") is not True:
        reasons.append("evaluator_integrity_failed")

    complete = validated == 10 and not reasons and unconditional == 0
    return {
        "schema": "gunnchos.engineering_wave006.completion_gate.v1",
        "COMPLETE_GATE_REQUIRES_10_OF_10": True,
        "WAVE006_COMPLETE_GATE_REQUIRES_10_OF_10": True,
        "target_count": len(TARGET_REQUIREMENTS),
        "evaluator_map_count": len(mapping),
        "result_count": len(classification),
        "validated_count": validated,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "complete": complete,
        "ok": complete,
        "reasons": reasons,
        "integrity_ok": integrity.get("ok") is True,
    }


def _broken_true_classifier(_ctx: Any = None) -> dict[str, Any]:
    return {
        "requirement_id": "INJECTED",
        "classification": "IMPLEMENTED_AND_VALIDATED",
        "ok": True,
        "note": "broken_evaluator_fixture",
        "evaluator": "_broken_true_classifier",
        "evidence": {},
    }


def run_negative_controls() -> dict[str, Any]:
    base = run_all_evaluators()
    classification = base["classification"]
    results: dict[str, Any] = {}

    broken_map = dict(EVALUATORS)
    victim = TARGET_REQUIREMENTS[0]
    broken_map[victim] = _broken_true_classifier
    broken_class = {k: (broken_map[k]() if k == victim else classification[k]) for k in TARGET_REQUIREMENTS}
    broken_class[victim]["requirement_id"] = victim
    gate_broken = evaluate_completion_gate(broken_class, evaluators=broken_map)
    results["broken_evaluator"] = {
        "injected": victim,
        "gate_complete": gate_broken["complete"],
        "rejected": gate_broken["complete"] is False,
        "reasons": gate_broken["reasons"],
    }

    missing_map = dict(EVALUATORS)
    missing_id = TARGET_REQUIREMENTS[1]
    del missing_map[missing_id]
    missing_class = {k: v for k, v in classification.items() if k != missing_id}
    gate_missing = evaluate_completion_gate(missing_class, evaluators=missing_map)
    results["missing_evaluator"] = {
        "injected": missing_id,
        "gate_complete": gate_missing["complete"],
        "rejected": gate_missing["complete"] is False,
        "reasons": gate_missing["reasons"],
    }

    unexpected_class = dict(classification)
    unexpected_class["NET-ORCH-999"] = copy.deepcopy(classification[TARGET_REQUIREMENTS[0]])
    gate_unexpected = evaluate_completion_gate(unexpected_class)
    results["unexpected_evaluator_id"] = {
        "gate_complete": gate_unexpected["complete"],
        "rejected": gate_unexpected["complete"] is False,
        "reasons": gate_unexpected["reasons"],
    }

    false_class = copy.deepcopy(classification)
    false_id = TARGET_REQUIREMENTS[2]
    false_class[false_id]["ok"] = False
    false_class[false_id]["classification"] = "IMPLEMENTATION_OPEN"
    gate_false = evaluate_completion_gate(false_class)
    results["ok_false"] = {
        "injected": false_id,
        "gate_complete": gate_false["complete"],
        "rejected": gate_false["complete"] is False,
        "reasons": gate_false["reasons"],
    }

    empty_class = copy.deepcopy(classification)
    empty_id = TARGET_REQUIREMENTS[3]
    empty_class[empty_id]["evidence"] = {}
    gate_empty = evaluate_completion_gate(empty_class)
    results["empty_evidence"] = {
        "injected": empty_id,
        "gate_complete": gate_empty["complete"],
        "rejected": gate_empty["complete"] is False,
        "reasons": gate_empty["reasons"],
    }

    env_victim = os.environ.get("WAVE006_BROKEN_EVALUATOR")
    env_result = None
    if env_victim:
        env_map = dict(EVALUATORS)
        if env_victim in env_map:
            env_map[env_victim] = _broken_true_classifier
            env_class = {k: env_map[k]() for k in TARGET_REQUIREMENTS}
            for k, row in env_class.items():
                row["requirement_id"] = k
            env_gate = evaluate_completion_gate(env_class, evaluators=env_map)
            env_result = {"injected": env_victim, "gate_complete": env_gate["complete"], "rejected": not env_gate["complete"]}

    all_rejected = all(
        results[k]["rejected"]
        for k in ("broken_evaluator", "missing_evaluator", "unexpected_evaluator_id", "ok_false", "empty_evidence")
    )
    return {
        "schema": "gunnchos.engineering_wave006.completion_gate_negative_control.v1",
        "ok": all_rejected,
        "BROKEN_EVALUATOR_GATE_RESULT": "REJECTED" if results["broken_evaluator"]["rejected"] else "ACCEPTED",
        "cases": results,
        "env_injection": env_result,
    }
