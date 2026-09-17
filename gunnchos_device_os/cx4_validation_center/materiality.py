"""Material-drift compare-freeze engine — deterministic invalidation of affected packs."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from gunnchos_device_os.cx4_validation_center.eligibility import ValidationEvidenceEligibility
from gunnchos_device_os.cx4_validation_center.freeze import build_freeze_manifest
from gunnchos_device_os.cx4_validation_center.library import build_task_library


class MaterialityClass(str, Enum):
    NON_MATERIAL = "NON_MATERIAL"
    MATERIAL_UI = "MATERIAL_UI"
    MATERIAL_ACCESSIBILITY = "MATERIAL_ACCESSIBILITY"
    MATERIAL_TASK_LOGIC = "MATERIAL_TASK_LOGIC"
    MATERIAL_EVIDENCE_PIPELINE = "MATERIAL_EVIDENCE_PIPELINE"
    MATERIAL_DEVICE_BEHAVIOR = "MATERIAL_DEVICE_BEHAVIOR"
    UNKNOWN = "UNKNOWN"


# Paths / keys that map to materiality classes when hashes differ.
PATH_CLASS_RULES = (
    (("apps/validation_center/src/styles.css", "apps/validation_center/index.html"), MaterialityClass.MATERIAL_UI),
    (("apps/validation_center/src/app.js", "a11y", "accessibility"), MaterialityClass.MATERIAL_ACCESSIBILITY),
    (("gunnchos_device_os/cx4_validation_center/library.py", "task_pack", "participant_steps"), MaterialityClass.MATERIAL_TASK_LOGIC),
    (("gunnchos_device_os/cx4_validation_center/export.py", "store.py", "collectors.py", "evidence"), MaterialityClass.MATERIAL_EVIDENCE_PIPELINE),
    (("device", "firmware", "peripheral", "printer", "camera"), MaterialityClass.MATERIAL_DEVICE_BEHAVIOR),
)


def _sha(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def classify_change(key: str) -> MaterialityClass:
    lower = key.lower()
    for needles, klass in PATH_CLASS_RULES:
        if any(n.lower() in lower for n in needles):
            return klass
    if lower.startswith("docs/") or lower.endswith(".md"):
        return MaterialityClass.NON_MATERIAL
    if "token" in lower or "readme" in lower:
        return MaterialityClass.NON_MATERIAL
    return MaterialityClass.UNKNOWN


def _submission_freeze_snapshot(submission: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comparable freeze fields from a submission or embedded freeze."""
    if "manifest" in submission and isinstance(submission.get("freeze_manifest"), dict):
        return submission["freeze_manifest"]
    prov = submission.get("provenance") or {}
    man = submission.get("manifest") or {}
    return {
        "device_os_commit": prov.get("commit") or man.get("commit") or "",
        "branch": prov.get("branch") or man.get("branch") or "",
        "task_pack_hashes": submission.get("task_pack_hashes") or man.get("task_pack_hashes") or {},
        "validation_task_schema_version": submission.get("contract_version") or "v1",
        "collector_versions": submission.get("collector_versions") or {},
        "pack_ids": man.get("pack_ids") or [],
        "task_ids": man.get("task_ids") or [],
        "build_version": man.get("build_version") or "",
        "ui_fingerprint": submission.get("ui_fingerprint") or "",
        "a11y_fingerprint": submission.get("a11y_fingerprint") or "",
        "evidence_pipeline_fingerprint": submission.get("evidence_pipeline_fingerprint") or "",
    }


def current_build_snapshot(repo_root: Path) -> Dict[str, Any]:
    freeze = build_freeze_manifest(repo_root).to_dict()
    app = Path(repo_root) / "apps" / "validation_center"
    ui_parts = []
    for rel in ("index.html", "src/app.js", "src/styles.css"):
        p = app / rel
        if p.is_file():
            ui_parts.append(hashlib.sha256(p.read_bytes()).hexdigest())
    lib = build_task_library()
    task_logic = _sha([t.to_dict() for t in lib])
    pipeline_files = [
        Path(repo_root) / "gunnchos_device_os" / "cx4_validation_center" / name
        for name in ("store.py", "export.py", "collectors.py", "eligibility.py")
    ]
    pipe = _sha([p.read_text(encoding="utf-8") if p.is_file() else "" for p in pipeline_files])
    return {
        "device_os_commit": freeze.get("device_os_commit"),
        "branch": freeze.get("branch"),
        "task_pack_hashes": freeze.get("task_pack_hashes") or {},
        "validation_task_schema_version": freeze.get("validation_task_schema_version"),
        "collector_versions": freeze.get("collector_versions") or {},
        "ui_fingerprint": _sha(ui_parts),
        "a11y_fingerprint": _sha(ui_parts + ["a11y"]),
        "evidence_pipeline_fingerprint": pipe,
        "task_logic_fingerprint": task_logic,
        "build_version": freeze.get("os_build_version"),
    }


