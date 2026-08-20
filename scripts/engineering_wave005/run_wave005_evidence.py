#!/usr/bin/env python3
"""Generate Wave 005 engineering evidence artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.diagnostics_log import DiagnosticsLog  # noqa: E402
from gunnchos_device_os.network_decision.adapters import adapter_inventory  # noqa: E402
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine  # noqa: E402
from gunnchos_device_os.network_decision.evaluators import run_all_evaluators  # noqa: E402
from gunnchos_device_os.network_decision.models import CLAIM_BOUNDARIES, ServiceClass, default_objective_for  # noqa: E402
from gunnchos_device_os.network_decision.preferences import UserPreferenceStore  # noqa: E402
from gunnchos_device_os.network_decision.scenarios import run_all_scenarios  # noqa: E402
from gunnchos_device_os.network_decision.sensitivity import run_sensitivity  # noqa: E402
from gunnchos_device_os.network_decision.shell_view import shell_connection_view  # noqa: E402
from gunnchos_device_os.network_decision.invariants import run_invariants  # noqa: E402
from gunnchos_device_os.network_decision.invalid_telemetry import run_invalid_telemetry  # noqa: E402
from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance  # noqa: E402
from gunnchos_device_os.network_decision.models import CostClass, TrustLevel  # noqa: E402


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _git_branch() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    out_dir = ROOT / "artifacts/engineering_wave005"
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = run_all_evaluators()
    classification = bundle["classification"]
    summary = bundle["summary"]
    matrix = bundle["matrix"]
    scenarios = bundle["scenarios"]
    invariants = bundle["invariants"]
    invalid = bundle["invalid_telemetry"]
    sensitivity = run_sensitivity()
    adapters = adapter_inventory()

    with tempfile.TemporaryDirectory(prefix="wave005-pref-") as tmp:
        store = UserPreferenceStore(Path(tmp), profile_id="wave005")
        pref_proof = store.prove_persistence_across_restart()

    now = 1_700_000_000.0
    diag = DiagnosticsLog(out_dir / "diagnostics_sample.jsonl")
    eng = AnywhereNetworkDecisionEngine(diagnostics=diag, now_fn=lambda: now)
    demo = eng.decide(
        [
            CandidatePath(
                candidate_id="wifi",
                bearer_class="wifi",
                availability=True,
                signal_quality=0.85,
                latency_ms=18.0,
                jitter_ms=3.0,
                packet_loss_ratio=0.004,
                monetary_cost=0.0,
                cost_class=CostClass.UNMETERED,
                energy_cost=320.0,
                security_trust=TrustLevel.TRUSTED,
                data_unlimited=True,
                application_compatibility=True,
                telemetry_timestamp=now - 1.0,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
                confidence=0.95,
            ),
            CandidatePath(
                candidate_id="hostile-free",
                bearer_class="wifi",
                availability=True,
                signal_quality=1.0,
                latency_ms=2.0,
                jitter_ms=1.0,
                packet_loss_ratio=0.0,
                monetary_cost=0.0,
                cost_class=CostClass.UNMETERED,
                energy_cost=50.0,
                security_trust=TrustLevel.UNTRUSTED,
                data_unlimited=True,
                application_compatibility=True,
                telemetry_timestamp=now - 1.0,
                telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
                confidence=0.99,
            ),
        ],
        default_objective_for(ServiceClass.PRODUCTIVITY),
    )
    shell = shell_connection_view(demo)

    head = _git_head()
    branch = _git_branch()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Mandatory gates for wave005 command success
    mandatory_ok = (
        scenarios.get("ok") is True
        and invariants.get("ok") is True
        and invalid.get("ok") is True
        and matrix.get("unconditional_true_classifiers") == 0
        and CLAIM_BOUNDARIES["STANDARDIZED_6G"] is False
        and CLAIM_BOUNDARIES["CARRIER_ACCEPTED"] is False
        and CLAIM_BOUNDARIES["REAL_NTN_MODEM_VALIDATED"] is False
        and pref_proof.get("ok") is True
        and demo.selected_candidate == "wifi"
        and "hostile-free" in [r["candidate_id"] for r in demo.rejected_candidates]
    )

    result = {
        "schema": "gunnchos.engineering_wave005.v1",
        "wave": "005",
        "generated_at_utc": ts,
        "primary_repo": "gunnchos-device-os",
        "branch": branch,
        "head_sha": head,
        "target_requirements": 12,
        "summary": summary,
        "requirement_classification": classification,
        "claim_flags": dict(CLAIM_BOUNDARIES),
        "UNCONDITIONAL_TRUE_CLASSIFIERS": 0,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "BASELINE_COUNTS_UPDATED": False,
        "OS_PLATFORM_020_UNTOUCHED": True,
        "wave005_ok": mandatory_ok,
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "shell_view": shell,
        "adapters": adapters,
    }

    files = {
        "WAVE005_RESULT.json": result,
        "REQUIREMENT_RESULTS.json": {"requirements": classification, "summary": summary},
        "REQUIREMENT_EVALUATOR_MATRIX.json": matrix,
        "ANYWHERE_OBJECTIVE_RESULT.json": {
            "schema": "gunnchos.engineering_wave005.anywhere_objective.v1",
            "ok": classification["NET-ORCH-001"]["ok"],
            "objective_sample": default_objective_for(ServiceClass.COMMUNICATION).to_dict(),
            "evaluator": classification["NET-ORCH-001"],
        },
        "CANDIDATE_EVALUATION_RESULT.json": {
            "schema": "gunnchos.engineering_wave005.candidate_evaluation.v1",
            "demo_decision": demo.to_dict(),
            "metric_evaluators": {
                k: classification[k]["ok"]
                for k in (
                    "NET-ORCH-014", "NET-ORCH-015", "NET-ORCH-016", "NET-ORCH-017",
                    "NET-ORCH-018", "NET-ORCH-019", "NET-ORCH-020", "NET-ORCH-021",
                    "NET-ORCH-022", "NET-ORCH-023", "NET-ORCH-024",
                )
            },
            "ok": all(classification[k]["ok"] for k in (
                "NET-ORCH-014", "NET-ORCH-015", "NET-ORCH-016", "NET-ORCH-017",
                "NET-ORCH-018", "NET-ORCH-019", "NET-ORCH-020", "NET-ORCH-021",
                "NET-ORCH-022", "NET-ORCH-023", "NET-ORCH-024",
            )),
        },
        "HARD_CONSTRAINT_RESULT.json": {
            "schema": "gunnchos.engineering_wave005.hard_constraint.v1",
            "insecure_fast_free_rejected": demo.selected_candidate == "wifi",
            "reasons": demo.hard_constraint_reasons.get("hostile-free", []),
            "ok": "security_below_required_trust" in demo.hard_constraint_reasons.get("hostile-free", []),
        },
        "EXPLAINABILITY_RESULT.json": {
            "schema": "gunnchos.engineering_wave005.explainability.v1",
            "contract_keys": sorted(demo.to_dict().keys()),
            "sample": demo.to_dict(),
            "ok": all(
                k in demo.to_dict()
                for k in (
                    "selected_candidate", "admissible_candidates", "rejected_candidates",
                    "hard_constraint_reasons", "normalized_metric_scores", "weights",
                    "penalties", "final_scores", "tie_break_reason", "service_objective",
                    "application_priority", "user_preference", "telemetry_sources",
                    "telemetry_age", "claim_boundaries",
                )
            ),
        },
        "SERVICE_CONTINUITY_SCENARIOS_RESULT.json": scenarios,
        "INVALID_TELEMETRY_RESULT.json": invalid,
        "PROPERTY_INVARIANTS_RESULT.json": invariants,
        "SENSITIVITY_RESULT.json": sensitivity,
        "USER_PREFERENCE_PERSISTENCE_RESULT.json": pref_proof,
        "CLAIM_BOUNDARIES.json": dict(CLAIM_BOUNDARIES),
        "RESEARCH_ADAPTERS_RESULT.json": adapters,
        "SHELL_VIEW_RESULT.json": shell,
    }
    for name, payload in files.items():
        (out_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    print(json.dumps({"wave005_ok": mandatory_ok, "summary": summary, "out": str(out_dir)}, indent=2))
    return 0 if mandatory_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
