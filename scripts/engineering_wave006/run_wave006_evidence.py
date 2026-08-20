#!/usr/bin/env python3
"""Generate Wave 006 integrity-repair evidence artifacts."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.service_continuity_execution.adapters import adapter_inventory  # noqa: E402
from gunnchos_device_os.service_continuity_execution.completion_gate import (  # noqa: E402
    evaluate_completion_gate,
    run_negative_controls,
)
from gunnchos_device_os.service_continuity_execution.controller import ContinuityController  # noqa: E402
from gunnchos_device_os.service_continuity_execution.evaluators import run_all_evaluators  # noqa: E402
from gunnchos_device_os.service_continuity_execution.models import CLAIM_BOUNDARIES  # noqa: E402

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
            try:
                p = Path(obj)
                if p.is_absolute():
                    try:
                        return str(p.relative_to(ROOT))
                    except ValueError:
                        parts = p.parts
                        if "repos" in parts:
                            idx = parts.index("repos")
                            return "/".join(parts[idx + 1 :])
                        if "artifacts" in parts:
                            idx = parts.index("artifacts")
                            return "/".join(parts[idx:])
            except Exception:
                pass
            return "<redacted_absolute_path>"
        return obj
    return obj


def _assert_no_abs_in_payload(payload: Any, *, name: str) -> None:
    blob = json.dumps(payload, default=str)
    if ABS_PATH_RE.search(blob):
        raise SystemExit(f"absolute workstation path leaked in {name}")


def _write(out_dir: Path, name: str, payload: Any) -> None:
    payload = _redact_abs(payload)
    _assert_no_abs_in_payload(payload, name=name)
    (out_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    out_dir = ROOT / "artifacts/engineering_wave006"
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = run_all_evaluators()
    classification = bundle["classification"]
    summary = bundle["summary"]
    integrity = bundle["integrity"]
    gate = evaluate_completion_gate(classification, integrity=integrity)
    negative = run_negative_controls()
    adapters = _redact_abs(adapter_inventory())
    behavioral = bundle["behavioral_negative_controls"]

    head = _git_head()
    branch = _git_branch()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    unconditional = int(integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"])

    prod_root = ROOT / "gunnchos_device_os" / "service_continuity_execution"
    production_paths = sorted(prod_root.glob("*.py"))
    production_tree_hash = _tree_hash(production_paths)
    evaluator_hashes = {row["requirement_id"]: row["source_hash"] for row in integrity.get("requirements", [])}

    provenance = {
        "schema": "gunnchos.engineering_wave006.source_provenance.v1",
        "evaluated_source_sha": head,
        "evidence_generation_sha_parent": head,
        "production_source_tree_hash": production_tree_hash,
        "evaluator_source_hashes": evaluator_hashes,
        "branch": branch,
        "note": "artifact SHA cannot equal commit containing itself; parent/evaluated sha recorded",
        "integrity_repair": True,
        "historical_device_os_pr": 129,
        "historical_field_kit_pr": 104,
    }

    import tempfile

    with tempfile.TemporaryDirectory(prefix="wave006-shell-") as td:
        ctrl = ContinuityController(storage_dir=Path(td))
        shell = ctrl.shell_view()

    all_validated = (
        summary.get("validated") == 10
        and summary.get("total") == 10
        and gate.get("complete") is True
        and unconditional == 0
        and integrity.get("ok") is True
        and negative.get("ok") is True
        and behavioral.get("ok") is True
        and bundle["e2e"].get("ok") is True
        and bundle["failure_injection"].get("ok") is True
        and bundle["state_machine"].get("ok") is True
    )

    status = "PASS" if all_validated else ("PARTIAL" if summary.get("validated", 0) > 0 else "FAIL")

    requirement_results = {
        "schema": "gunnchos.engineering_wave006.requirement_results.v1",
        "requirements": classification,
        "summary": summary,
    }

    integrity_repair = {
        "schema": "gunnchos.engineering_wave006.integrity_repair.v1",
        "WAVE006_POSTMERGE_INTEGRITY_REPAIR": status,
        "historical_device_os_pr": 129,
        "historical_field_kit_pr": 104,
        "defects_targeted": list("ABCDEFGHIJK"),
        "BASELINE_COUNTS_UPDATED": False,
        "OS_PLATFORM_020_UNTOUCHED": True,
        "CURSOR_MERGED_NOTHING": True,
        "summary": summary,
        "status": status,
    }

    result = {
        "schema": "gunnchos.engineering_wave006.result.v1",
        "wave": "006",
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "generated_at_utc": ts,
        "head_sha": head,
        "branch": branch,
        "primary_repo": "gunnchos-device-os",
        "TARGET_REQUIREMENTS": list(bundle["target_requirements"]),
        "target_requirements": 10,
        "summary": summary,
        "requirement_classification": classification,
        "completion_gate": gate,
        "wave006_ok": all_validated,
        "WAVE006_POSTMERGE_INTEGRITY_REPAIR": status,
        "status": status,
        "PARTIAL": status == "PARTIAL",
        "UNCONDITIONAL_TRUE_CLASSIFIERS": unconditional,
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "COMPLETE_GATE_REQUIRES_10_OF_10": True,
        "WAVE006_COMPLETE_GATE_REQUIRES_10_OF_10": True,
        "BEHAVIORAL_NEGATIVE_CONTROLS_PASS": behavioral.get("ok") is True,
        "OS_PLATFORM_020_UNTOUCHED": True,
        "BASELINE_COUNTS_UPDATED": False,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "SUPPORTING_PR": "NONE",
        "claim_flags": dict(CLAIM_BOUNDARIES),
        "MULTIPATH_KIND": "APPLICATION_LEVEL_MULTIPATH",
        "adapters": adapters,
        "e2e": bundle["e2e"],
        "failure_injection": bundle["failure_injection"],
        "metrics": bundle["metrics"],
        "baselines": bundle["baselines"],
        "behavioral_negative_controls": behavioral,
        "state_machine": bundle["state_machine"],
        "READY_FOR_OWNER_MERGE": False,
        "READY_FOR_OWNER_MERGE_SEQUENCE": all_validated,
        "CURSOR_MERGED_NOTHING": True,
        "DO_NOT_MERGE_UNTIL_WAVE006_INTEGRITY_REPAIR_ACCEPTED": True,
    }

    artifacts = {
        "INTEGRITY_REPAIR_RESULT.json": integrity_repair,
        "WAVE006_RESULT.json": result,
        "REQUIREMENT_RESULTS.json": requirement_results,
        "REQUIREMENT_EVALUATOR_MATRIX.json": bundle["matrix"],
        "CLAIM_BOUNDARIES.json": dict(CLAIM_BOUNDARIES),
        "EVALUATOR_INTEGRITY_RESULT.json": integrity,
        "COMPLETION_GATE_NEGATIVE_CONTROL_RESULT.json": negative,
        "BEHAVIORAL_NEGATIVE_CONTROL_RESULT.json": behavioral,
        "E2E_SCENARIOS_A_J_RESULT.json": bundle["e2e"],
        "FAILURE_INJECTION_RESULT.json": bundle["failure_injection"],
        "RESEARCH_METRICS_RESULT.json": bundle["metrics"],
        "COMPARATIVE_BASELINES_RESULT.json": bundle["baselines"],
        "RESEARCH_ADAPTERS_RESULT.json": adapters,
        "SOURCE_PROVENANCE_RESULT.json": provenance,
        "CONTINUITY_STATE_MACHINE_RESULT.json": bundle["state_machine"],
        "SATELLITE_VISIBILITY_RESULT.json": classification["NET-ORCH-026"]["evidence"],
        "LOCAL_INFRA_RESULT.json": classification["NET-ORCH-027"]["evidence"],
        "BEARER_TRANSITION_RESULT.json": classification["NET-ORCH-028"]["evidence"],
        "BEARER_TRANSITION_TRANSACTION_RESULT.json": classification["NET-ORCH-028"]["evidence"],
        "SESSION_RESUME_A_B_C_RESULT.json": classification["NET-ORCH-029"]["evidence"],
        "APPLICATION_MULTIPATH_RESULT.json": classification["NET-ORCH-030"]["evidence"],
        "APPLICATION_MULTIPATH_TRANSFER_RESULT.json": classification["NET-ORCH-030"]["evidence"],
        "LOW_BANDWIDTH_ADAPTATION_RESULT.json": classification["NET-ORCH-031"]["evidence"],
        "TRAFFIC_PRIORITIZATION_RESULT.json": classification["NET-ORCH-032"]["evidence"],
        "TRAFFIC_SCHEDULER_STRESS_RESULT.json": classification["NET-ORCH-032"]["evidence"],
        "PERSISTENT_CACHE_A_B_C_RESULT.json": classification["NET-ORCH-033"]["evidence"],
        "CACHE_POLICY_RESULT.json": classification["NET-ORCH-033"]["evidence"],
        "OPPORTUNISTIC_SYNC_RESULT.json": classification["NET-ORCH-034"]["evidence"],
        "DEGRADED_MODE_REPORTING_RESULT.json": classification["NET-ORCH-035"]["evidence"],
        "SHELL_VIEW_RESULT.json": shell,
    }

    for name, payload in artifacts.items():
        _write(out_dir, name, payload)

    uml = """@startuml wave006_continuity_controller
