"""HumanValidationFreezeManifest v1 + freeze-check command support."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.contracts import CONTRACT_VERSION, _now
from gunnchos_device_os.cx4_validation_center.eligibility import (
    ValidationEvidenceEligibility,
    cx4_final_human_validation_eligible,
    final_gating_missing_conditions,
)
from gunnchos_device_os.cx4_validation_center.library import build_task_library, packs_summary

VALIDATION_CENTER_VERSION = "cx4.2-pilot-readiness"


@dataclass
class HumanValidationFreezeManifest:
    schema: str = "HumanValidationFreezeManifest/v1"
    validation_center_version: str = VALIDATION_CENTER_VERSION
    device_os_commit: str = ""
    portal_control_commit: str = ""
    target_release_or_main_commit: str = ""
    branch: str = ""
    branch_status: str = "draft_unmerged"
    dirty_worktree: bool = True
    task_pack_hashes: Dict[str, str] = field(default_factory=dict)
    validation_task_schema_version: str = CONTRACT_VERSION
    collector_versions: Dict[str, str] = field(default_factory=dict)
    os_build_version: str = ""
    device_sku: str = ""
    hardware_serial_alias: str = ""
    evidence_eligibility: str = ValidationEvidenceEligibility.PILOT_NON_GATING.value
    freeze_timestamp: str = ""
    materiality_policy: str = "material_ui_a11y_task_logic_evidence_pipeline_device_behavior"
    build_frozen: bool = False
    application_provenance: Dict[str, Any] = field(default_factory=dict)
    hardware_prerequisites_real: bool = False
    cx_stack_draft_unmerged: bool = True
    material_drift_detected: bool = False
    final_gating_eligible: bool = False
    missing_conditions: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return ""


def _pack_hashes() -> Dict[str, str]:
    lib = build_task_library()
    by_pack: Dict[str, List[str]] = {}
    for t in lib:
        by_pack.setdefault(t.pack_id, []).append(
            json.dumps(t.to_dict(), sort_keys=True, separators=(",", ":"))
        )
    out: Dict[str, str] = {}
    for pack_id, blobs in sorted(by_pack.items()):
        digest = hashlib.sha256("\n".join(sorted(blobs)).encode("utf-8")).hexdigest()
        out[pack_id] = digest
    return out


def build_freeze_manifest(
    repo_root: Path,
    *,
    portal_control_commit: str = "",
    device_sku: str = "",
    os_build_version: str = "",
    hardware_serial_alias: str = "",
) -> HumanValidationFreezeManifest:
    repo_root = Path(repo_root)
    commit = _git(repo_root, "rev-parse", "HEAD")
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(_git(repo_root, "status", "--porcelain"))
    from gunnchos_device_os.cx4_validation_center.collectors import list_collectors

    collectors = {c["id"]: c.get("version", "v1") for c in list_collectors()}
    packs = packs_summary()
    manifest = HumanValidationFreezeManifest(
        device_os_commit=commit,
        portal_control_commit=portal_control_commit,
        target_release_or_main_commit="",  # unknown until accepted RC
        branch=branch,
        branch_status="draft_unmerged",
        dirty_worktree=dirty,
        task_pack_hashes=_pack_hashes(),
        collector_versions=collectors,
        os_build_version=os_build_version or VALIDATION_CENTER_VERSION,
        device_sku=device_sku,
        hardware_serial_alias=hardware_serial_alias,
        evidence_eligibility=ValidationEvidenceEligibility.PILOT_NON_GATING.value,
        freeze_timestamp=_now(),
        build_frozen=False,
        application_provenance={
            "validation_center_version": VALIDATION_CENTER_VERSION,
            "packs": [p["pack_id"] for p in packs],
            "commit": commit,
            "branch": branch,
        },
        hardware_prerequisites_real=False,
        cx_stack_draft_unmerged=True,
        material_drift_detected=False,
    )
    freeze_dict = manifest.to_dict()
    missing = final_gating_missing_conditions(freeze=freeze_dict)
    manifest.missing_conditions = missing
    manifest.final_gating_eligible = cx4_final_human_validation_eligible(freeze_dict) and len(missing) == 0
    if not manifest.final_gating_eligible:
        manifest.evidence_eligibility = ValidationEvidenceEligibility.PILOT_NON_GATING.value
        manifest.notes = (
            "FINAL_GATING_ELIGIBLE=false because the CX stack is still DRAFT/unmerged "
            "and required freeze conditions are not satisfied. "
            "Missing: " + ", ".join(missing)
        )
    return manifest


def freeze_check(repo_root: Path, **kwargs: Any) -> Dict[str, Any]:
    """Run freeze-check. Returns manifest + token CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS=true when check works."""
    manifest = build_freeze_manifest(repo_root, **kwargs)
    d = manifest.to_dict()
    return {
        "ok": True,
        "CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS": True,
        "CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE": bool(d.get("final_gating_eligible")),
        "FINAL_GATING_ELIGIBLE": bool(d.get("final_gating_eligible")),
        "missing_conditions": d.get("missing_conditions") or [],
        "manifest": d,
        "explanation": d.get("notes")
        or "Freeze check executed. Final gating eligibility is false until an accepted build exists.",
    }
