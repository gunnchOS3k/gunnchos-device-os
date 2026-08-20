"""AST/source integrity inspection for Wave006 requirement evaluators."""
from __future__ import annotations

import ast
import hashlib
import inspect
from typing import Any, Callable


def _source_hash(fn: Callable[..., Any]) -> str:
    try:
        src = inspect.getsource(fn)
    except OSError:
        src = repr(fn)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


def _literal_success_findings(fn: Callable[..., Any]) -> list[str]:
    findings: list[str] = []
    try:
        src = inspect.getsource(fn)
        tree = ast.parse(src)
    except (OSError, SyntaxError) as exc:
        return [f"source_unreadable:{exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "ok":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    findings.append("assign_ok_true")
        if isinstance(node, ast.Return) and node.value is not None:
            val = node.value
            if isinstance(val, ast.Call):
                if len(val.args) >= 2 and isinstance(val.args[1], ast.Constant) and val.args[1].value is True:
                    has_evidence = any(isinstance(kw, ast.keyword) and kw.arg == "evidence" for kw in val.keywords)
                    findings.append("return_result_literal_true")
                    if not has_evidence:
                        findings.append("return_result_literal_true_without_evidence_kw")
            if isinstance(val, ast.Dict):
                for k, v in zip(val.keys or [], val.values or []):
                    if isinstance(k, ast.Constant) and k.value == "ok" and isinstance(v, ast.Constant) and v.value is True:
                        findings.append("return_dict_ok_true")
    compares = [n for n in ast.walk(tree) if isinstance(n, (ast.Compare, ast.BoolOp, ast.Call))]
    if "assign_ok_true" in findings and len(compares) < 2:
        findings.append("unconditional_success_suspected")
    return findings


def _is_unconditional(findings: list[str], evidence_keys: list[str], fn: Callable[..., Any]) -> bool:
    if "return_result_literal_true_without_evidence_kw" in findings and not evidence_keys:
        return True
    if "unconditional_success_suspected" in findings and not evidence_keys:
        return True
    try:
        result = fn()
    except Exception:
        return False
    if not isinstance(result, dict):
        return True
    if result.get("ok") is True and not result.get("evidence"):
        return True
    if "return_result_literal_true" in findings:
        try:
            src = inspect.getsource(fn)
        except OSError:
            return False
        if ", True," in src and "return _result" in src:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
                    if len(node.value.args) >= 2 and isinstance(node.value.args[1], ast.Constant) and node.value.args[1].value is True:
                        return True
    return False


def inspect_evaluators(evaluators: dict[str, Callable[..., Any]] | None = None) -> dict[str, Any]:
    from gunnchos_device_os.service_continuity_execution.evaluators import EVALUATORS, TARGET_REQUIREMENTS

    mapping = evaluators if evaluators is not None else dict(EVALUATORS)
    rows: list[dict[str, Any]] = []
    unconditional = 0
    for req_id in TARGET_REQUIREMENTS:
        fn = mapping.get(req_id)
        if fn is None:
            rows.append({
                "requirement_id": req_id,
                "evaluator_name": None,
                "source_hash": None,
                "literal_success_findings": ["missing_evaluator"],
                "evidence_keys": [],
                "integrity_ok": False,
                "unconditional": True,
            })
            unconditional += 1
            continue
        findings = _literal_success_findings(fn)
        try:
            sample = fn()
            evidence = sample.get("evidence") if isinstance(sample, dict) else None
            evidence_keys = sorted(evidence.keys()) if isinstance(evidence, dict) else []
        except Exception as exc:
            evidence_keys = []
            findings = findings + [f"runtime_error:{exc}"]
            sample = None
        uncond = _is_unconditional(findings, evidence_keys, fn)
        if uncond:
            unconditional += 1
        integrity_ok = (
            not uncond
            and callable(fn)
            and isinstance(sample, dict)
            and bool(evidence_keys)
            and "evaluator" in (sample or {})
        )
        rows.append({
            "requirement_id": req_id,
            "evaluator_name": getattr(fn, "__name__", str(fn)),
            "source_hash": _source_hash(fn),
            "literal_success_findings": findings,
            "evidence_keys": evidence_keys,
            "integrity_ok": integrity_ok,
            "unconditional": uncond,
        })
    return {
        "schema": "gunnchos.engineering_wave006.evaluator_integrity.v1",
        "target_requirements": list(TARGET_REQUIREMENTS),
        "evaluators_inspected": len(rows),
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "ok": unconditional == 0 and all(r["integrity_ok"] for r in rows),
        "requirements": rows,
    }
