"""CX3.3 read-only WAIKE release-lane discovery — never mutates WAIKE or Device Lab."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx3_2.waike_adapter import WaikeReadOnlyAdapter
from gunnchos_device_os.cx3_2.waike_discovery import EXPECTED_MERGE_16, discover_waike_repo, run_discovery
from gunnchos_device_os.cx3_3.paths import DEVICE_LAB_134_TIP


def _git(cwd: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _load(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def run_release_lane_discovery(repo: Path) -> Dict[str, Any]:
    """Inspect accepted-main WAIKE + local release evidence; fail closed on fabrication."""
    base = run_discovery()
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx3_3.waike_release_dependency_discovery.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_discovery": base,
        "device_lab_134_expected_tip": DEVICE_LAB_134_TIP,
        "waike_mutated": False,
        "device_lab_mutated": False,
        "certification_claimed": False,
        "inferred_from_forbidden_sources": False,
    }

    waike = discover_waike_repo()
    main_sha = base.get("main_sha")
    out["waike_main_sha"] = main_sha
    out["pr16_ancestry"] = bool(base.get("pr16_ancestry"))
    out["expected_merge_16"] = EXPECTED_MERGE_16

    # Device OS #134 tip (read-only observation of local/remote tip if present)
    device_os = Path(
        "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os"
    )
    tip_134 = ""
    if (device_os / ".git").exists() or (device_os / ".git").is_file():
        tip_134 = _git(device_os, "rev-parse", "origin/cursor/device-lab-current-pin-revalidation") or _git(
            device_os, "rev-parse", "cursor/device-lab-current-pin-revalidation"
        )
    out["device_lab_134_observed_tip"] = tip_134 or None
    out["device_lab_134_tip_matches_expected"] = tip_134 == DEVICE_LAB_134_TIP if tip_134 else False

    # Probe release evidence tokens without treating diagnostics as academic achievement
    lab_root = (
        device_os
        / ".worktrees"
        / "device-lab-current-pin-revalidation"
        / "artifacts"
        / "device_lab_current_pin"
        / "waike"
        / "gui_journey"
    )
    assessment = _load(lab_root / "WAIKE_ASSESSMENT_SUBMISSION_17G5D.json")
    learner = _load(lab_root / "WAIKE_LEARNER_GUI_JOURNEY.json")
    runtime_token_files: List[str] = []
    for p in lab_root.glob("*.json") if lab_root.is_dir() else []:
        runtime_token_files.append(p.name)
    out["release_evidence_files"] = runtime_token_files
    out["assessment_submission_pass"] = bool(assessment.get("pass"))
    out["learner_gui_complete"] = bool(learner.get("complete"))
    out["WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(
        assessment.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS")
        or learner.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS")
        or False
    )

    # Genuine earned evidence requires attributable completion — not healthz/login/fixture alone
    genuine = bool(
        base.get("can_expose_real_completed_learning_evidence_readonly")
        and out["assessment_submission_pass"]
        and out["learner_gui_complete"]
        and out["WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"]
    )
    # Explicitly refuse inference from forbidden sources
    forbidden_alone = not genuine
    reason = "RELEASE_TRAIN_DEPENDENCY_PENDING"
    if not waike:
        reason = "WAIKE_REPO_NOT_FOUND"
    elif not out["pr16_ancestry"]:
        reason = "PR16_ANCESTRY_MISSING"
    elif forbidden_alone:
        reason = "RELEASE_TRAIN_DEPENDENCY_PENDING"

    out["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"] = genuine
    out["reason"] = reason if not genuine else ""
    out["ok"] = True
    out["readonly"] = True

    adapter = WaikeReadOnlyAdapter(discovery=base)
    adapter_status = adapter.adapter_status()
    out["adapter"] = adapter_status
    out["CX3_WAIKE_READ_ONLY_PROVIDER_PASS"] = bool(adapter_status.get("CX3_WAIKE_READ_ONLY_PROVIDER_PASS"))
    out["CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"] = bool(adapter_status.get("CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"))
    mismatch = adapter.mismatch_detection_demo()
    out["mismatch"] = mismatch
    out["CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS"] = bool(
        mismatch.get("CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS")
    )

    # Conditional Track A journey record (honest false when unavailable)
    journey: Dict[str, Any] = {
        "schema": "gunnchos.cx3_3.real_waike_earned_credential.v1",
        "attempted": False,
        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False,
        "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": genuine,
        "reason": reason if not genuine else "",
        "fabricated": False,
        "certification_claimed": False,
    }
    if genuine:
        journey["attempted"] = True
        achievements = adapter.list_completed_achievements()
        if achievements:
            evidence = adapter.map_to_evidence_record(achievements[0])
            elig = adapter.credential_eligibility(evidence)
            journey["eligibility"] = elig
            journey["CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = bool(elig.get("eligible"))
        else:
            journey["reason"] = "no_achievements_returned"
            journey["CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = False
    out["earned_credential_journey"] = journey
    return out
