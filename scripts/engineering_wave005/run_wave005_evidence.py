#!/usr/bin/env python3
"""Generate Wave 005 engineering evidence artifacts (integrity repair)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.diagnostics_log import DiagnosticsLog  # noqa: E402
from gunnchos_device_os.network_decision.adapters import adapter_inventory  # noqa: E402
from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance  # noqa: E402
from gunnchos_device_os.network_decision.completion_gate import (  # noqa: E402
    evaluate_completion_gate,
    run_negative_controls,
)
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine  # noqa: E402
from gunnchos_device_os.network_decision.evaluators import run_all_evaluators  # noqa: E402
from gunnchos_device_os.network_decision.models import (  # noqa: E402
    CLAIM_BOUNDARIES,
    CostClass,
    ServiceClass,
    TrustLevel,
    default_objective_for,
)
from gunnchos_device_os.network_decision.preferences import (  # noqa: E402
    UserPreferenceStore,
    prove_user_preference_policy,
)
from gunnchos_device_os.network_decision.priority_authority import (  # noqa: E402
    prove_priority_only_boundary,
    prove_self_asserted_critical_blocked,
)
from gunnchos_device_os.network_decision.shell_view import shell_connection_view  # noqa: E402
from gunnchos_device_os.network_decision.sensitivity import run_sensitivity  # noqa: E402


ABS_PATH_RE = re.compile(r"(/Users/|/home/|/mnt/|/tmp/|[A-Za-z]:\\\\)")


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


def _tree_hash(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():
            h.update(path.as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def _redact_abs(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _redact_abs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_abs(v) for v in obj]
    if isinstance(obj, str):
        if ABS_PATH_RE.search(obj):
            # convert absolute to repo-relative when possible
            try:
                p = Path(obj)
                if p.is_absolute():
                    try:
                        return str(p.relative_to(ROOT))
                    except ValueError:
                        # sibling repo under spine
                        parts = p.parts
                        if "repos" in parts:
                            idx = parts.index("repos")
                            return "/".join(parts[idx + 1 :])
            except Exception:
                pass
            return "<redacted_absolute_path>"
        return obj
    return obj


def _assert_no_abs_in_payload(payload: Any, *, name: str) -> None:
    blob = json.dumps(payload, default=str)
    if ABS_PATH_RE.search(blob):
        raise SystemExit(f"absolute workstation path leaked in {name}")


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
    integrity = bundle["integrity"]
    sensitivity = run_sensitivity()
    adapters = _redact_abs(adapter_inventory())
    gate = evaluate_completion_gate(classification, integrity=integrity)
    negative = run_negative_controls()
    authority = prove_self_asserted_critical_blocked()
    boundary = prove_priority_only_boundary()

    with tempfile.TemporaryDirectory(prefix="wave005-pref-") as tmp:
        store = UserPreferenceStore(Path(tmp) / "basic", profile_id="wave005")
        pref_proof = store.prove_persistence_across_restart()
        policy_proof = prove_user_preference_policy(Path(tmp) / "policy")

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
    unconditional = int(integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"])

    nd_root = ROOT / "gunnchos_device_os" / "network_decision"
    production_paths = sorted(nd_root.glob("*.py"))
    production_tree_hash = _tree_hash(production_paths)
    evaluator_hashes = {
        row["requirement_id"]: row["source_hash"]
        for row in integrity.get("requirements", [])
    }

    provenance = {
        "schema": "gunnchos.engineering_wave005.source_provenance.v1",
        "evaluated_source_sha": head,
        "evidence_generation_sha_parent": head,
        "production_source_tree_hash": production_tree_hash,
        "evaluator_source_hashes": evaluator_hashes,
        "branch": branch,
        "note": "artifact SHA cannot equal commit containing itself; parent/evaluated sha recorded",
    }

    all_validated = (
        summary.get("validated") == 12
        and summary.get("total") == 12
        and all(
            classification[r]["classification"] == "IMPLEMENTED_AND_VALIDATED"
            and classification[r]["ok"] is True
            and classification[r].get("evidence")
            for r in classification
        )
    )

    mandatory_ok = (
        all_validated
        and gate.get("complete") is True
        and integrity.get("ok") is True
        and unconditional == 0
        and negative.get("ok") is True
        and scenarios.get("ok") is True
        and invariants.get("ok") is True
        and invalid.get("ok") is True
        and invalid.get("never_best_case_missing_invalid") is True
        and pref_proof.get("ok") is True
        and policy_proof.get("ok") is True
        and authority.get("ok") is True
        and boundary.get("ok") is True
        and CLAIM_BOUNDARIES["STANDARDIZED_6G"] is False
        and CLAIM_BOUNDARIES["CARRIER_ACCEPTED"] is False
        and CLAIM_BOUNDARIES["REAL_NTN_MODEM_VALIDATED"] is False
        and CLAIM_BOUNDARIES.get("PRODUCTION_APP_PRIORITY_SIGNING") is False
        and demo.selected_candidate == "wifi"
        and "hostile-free" in [r["candidate_id"] for r in demo.rejected_candidates]
    )

    repair_status = "PASS" if mandatory_ok else ("PARTIAL" if summary.get("validated", 0) > 0 else "FAIL")

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
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "WAVE005_COMPLETE_GATE_REQUIRES_12_OF_12": True,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "BASELINE_COUNTS_UPDATED": False,
        "OS_PLATFORM_020_UNTOUCHED": True,
        "WAVE005_POSTMERGE_INTEGRITY_REPAIR": repair_status,
        "wave005_ok": mandatory_ok,
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "shell_view": shell,
        "adapters": adapters,
        "completion_gate": gate,
    }

    integrity_repair = {
        "schema": "gunnchos.engineering_wave005.integrity_repair.v1",
        "wave": "005",
        "generated_at_utc": ts,
        "branch": branch,
        "head_sha": head,
        "historical_device_os_pr": 127,
        "historical_field_kit_pr": 101,
        "PRIMARY_REPAIR_TARGETS": ["NET-ORCH-023", "NET-ORCH-024"],
        "WAVE005_POSTMERGE_INTEGRITY_REPAIR": repair_status,
        "defects_repaired": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "validated_count": summary["validated"],
        "target_requirements": 12,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "COMPLETE_GATE_REQUIRES_12_OF_12": True,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "DO_NOT_MERGE_UNTIL_WAVE005_INTEGRITY_REPAIR_ACCEPTED": True,
        "BASELINE_COUNTS_UPDATED": False,
        "OS_PLATFORM_020_UNTOUCHED": True,
        "wave005_ok": mandatory_ok,
    }

    files = {
        "WAVE005_RESULT.json": result,
        "INTEGRITY_REPAIR_RESULT.json": integrity_repair,
        "EVALUATOR_INTEGRITY_RESULT.json": integrity,
        "COMPLETION_GATE_NEGATIVE_CONTROL_RESULT.json": negative,
        "APPLICATION_PRIORITY_AUTHORITY_RESULT.json": authority,
        "APPLICATION_PRIORITY_BOUNDARY_RESULT.json": boundary,
        "USER_PREFERENCE_POLICY_RESULT.json": policy_proof,
        "USER_PREFERENCE_PERSISTENCE_RESULT.json": pref_proof,
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
        "CLAIM_BOUNDARIES.json": dict(CLAIM_BOUNDARIES),
        "RESEARCH_ADAPTERS_RESULT.json": adapters,
        "SHELL_VIEW_RESULT.json": shell,
        "SOURCE_PROVENANCE_RESULT.json": provenance,
    }

    for name, payload in files.items():
        clean = _redact_abs(payload)
        _assert_no_abs_in_payload(clean, name=name)
        (out_dir / name).write_text(json.dumps(clean, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    print(json.dumps({
        "wave005_ok": mandatory_ok,
        "summary": summary,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "gate_complete": gate.get("complete"),
        "out": str(out_dir.relative_to(ROOT)),
    }, indent=2))
    return 0 if mandatory_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