title Wave006 Service-Continuity Execution Plane (Integrity Repair)
actor Telemetry
participant "Wave005\\nAnywhereNetworkDecisionEngine" as D
participant "ContinuityController" as C
database "PersistentCache\\nSessionCheckpoint\\nSyncQueue" as S
Telemetry -> C : ingest candidates + sat/infra
C -> D : decide(candidates, objective)
D --> C : DecisionExplanation
C -> C : EXECUTE KEEP/TRANSITION/RESUME/MULTIPATH/ADAPT/...
C -> S : checkpoint / cache / opportunistic sync
C --> Telemetry : canonical degraded-mode report + shell projection
note right of C
  DIGITAL/SYNTHETIC only
  LIVE_CARRIER_HANDOVER_VALIDATED=false
  PRODUCTION_MPTCP_VALIDATED=false
  REAL_NTN_MODEM_VALIDATED=false
  MULTIPATH_KIND=APPLICATION_LEVEL_MULTIPATH
end note
@enduml
"""
    (ROOT / "docs/diagrams/wave006_continuity_controller.puml").write_text(uml, encoding="utf-8")

    print(
        json.dumps(
            {
                "wave006_ok": all_validated,
                "status": status,
                "validated": summary["validated"],
                "head": head,
                "PARTIAL": status == "PARTIAL",
            },
            indent=2,
        )
    )
    # Green only for real PASS; PARTIAL/FAIL exits nonzero so CI cannot silently accept
    return 0 if all_validated else 1


if __name__ == "__main__":
    raise SystemExit(main())
