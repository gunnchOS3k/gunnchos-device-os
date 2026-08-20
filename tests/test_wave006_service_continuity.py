"""Wave006 service-continuity execution plane tests."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from gunnchos_device_os.service_continuity_execution.completion_gate import (
    evaluate_completion_gate,
    run_negative_controls,
)
from gunnchos_device_os.service_continuity_execution.evaluators import TARGET_REQUIREMENTS, run_all_evaluators
from gunnchos_device_os.service_continuity_execution.models import CLAIM_BOUNDARIES, MultipathKind


ABS_RE = re.compile(r"(/Users/|/home/|/mnt/|/tmp/|[A-Za-z]:\\\\)")


def test_target_requirements_exactly_10():
    assert len(TARGET_REQUIREMENTS) == 10
    assert TARGET_REQUIREMENTS[0] == "NET-ORCH-026"
    assert TARGET_REQUIREMENTS[-1] == "NET-ORCH-035"
    assert "NET-ORCH-001" not in TARGET_REQUIREMENTS
    assert "OS-PLATFORM-020" not in TARGET_REQUIREMENTS


def test_evaluators_all_validated():
    bundle = run_all_evaluators()
    assert bundle["summary"]["total"] == 10
    assert bundle["summary"]["validated"] == 10
    for req_id in TARGET_REQUIREMENTS:
        row = bundle["classification"][req_id]
        assert row["ok"] is True, req_id
        assert row["classification"] == "IMPLEMENTED_AND_VALIDATED", req_id
        assert row["evidence"], req_id


def test_completion_gate_requires_10_of_10():
    bundle = run_all_evaluators()
    gate = evaluate_completion_gate(bundle["classification"], integrity=bundle["integrity"])
    assert gate["COMPLETE_GATE_REQUIRES_10_OF_10"] is True
    assert gate["complete"] is True
    assert gate["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0


def test_integrity_unconditional_zero():
    bundle = run_all_evaluators()
    assert bundle["integrity"]["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0
    assert bundle["integrity"]["UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED"] is True
    assert bundle["integrity"]["ok"] is True


def test_negative_controls_reject():
    neg = run_negative_controls()
    assert neg["ok"] is True
    assert neg["BROKEN_EVALUATOR_GATE_RESULT"] == "REJECTED"


def test_env_broken_evaluator_fails_gate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WAVE006_BROKEN_EVALUATOR", "NET-ORCH-026")
    bundle = run_all_evaluators()
    gate = evaluate_completion_gate(bundle["classification"], integrity=bundle["integrity"])
    assert gate["complete"] is False


def test_e2e_a_through_j():
    bundle = run_all_evaluators()
    assert bundle["e2e"]["ok"] is True
    assert bundle["e2e"]["passed"] == 10


def test_failure_injection():
    bundle = run_all_evaluators()
    assert bundle["failure_injection"]["ok"] is True


def test_multipath_kind_application_level():
    from gunnchos_device_os.service_continuity_execution.multipath import prove_application_multipath

    proof = prove_application_multipath()
    assert proof["MULTIPATH_KIND"] == MultipathKind.APPLICATION_LEVEL_MULTIPATH.value
    assert proof["REAL_MPTCP"] is False


def test_claim_boundaries_all_false():
    assert all(v is False for v in CLAIM_BOUNDARIES.values())


def test_baselines_no_universal_optimality():
    bundle = run_all_evaluators()
    assert bundle["baselines"]["UNIVERSAL_OPTIMALITY"] is False
    assert bundle["metrics"]["UNIVERSAL_OPTIMALITY"] is False


def test_wave006_evidence_script_and_no_abs_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    import scripts.engineering_wave006.run_wave006_evidence as ev

    # redirect artifacts to tmp by patching ROOT? script uses its own ROOT
    rc = ev.main()
    assert rc == 0
    out = root / "artifacts/engineering_wave006"
    result = json.loads((out / "WAVE006_RESULT.json").read_text())
    assert result["wave006_ok"] is True
    assert result["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0
    assert result["OS_PLATFORM_020_UNTOUCHED"] is True
    assert result["BASELINE_COUNTS_UPDATED"] is False
    for path in out.glob("*.json"):
        blob = path.read_text(encoding="utf-8")
        assert not ABS_RE.search(blob), path.name
