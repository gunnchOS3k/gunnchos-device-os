"""Read-only accepted-main WAIKE discovery — never mutates WAIKE."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

EXPECTED_MERGE_16 = "34fb050ccabec813cef4811d64581b32453e1ec2"


def _git(cwd: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def discover_waike_repo(candidates: Optional[List[Path]] = None) -> Optional[Path]:
    roots = candidates or []
    # Common sibling / mirror locations
    here = Path(__file__).resolve()
    guesses = [
        Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-waike-learning-platform"),
        here.parents[4] / "gunnchos-waike-learning-platform",
        here.parents[3] / "gunnchos-waike-learning-platform",
    ]
    for g in list(roots) + guesses:
        if g and (g / ".git").exists() and (g / "services" / "hub").exists():
            return g
    return None


def run_discovery(repo: Optional[Path] = None) -> Dict[str, Any]:
    waike = discover_waike_repo([repo] if repo else None)
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx3_2.waike_accepted_main_discovery.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "waike_path": str(waike) if waike else None,
        "expected_merge_16": EXPECTED_MERGE_16,
        "certification_claimed": False,
        "waike_mutated": False,
    }
    if not waike:
        out["ok"] = False
        out["blocker"] = "WAIKE_REPO_NOT_FOUND"
        return out

    main_sha = _git(waike, "rev-parse", "origin/main") or _git(waike, "rev-parse", "HEAD")
    contains_16 = _git(waike, "merge-base", "--is-ancestor", EXPECTED_MERGE_16, main_sha or "HEAD")
    # merge-base --is-ancestor returns exit via check_output empty on success — use explicit
    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", EXPECTED_MERGE_16, main_sha or "HEAD"],
            cwd=waike,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ancestry = True
    except Exception:
        ancestry = False

    hub_routes = [
        "GET /api/v1/assignments/{id}/mastery",
        "GET /api/v1/submissions/{id}",
        "GET /api/v1/submissions/{id}/receipt",
        "GET /api/v1/sections/{id}/gradebook",
        "GET /api/v1/gradebook",
        "POST /api/v1/assignments/{id}/submissions (write — NOT used by CX3.2 adapter)",
    ]
    schemas = []
    for rel in (
        "contracts/schemas/assessment.v1.json",
        "contracts/schemas/assessment_lifecycle/submission_receipt.v1.json",
        "contracts/schemas/rubric.v1.json",
        "contracts/deviceos/WAIKE_LEARNING_OS_INTEGRATION_CONTRACT.json",
    ):
        p = waike / rel
        schemas.append({"path": rel, "exists": p.is_file()})

    # Honest: Device Lab release-train does not currently expose trustworthy completion
    lab_evidence_available = False
    lab_reason = "RELEASE_TRAIN_DEPENDENCY_PENDING"
    # Probe known Device Lab journey artifacts (read-only) without treating diagnostics as academic achievement
    lab_probe = Path(
        "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os"
        "/.worktrees/device-lab-current-pin-revalidation/artifacts/device_lab_current_pin/waike/gui_journey"
        "/WAIKE_ASSESSMENT_SUBMISSION_17G5D.json"
    )
    assessment_pass = False
    if lab_probe.is_file():
        try:
            assessment_pass = bool(json.loads(lab_probe.read_text()).get("pass"))
        except Exception:
            assessment_pass = False
    learner_journey = lab_probe.parent / "WAIKE_LEARNER_GUI_JOURNEY.json"
    learner_complete = False
    if learner_journey.is_file():
        try:
            learner_complete = bool(json.loads(learner_journey.read_text()).get("complete"))
        except Exception:
            learner_complete = False

    can_expose_real_completion = bool(assessment_pass and learner_complete)
    if not can_expose_real_completion:
        lab_evidence_available = False
        lab_reason = "RELEASE_TRAIN_DEPENDENCY_PENDING"

    out.update(
        {
            "ok": True,
            "main_sha": main_sha,
            "pr16_ancestry": ancestry,
            "main_matches_expected": main_sha == EXPECTED_MERGE_16,
            "hub_apis": hub_routes,
            "schemas": schemas,
            "auth_model": "actor bearer/session via Hub require_actor (learner/instructor roles)",
            "can_expose_real_completed_learning_evidence_readonly": can_expose_real_completion,
            "device_lab_trustworthy_completion_available": lab_evidence_available,
            "lab_blocker_reason": lab_reason,
            "assessment_submission_pass": assessment_pass,
            "learner_gui_complete": learner_complete,
            "readonly": True,
        }
    )
    return out