def compare_freeze(
    submission: Dict[str, Any],
    current_build: Optional[Dict[str, Any]] = None,
    *,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare a submission freeze snapshot against current build; classify materiality."""
    if current_build is None:
        if repo_root is None:
            raise ValueError("repo_root_or_current_build_required")
        current_build = current_build_snapshot(Path(repo_root))

    prior = _submission_freeze_snapshot(submission)
    changes: List[Dict[str, Any]] = []
    classes: Set[str] = set()

    def note(key: str, before: Any, after: Any) -> None:
        if before == after:
            return
        klass = classify_change(key)
        classes.add(klass.value)
        changes.append(
            {
                "key": key,
                "before": before,
                "after": after,
                "class": klass.value,
            }
        )

    note("device_os_commit", prior.get("device_os_commit"), current_build.get("device_os_commit"))
    note("branch", prior.get("branch"), current_build.get("branch"))
    note(
        "validation_task_schema_version",
        prior.get("validation_task_schema_version"),
        current_build.get("validation_task_schema_version"),
    )
    note("ui_fingerprint", prior.get("ui_fingerprint") or "", current_build.get("ui_fingerprint"))
    note("a11y_fingerprint", prior.get("a11y_fingerprint") or "", current_build.get("a11y_fingerprint"))
    note(
        "evidence_pipeline_fingerprint",
        prior.get("evidence_pipeline_fingerprint") or "",
        current_build.get("evidence_pipeline_fingerprint"),
    )
    note(
        "task_logic_fingerprint",
        prior.get("task_logic_fingerprint") or prior.get("task_pack_hashes"),
        current_build.get("task_logic_fingerprint") or current_build.get("task_pack_hashes"),
    )

    prior_packs = prior.get("task_pack_hashes") or {}
    curr_packs = current_build.get("task_pack_hashes") or {}
    affected_packs: List[str] = []
    for pack_id in sorted(set(prior_packs) | set(curr_packs)):
        if prior_packs.get(pack_id) != curr_packs.get(pack_id):
            affected_packs.append(pack_id)
            note(f"task_pack:{pack_id}", prior_packs.get(pack_id), curr_packs.get(pack_id))

    material = [c for c in classes if c != MaterialityClass.NON_MATERIAL.value]
    if not changes:
        overall = MaterialityClass.NON_MATERIAL.value
    elif not material:
        overall = MaterialityClass.NON_MATERIAL.value
    elif len(material) == 1:
        overall = material[0]
    elif MaterialityClass.UNKNOWN.value in material and len(material) == 1:
        overall = MaterialityClass.UNKNOWN.value
    else:
        # Prefer most severe known class for reporting
        priority = [
            MaterialityClass.MATERIAL_DEVICE_BEHAVIOR.value,
            MaterialityClass.MATERIAL_EVIDENCE_PIPELINE.value,
            MaterialityClass.MATERIAL_TASK_LOGIC.value,
            MaterialityClass.MATERIAL_ACCESSIBILITY.value,
            MaterialityClass.MATERIAL_UI.value,
            MaterialityClass.UNKNOWN.value,
        ]
        overall = next((p for p in priority if p in material), MaterialityClass.UNKNOWN.value)

    is_material = overall != MaterialityClass.NON_MATERIAL.value
    recommendation = (
        "No material drift; evidence may remain under its original eligibility class "
        "(still subject to FINAL_GATING rules)."
        if not is_material
        else (
            "Material drift detected. Final evidence cannot be reused automatically. "
            "Invalidate FINAL_GATING_ACCEPTED/ELIGIBLE submissions and run targeted revalidation "
            f"for packs: {', '.join(affected_packs) or 'all_changed'}."
        )
    )

    return {
        "overall_class": overall,
        "is_material": is_material,
        "changes": changes,
        "affected_packs": affected_packs,
        "recommendation": recommendation,
        "invalidate_eligibility_to": (
            ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value if is_material else None
        ),
        "CX4_VALIDATION_MATERIALITY_ENGINE_PASS": True,
    }


def apply_material_invalidation(session: Dict[str, Any], compare_result: Dict[str, Any]) -> Dict[str, Any]:
    """Mark session invalidated when material drift affects it. Never auto-promotes."""
    session = dict(session)
    if compare_result.get("is_material"):
        session["evidence_eligibility"] = ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value
        session["material_drift"] = {
            "overall_class": compare_result.get("overall_class"),
            "affected_packs": compare_result.get("affected_packs"),
            "recommendation": compare_result.get("recommendation"),
        }
    return session
