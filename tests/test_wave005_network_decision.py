"""Wave005 Anywhere Network Decision Engine tests (integrity repair)."""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import pytest

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.completion_gate import evaluate_completion_gate, run_negative_controls
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.evaluator_integrity import inspect_evaluators
from gunnchos_device_os.network_decision.evaluators import TARGET_REQUIREMENTS, run_all_evaluators
from gunnchos_device_os.network_decision.invariants import run_invariants
from gunnchos_device_os.network_decision.invalid_telemetry import run_invalid_telemetry
from gunnchos_device_os.network_decision.models import (
    CLAIM_BOUNDARIES,
    ApplicationPriority,
    CostClass,
    EnforcementMode,
    NetworkPreferencePolicy,
    PriorityAuthority,
    PrioritySource,
    ServiceClass,
    TrustLevel,
    UserPreferenceProfile,
    default_objective_for,
)
from gunnchos_device_os.network_decision.preferences import UserPreferenceStore, prove_user_preference_policy
from gunnchos_device_os.network_decision.priority_authority import (
    prove_priority_only_boundary,
    prove_self_asserted_critical_blocked,
    resolve_priority_authority,
)
from gunnchos_device_os.network_decision.scenarios import run_all_scenarios
from gunnchos_device_os.network_decision.sensitivity import run_sensitivity

NOW = 1_700_000_000.0
ROOT = Path(__file__).resolve().parents[1]
ABS_RE = re.compile(r"(/Users/|/home/|/mnt/|/tmp/|[A-Za-z]:\\\\)")


def test_target_requirements_exactly_12():
    assert len(TARGET_REQUIREMENTS) == 12
    assert "NET-ORCH-026" not in TARGET_REQUIREMENTS


def test_scenarios_a_through_o():
    result = run_all_scenarios()
    assert result["ok"] is True, result.get("failed")
    assert result["count"] >= 15
    ids = {s["id"] for s in result["scenarios"]}
    assert {"K", "L", "M", "N", "O"} <= ids
    assert result["label"] == "DIGITAL_SYNTHETIC_EVIDENCE"


def test_invariants():
    result = run_invariants()
    assert result["ok"] is True, result


def test_invalid_telemetry():
    result = run_invalid_telemetry()
    assert result["ok"] is True, result
    assert result["never_best_case_missing_invalid"] is True
    assert result["NEVER_BEST_CASE_MISSING_INVALID_COMPUTED"] is True


def test_insecure_fast_free_rejected():
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.constraints.min_trust = TrustLevel.TRUSTED
    d = eng.decide(
        [
            CandidatePath(
                candidate_id="hostile",
                bearer_class="wifi",
                availability=True,
                signal_quality=1.0,
                latency_ms=1.0,
                jitter_ms=0.5,
                packet_loss_ratio=0.0,
                monetary_cost=0.0,
                cost_class=CostClass.UNMETERED,
                energy_cost=10.0,
                security_trust=TrustLevel.UNTRUSTED,
                data_unlimited=True,
                application_compatibility=True,
                telemetry_timestamp=NOW - 1,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
                confidence=1.0,
            ),
            CandidatePath(
                candidate_id="safe",
                bearer_class="wifi",
                availability=True,
                signal_quality=0.7,
                latency_ms=40.0,
                jitter_ms=8.0,
                packet_loss_ratio=0.02,
                monetary_cost=0.0,
                cost_class=CostClass.UNMETERED,
                energy_cost=400.0,
                security_trust=TrustLevel.TRUSTED,
                data_unlimited=True,
                application_compatibility=True,
                telemetry_timestamp=NOW - 1,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
                confidence=0.9,
            ),
        ],
        obj,
    )
    assert d.selected_candidate == "safe"
    assert "security_below_required_trust" in d.hard_constraint_reasons["hostile"]


def test_determinism():
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    cands = [
        CandidatePath(
            candidate_id="a",
            bearer_class="wifi",
            availability=True,
            signal_quality=0.8,
            latency_ms=20,
            jitter_ms=4,
            packet_loss_ratio=0.01,
            monetary_cost=0.0,
            cost_class=CostClass.UNMETERED,
            energy_cost=300,
            security_trust=TrustLevel.TRUSTED,
            data_unlimited=True,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.9,
        ),
        CandidatePath(
            candidate_id="b",
            bearer_class="cellular_generic",
            availability=True,
            signal_quality=0.7,
            latency_ms=40,
            jitter_ms=10,
            packet_loss_ratio=0.02,
            monetary_cost=0.05,
            cost_class=CostClass.METERED,
            energy_cost=800,
            security_trust=TrustLevel.TRUSTED,
            data_metered=True,
            data_remaining_fraction=0.5,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.9,
        ),
    ]
    d1 = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(cands, obj)
    d2 = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(list(reversed(cands)), obj)
    assert d1.selected_candidate == d2.selected_candidate
    assert d1.final_scores == d2.final_scores


def test_claim_boundaries_false():
    for k, v in CLAIM_BOUNDARIES.items():
        assert v is False, k
    assert CLAIM_BOUNDARIES["PRODUCTION_APP_PRIORITY_SIGNING"] is False


def test_sensitivity_runs():
    r = run_sensitivity()
    assert r["universal_optimality_claimed"] is False
    assert r["ok"] is True


