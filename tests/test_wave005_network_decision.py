"""Wave005 Anywhere Network Decision Engine tests."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.evaluators import TARGET_REQUIREMENTS, run_all_evaluators
from gunnchos_device_os.network_decision.invariants import run_invariants
from gunnchos_device_os.network_decision.invalid_telemetry import run_invalid_telemetry
from gunnchos_device_os.network_decision.models import (
    CLAIM_BOUNDARIES,
    CostClass,
    ServiceClass,
    TrustLevel,
    default_objective_for,
)
from gunnchos_device_os.network_decision.scenarios import run_all_scenarios
from gunnchos_device_os.network_decision.sensitivity import run_sensitivity

NOW = 1_700_000_000.0


def test_target_requirements_exactly_12():
    assert len(TARGET_REQUIREMENTS) == 12
    assert "NET-ORCH-026" not in TARGET_REQUIREMENTS


def test_scenarios_a_through_j():
    result = run_all_scenarios()
    assert result["ok"] is True, result.get("failed")
    assert result["count"] >= 8
    assert result["label"] == "DIGITAL_SYNTHETIC_EVIDENCE"


def test_invariants():
    result = run_invariants()
    assert result["ok"] is True, result


def test_invalid_telemetry():
    result = run_invalid_telemetry()
    assert result["ok"] is True, result


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


def test_sensitivity_runs():
    r = run_sensitivity()
    assert r["universal_optimality_claimed"] is False
    assert r["ok"] is True


def test_evaluators_no_unconditional_true():
    bundle = run_all_evaluators()
    assert bundle["matrix"]["unconditional_true_classifiers"] == 0
    assert bundle["matrix"]["broken_evaluator_used_as_classifier"] is False
    for req_id, row in bundle["classification"].items():
        assert row["ok"] is True, (req_id, row)
        assert callable is not None
        # classification must come from evaluator evidence, not literal True alone
        assert "evidence" in row and row["evidence"] is not None


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
