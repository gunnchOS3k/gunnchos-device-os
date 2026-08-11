"""Cross-device continuity transfer for ECO-001 / ECO-004 / ECO-009.

Honest digital continuity over Lab work trees + checksum identity — not cloud sync
and not physical device replacement.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


CLAIM = (
    "Lab digital continuity over work-tree export/import + content checksum. "
    "SILICON_EXACT_EMULATION=false. Not production cloud sync or physical handoff."
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def export_bundle(
    *,
    source_work: Path,
    bundle_dir: Path,
    identity: dict[str, Any],
    project_rel: str = "continuity/project.json",
) -> dict[str, Any]:
    """Export approved user/project state from a Lab session work tree."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    src = source_work / project_rel
    if not src.exists():
        return {"ok": False, "error": "project_missing", "path": str(src), "claim_boundary": CLAIM}
    payload = src.read_bytes()
    dest = bundle_dir / "project.json"
    dest.write_bytes(payload)
    meta = {
        "identity": identity,
        "content_sha256": _sha256_bytes(payload),
        "exported_at": time.time(),
        "source_path": str(src),
        "project_rel": project_rel,
    }
    (bundle_dir / "manifest.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return {"ok": True, "bundle_dir": str(bundle_dir), "manifest": meta, "claim_boundary": CLAIM}


def import_bundle(
    *,
    bundle_dir: Path,
    dest_work: Path,
    expected_identity: dict[str, Any] | None = None,
    project_rel: str = "continuity/project.json",
) -> dict[str, Any]:
    """Import continuity bundle onto another Lab session; verify identity + checksum."""
    man_path = bundle_dir / "manifest.json"
    proj = bundle_dir / "project.json"
    if not man_path.exists() or not proj.exists():
        return {"ok": False, "error": "bundle_incomplete", "claim_boundary": CLAIM}
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    identity = manifest.get("identity") or {}
    if expected_identity:
        for k, v in expected_identity.items():
            if identity.get(k) != v:
                return {
                    "ok": False,
                    "error": "identity_mismatch",
                    "expected": expected_identity,
                    "actual": identity,
                    "claim_boundary": CLAIM,
                }
    digest = _sha256_file(proj)
    if digest != manifest.get("content_sha256"):
        return {
            "ok": False,
            "error": "checksum_mismatch",
            "expected": manifest.get("content_sha256"),
            "actual": digest,
            "claim_boundary": CLAIM,
        }
    dest = dest_work / project_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(proj, dest)
    opened = json.loads(dest.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "dest": str(dest),
        "identity": identity,
        "content_sha256": digest,
        "opened": opened,
        "claim_boundary": CLAIM,
    }


def seed_student_project(work: Path, *, title: str = "ECO-001 lesson") -> dict[str, Any]:
    """Begin a lesson/document/project on Student Lab work tree."""
    rel = "continuity/project.json"
    path = work / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "title": title,
        "body": "Student lesson draft for DS-XL continuity transfer.",
        "version": 1,
        "created_at": time.time(),
        "app": "lab-notes",
    }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "path": str(path),
        "rel": rel,
        "content_sha256": _sha256_file(path),
        "doc": doc,
    }


def destroy_instance_state(work: Path) -> dict[str, Any]:
    """ECO-009: destroy/reset virtual instance user state (Lab work subtree only)."""
    target = work / "continuity"
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {"ok": True, "destroyed": existed, "path": str(target)}
