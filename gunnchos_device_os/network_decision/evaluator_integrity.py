"""AST/source integrity inspection for Wave005 requirement evaluators."""
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
    """Bounded integrity rule: reject trivial unconditional success patterns."""
    findings: list[str] = []
    try:
        src = inspect.getsource(fn)
        tree = ast.parse(src)
    except (OSError, SyntaxError) as exc:
        return [f"source_unreadable:{exc}"]

    # Walk function body for suspicious patterns
    for node in ast.walk(tree):
        # ok = True (bare)
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "ok":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    # Allow only if later overwritten — still flag as finding for review;
                    # count as unconditional only if it's the sole assignment and return uses it
                    findings.append("assign_ok_true")
        # return _result(..., True, ...) or return {"ok": True}
        if isinstance(node, ast.Return) and node.value is not None:
            val = node.value
            if isinstance(val, ast.Call):
                # _result(req, True, ...)
                if len(val.args) >= 2 and isinstance(val.args[1], ast.Constant) and val.args[1].value is True:
                    # Check whether True is the only predicate — look for evidence kw
                    has_evidence = any(
                        isinstance(kw, ast.keyword) and kw.arg == "evidence" for kw in val.keywords
                    )
                    # Still suspicious if True is literal first positional for ok
                    # Only unconditional if no preceding ok computation uses comparisons
                    findings.append("return_result_literal_true")
                    if not has_evidence:
                        findings.append("return_result_literal_true_without_evidence_kw")
            if isinstance(val, ast.Dict):
                for k, v in zip(val.keys, val.values):
                    if isinstance(k, ast.Constant) and k.value == "ok" and isinstance(v, ast.Constant) and v.value is True:
                        findings.append("return_dict_ok_true")

    # Heuristic: unconditional if function body has ok=True AND no Compare/BoolOp involving evidence vars
    compares = [n for n in ast.walk(tree) if isinstance(n, (ast.Compare, ast.BoolOp, ast.Call))]
    if "assign_ok_true" in findings and len(compares) < 2:
        findings.append("unconditional_success_suspected")
    # return_result_literal_true alone is common (_result(id, ok, ...)) where ok is Name — filter those
    refined: list[str] = []
    for f in findings:
        if f == "return_result_literal_true":
            # Check if second arg is Name('ok') vs Constant True — already only flagged Constant
            refined.append(f)
        else:
            refined.append(f)
    # Count as unconditional classifier only for strong patterns
    return refined


def _predicate_variables(fn: Callable[..., Any]) -> list[str]:
    try:
        src = inspect.getsource(fn)
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in {"ok", "d", "proof", "selected", "s_hi", "s_lo", "eng", "obj"}:
                names.add(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.attr, str):
            if node.attr in {"selected_candidate", "ok", "evidence", "classification"}:
                names.add(node.attr)
    return sorted(names)


def _is_unconditional(findings: list[str], evidence_keys: list[str], fn: Callable[..., Any]) -> bool:
    """Strong unconditional: literal True return with no evidence OR bare ok=True with no compares."""
    if "return_result_literal_true_without_evidence_kw" in findings and not evidence_keys:
        return True
    if "unconditional_success_suspected" in findings and not evidence_keys:
        return True
    # Runtime probe: call evaluator and require evidence non-empty when ok
    try:
        result = fn()
    except Exception:
        return False
    if not isinstance(result, dict):
        return True
    if result.get("ok") is True and not result.get("evidence"):
        return True
    # AST: if return _result(..., True, ...) with Constant True as ok arg — that means always True
    if "return_result_literal_true" in findings:
        # Distinguish Constant True vs Name: already Constant-only. Check source for pattern.
        try:
            src = inspect.getsource(fn)
        except OSError:
            return False
        # If 'ok = True' appears without later reassignment from expression, flag
        if "\nok = True\n" in src or src.strip().endswith("ok = True"):
            # see if ok is recomputed
            if src.count("ok =") == 1:
                return True
        # return _result("...", True, ...) hard-coded
        if ", True," in src and "return _result" in src:
            # Allow only if True is not the ok argument — hard to parse; use AST again
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
                    if len(node.value.args) >= 2 and isinstance(node.value.args[1], ast.Constant) and node.value.args[1].value is True:
                        return True
    return False


def inspect_evaluators(evaluators: dict[str, Callable[..., Any]] | None = None) -> dict[str, Any]:
    from gunnchos_device_os.network_decision.evaluators import EVALUATORS, TARGET_REQUIREMENTS

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
                "predicate_variables": [],
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
            "predicate_variables": _predicate_variables(fn),
            "literal_success_findings": findings,
            "evidence_keys": evidence_keys,
            "integrity_ok": integrity_ok,
            "unconditional": uncond,
        })
    return {
        "schema": "gunnchos.engineering_wave005.evaluator_integrity.v1",
        "target_requirements": list(TARGET_REQUIREMENTS),
        "evaluators_inspected": len(rows),
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "ok": unconditional == 0 and all(r["integrity_ok"] for r in rows),
        "requirements": rows,
    }
