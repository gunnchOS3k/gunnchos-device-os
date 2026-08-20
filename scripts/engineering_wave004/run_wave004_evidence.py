#!/usr/bin/env python3
"""Generate Wave 004 engineering evidence artifacts (final integrity correction)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator  # noqa: E402
from gunnchos_device_os.platform.persistent_sync import (  # noqa: E402
    prove_corruption_failures,
    run_a_b_c_restart_proof,
)


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    out_dir = ROOT / "artifacts/engineering_wave004"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wave004-evidence-") as tmp:
        tmp_path = Path(tmp)
        coord = Wave004PlatformCoordinator(tmp_path)
        validation = coord.run_full_validation()
        classification = validation["requirement_classification"]
        matrix = validation["evaluator_matrix"]
        runtime_status = coord.status()
        package_proof = coord.package_lifecycle.run_full_lifecycle_proof("evidence-pkg")
        package_negatives = coord.package_lifecycle.run_negative_proofs()
        abc = run_a_b_c_restart_proof(tmp_path / "abc_evidence")
        corruption = prove_corruption_failures(tmp_path / "corrupt_evidence")
        sandbox = coord.sandbox_executor.run_enforcement_suite("evidence-sandbox")

    summary = {
        "validated": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTED_AND_VALIDATED"),
        "implemented_validation_open": sum(
            1 for v in classification.values() if v["classification"] == "IMPLEMENTED_VALIDATION_OPEN"
        ),
        "implementation_open": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTATION_OPEN"),
        "blocked_environment": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_ENVIRONMENT"),
        "blocked_external": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_EXTERNAL"),
        "total": len(classification),
    }
    head = _git_head()
    primary_targets = ["OS-PLATFORM-008", "OS-PLATFORM-012", "OS-PLATFORM-020"]
    all_12 = summary["validated"] == 12 and validation["ok"]
    repair_status = "COMPLETE" if all_12 else "PARTIAL"
    claim_flags = dict(validation["claim_flags"])
    claim_flags["KERNEL_SANDBOX"] = bool(sandbox.get("KERNEL_SANDBOX"))
    claim_flags["PRODUCTION_SIGNING"] = False

    final_integrity = {
        "schema": "gunnchos.engineering_wave004.final_integrity.v1",
        "wave": "004",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": "eng/wave004-final-integrity",
        "head_sha": head,
        "historical_device_os_pr_124": 124,
        "historical_field_kit_pr_97": 97,
        "historical_device_os_pr_125": 125,
        "historical_field_kit_pr_98": 98,
        "PRIMARY_REPAIR_TARGETS": primary_targets,
        "WAVE004_FINAL_INTEGRITY_CLOSURE": repair_status,
        "validated_count": summary["validated"],
        "target_requirements": 12,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": 0,
        "COMPLETE_GATE_REQUIRES_12_OF_12": True,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "BASELINE_COUNTS_UPDATED": False,
        "DO_NOT_MERGE_UNTIL_WAVE004_FINAL_INTEGRITY_ACCEPTED": True,
        "repair_summary": {req: classification.get(req, {}) for req in primary_targets},
        "claim_flags": claim_flags,
        "wave004_ok": validation["ok"],
        "sandbox": {
            "SANDBOX_BACKEND": sandbox.get("SANDBOX_BACKEND"),
            "KERNEL_SANDBOX": sandbox.get("KERNEL_SANDBOX"),
            "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
            "LOCAL_SANDBOX_VALIDATION": sandbox.get("LOCAL_SANDBOX_VALIDATION"),
            "SANDBOX_EXECUTION_VALIDATED": sandbox.get("SANDBOX_EXECUTION_VALIDATED"),
        },
    }
    result = {
        "schema": "gunnchos.engineering_wave004.v1",
        "wave": "004",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_repo": "gunnchos-device-os",
        "branch": "eng/wave004-final-integrity",
        "head_sha": head,
        "target_requirements": 12,
        "summary": summary,
        "requirement_classification": classification,
        "e2e_scenarios": validation["e2e"],
        "security_injection": validation["security_injection"],
        "claim_flags": claim_flags,
        "UNCONDITIONAL_TRUE_CLASSIFIERS": 0,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "BASELINE_COUNTS_UPDATED": False,
        "wave004_ok": validation["ok"],
        "WAVE004_FINAL_INTEGRITY_CLOSURE": repair_status,
    }
    package_result = {
        "schema": "gunnchos.engineering_wave004.package_full_lifecycle.v1",
        "ok": package_proof.get("ok") and package_negatives.get("ok"),
        "lifecycle": package_proof,
        "negatives": package_negatives,
        "PRODUCTION_SIGNING": False,
    }
    abc_result = {
        **abc,
        "corruption_proof_ok": corruption.get("ok"),
    }
    sandbox_result = {
        "schema": "gunnchos.engineering_wave004.sandbox_enforcement.v1",
        **{k: sandbox.get(k) for k in (
            "SANDBOX_BACKEND",
            "KERNEL_SANDBOX",
            "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX",
            "HOST_PRIVATE_READ_BLOCKED",
            "OUTSIDE_WRITE_BLOCKED",
            "NETWORK_DENIED",
            "NETWORK_CONTROL_REACHABLE",
            "CHILD_SPAWN_DENIED",
            "CROSS_APP_READ_BLOCKED",
            "PRIVILEGED_CAPABILITY_DENIED",
            "SANDBOX_EXECUTION_VALIDATED",
            "LOCAL_SANDBOX_VALIDATION",
            "ok",
            "fixture_result",
            "claim_boundary",
        )},
    }
    files = {
        "WAVE004_RESULT.json": result,
        "FINAL_INTEGRITY_RESULT.json": final_integrity,
        "PACKAGE_FULL_LIFECYCLE_RESULT.json": package_result,
        "OFFLINE_SYNC_A_B_C_RESTART_RESULT.json": abc_result,
        "SANDBOX_ENFORCEMENT_RESULT.json": sandbox_result,
        "REQUIREMENT_EVALUATOR_MATRIX.json": matrix,
        "REQUIREMENT_RESULTS.json": {"requirements": classification, "summary": summary},
        "E2E_SCENARIOS_RESULT.json": validation["e2e"],
        "SECURITY_INJECTION_RESULT.json": validation["security_injection"],
        "CLAIM_BOUNDARIES.json": {"claim_flags": claim_flags},
        "RUNTIME_STATUS.json": runtime_status,
    }
    for name, payload in files.items():
        (out_dir / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": validation["ok"],
                "path": str(out_dir / "FINAL_INTEGRITY_RESULT.json"),
                "summary": summary,
                "repair_status": repair_status,
                "sandbox_backend": sandbox.get("SANDBOX_BACKEND"),
                "LOCAL_SANDBOX_VALIDATION": sandbox.get("LOCAL_SANDBOX_VALIDATION"),
            },
            indent=2,
        )
    )
    # Evidence generation succeeds even when PARTIAL (honest local macOS).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