def test_evaluators_integrity_computed():
    bundle = run_all_evaluators()
    integrity = inspect_evaluators()
    assert integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0
    assert integrity["ok"] is True
    assert bundle["matrix"]["UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED"] is True
    assert bundle["matrix"]["unconditional_true_classifiers"] == integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"]
    gate = evaluate_completion_gate(bundle["classification"], integrity=bundle["integrity"])
    assert gate["complete"] is True
    assert gate["WAVE005_COMPLETE_GATE_REQUIRES_12_OF_12"] is True
    for req_id, row in bundle["classification"].items():
        assert row["ok"] is True, (req_id, row)
        assert row["classification"] == "IMPLEMENTED_AND_VALIDATED"
        assert row.get("evidence")


def test_broken_evaluator_negative_control():
    neg = run_negative_controls()
    assert neg["ok"] is True
    assert neg["BROKEN_EVALUATOR_GATE_RESULT"] == "REJECTED"


def test_env_broken_evaluator_fails_gate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WAVE005_BROKEN_EVALUATOR", "NET-ORCH-001")
    bundle = run_all_evaluators()
    gate = evaluate_completion_gate(bundle["classification"], integrity=bundle["integrity"])
    assert gate["complete"] is False
    assert bundle["summary"]["validated"] < 12 or not bundle["classification"]["NET-ORCH-001"].get("evidence")


def test_priority_authority_and_boundary():
    assert prove_self_asserted_critical_blocked()["ok"] is True
    boundary = prove_priority_only_boundary()
    assert boundary["ok"] is True
    assert boundary["selection_changed"] is True
    res = resolve_priority_authority(
        ApplicationPriority.CRITICAL,
        PriorityAuthority(source=PrioritySource.APP_SELF_ASSERTED, trusted=False, asserted_priority=ApplicationPriority.CRITICAL),
    )
    assert res["effective"] != "CRITICAL"


def test_hard_preference_policy(tmp_path: Path):
    proof = prove_user_preference_policy(tmp_path)
    assert proof["ok"] is True, proof
    store = UserPreferenceStore(tmp_path / "h", profile_id="h")
    store.set_policy(NetworkPreferencePolicy(
        preference=UserPreferenceProfile.AVOID_CELLULAR,
        enforcement_mode=EnforcementMode.HARD,
        hard_avoid_bearers={"cellular_generic"},
        profile_id="h",
    ))
    eng = AnywhereNetworkDecisionEngine(preference_store=store, now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    d = eng.decide(
        [
            CandidatePath(
                candidate_id="wifi", bearer_class="wifi", availability=True, signal_quality=0.5,
                latency_ms=200, jitter_ms=10, packet_loss_ratio=0.02, monetary_cost=0.0,
                cost_class=CostClass.UNMETERED, energy_cost=500, security_trust=TrustLevel.TRUSTED,
                data_unlimited=True, application_compatibility=True, telemetry_timestamp=NOW - 1,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE, confidence=0.9,
            ),
            CandidatePath(
                candidate_id="cell", bearer_class="cellular_generic", availability=True, signal_quality=0.99,
                latency_ms=5, jitter_ms=2, packet_loss_ratio=0.001, monetary_cost=0.01,
                cost_class=CostClass.METERED, energy_cost=100, security_trust=TrustLevel.TRUSTED,
                data_metered=True, data_remaining_fraction=0.9, application_compatibility=True,
                telemetry_timestamp=NOW - 1, telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE, confidence=0.9,
            ),
        ],
        obj,
    )
    assert d.selected_candidate == "wifi"
    assert "cell" in [r["candidate_id"] for r in d.rejected_candidates]


def test_scores_finite():
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    d = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(
        [
            CandidatePath(
                candidate_id="x",
                bearer_class="wifi",
                availability=True,
                signal_quality=0.5,
                latency_ms=30,
                jitter_ms=5,
                packet_loss_ratio=0.01,
                monetary_cost=0.0,
                cost_class=CostClass.UNMETERED,
                energy_cost=400,
                security_trust=TrustLevel.TRUSTED,
                data_unlimited=True,
                application_compatibility=True,
                telemetry_timestamp=NOW - 1,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
                confidence=0.8,
            )
        ],
        obj,
    )
    for scores in d.normalized_metric_scores.values():
        for v in scores.values():
            assert math.isfinite(v)


@pytest.mark.skipif(os.environ.get("WAVE005_BROKEN_EVALUATOR"), reason="broken evaluator mode")
def test_wave005_evidence_script_and_no_abs_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Run evidence generation in-process by importing main
    import scripts.engineering_wave005.run_wave005_evidence as ev

    # Ensure script path resolves to repo root
    rc = ev.main()
    assert rc == 0
    art = ROOT / "artifacts/engineering_wave005"
    required = [
        "WAVE005_RESULT.json",
        "INTEGRITY_REPAIR_RESULT.json",
        "EVALUATOR_INTEGRITY_RESULT.json",
        "COMPLETION_GATE_NEGATIVE_CONTROL_RESULT.json",
        "APPLICATION_PRIORITY_AUTHORITY_RESULT.json",
        "APPLICATION_PRIORITY_BOUNDARY_RESULT.json",
        "USER_PREFERENCE_POLICY_RESULT.json",
        "INVALID_TELEMETRY_RESULT.json",
        "SOURCE_PROVENANCE_RESULT.json",
        "CLAIM_BOUNDARIES.json",
    ]
    for name in required:
        path = art / name
        assert path.exists(), name
        data = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(data)
        assert not ABS_RE.search(blob), name
    result = json.loads((art / "WAVE005_RESULT.json").read_text())
    assert result["wave005_ok"] is True
    assert result["summary"]["validated"] == 12
    assert result["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0
    assert result["UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED"] is True
    assert result["OS_PLATFORM_020_UNTOUCHED"] is True
    assert result["BASELINE_COUNTS_UPDATED"] is False
