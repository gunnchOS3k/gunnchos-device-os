"""AST/source integrity for Wave009 OS-PLATFORM-020 evaluator."""
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
            if isinstance(val, ast.Dict):
                for k, v in zip(val.keys or [], val.values or []):
                    if isinstance(k, ast.Constant) and k.value == "ok" and isinstance(v, ast.Constant) and v.value is True:
                        findings.append("return_dict_ok_true")
    compares = [n for n in ast.walk(tree) if isinstance(n, (ast.Compare, ast.BoolOp, ast.Call))]
    if "assign_ok_true" in findings and len(compares) < 2:
        findings.append("unconditional_success_suspected")
    return findings


def inspect_wave009_evaluator(fn: Callable[..., Any]) -> dict[str, Any]:
    findings = _literal_success_findings(fn)
    try:
        sample = fn()
        evidence = sample.get("evidence") if isinstance(sample, dict) else None
        evidence_keys = sorted(evidence.keys()) if isinstance(evidence, dict) else []
    except Exception as exc:  # noqa: BLE001
        sample = None
        evidence_keys = []
        findings = findings + [f"runtime_error:{exc}"]

    unconditional = False
    if "unconditional_success_suspected" in findings and not evidence_keys:
        unconditional = True
    if isinstance(sample, dict) and sample.get("ok") is True and not sample.get("evidence"):
        unconditional = True
    if "return_dict_ok_true" in findings and not evidence_keys:
        unconditional = True

    integrity_ok = (
        not unconditional
        and callable(fn)
        and isinstance(sample, dict)
        and bool(evidence_keys)
        and sample.get("evaluator") == getattr(fn, "__name__", None)
    )
    return {
        "schema": "gunnchos.engineering_wave009.evaluator_integrity.v1",
        "requirement_id": "OS-PLATFORM-020",
        "evaluator_name": getattr(fn, "__name__", str(fn)),
        "source_hash": _source_hash(fn),
        "literal_success_findings": findings,
        "evidence_keys": evidence_keys,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": 1 if unconditional else 0,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "ok": integrity_ok and not unconditional,
        "integrity_ok": integrity_ok and not unconditional,
    }
