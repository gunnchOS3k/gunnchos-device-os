"""Run manifest reproducibility for Device Lab."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any


def _git_sha(repo: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), stderr=subprocess.DEVNULL, text=True
        )
        return out.strip()
    except Exception:
        return None


def _hash_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_manifest(
    *,
    profile: dict[str, Any],
    scenario: str | None,
    fidelity: dict[str, Any],
    virtualization: dict[str, Any],
    virtual_devices: dict[str, Any],
    applications: list[str],
    result: dict[str, Any],
    evidence_dir: Path,
    repo_root: Path,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    run_id = f"lab-{uuid.uuid4().hex[:12]}"
    image_candidates = [
        repo_root / "artifacts" / "bootable_reference" / "IMAGE_HASH.txt",
        repo_root / "os_build" / "bootable_reference" / "IMAGE_HASH.txt",
    ]
    image_hash = None
    for c in image_candidates:
        if c.exists():
            image_hash = c.read_text(encoding="utf-8").strip()[:128]
            break

    manifest = {
        "schema": "gunnchos.device_lab.run_manifest.v1",
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {
            "os": platform.platform(),
            "cpu": platform.processor() or platform.machine(),
            "python": platform.python_version(),
        },
        "hypervisor": (virtualization.get("selected") or {}).get("name"),
        "device_profile": profile.get("profile_id"),
        "profile_version": profile.get("profile_version"),
        "accepted_repo_SHAs": {
            "device_os": _git_sha(repo_root),
            "profile_baseline_note": profile.get("accepted_source_revisions"),
        },
        "OS_image_hash": image_hash,
        "scenario": scenario,
        "applications": applications,
        "virtual_devices": virtual_devices,
        "resource_constraints": profile.get("performance_model"),
        "fidelity_levels": fidelity,
        "measurement_types": {
            "HOST_OBSERVED": "allowed",
            "VIRTUAL_CONSTRAINED": "allowed_when_vm",
            "MODELED_TARGET_RANGE": "schema_only_pre_EVT",
            "CALIBRATED_TARGET": "unavailable_pre_EVT",
            "PHYSICAL_MEASURED": "unavailable_pre_EVT",
        },
        "evidence_dir": str(evidence_dir),
        "result": {
            "ok": bool(result.get("ok")),
            "status": "PASS" if result.get("ok") else "FAIL",
            "summary": {k: result.get(k) for k in ("ok", "scenario_id", "errors") if k in result},
        },
        "limitations": limitations or [
            "SILICON_EXACT_EMULATION=false",
            "Full QEMU guest optional; CI uses HYBRID_BEHAVIORAL",
            "VF4/VF5/VF6 PHYSICAL_PENDING",
            "Not independent verification",
        ],
        "SILICON_EXACT_EMULATION": False,
        "BEHAVIORAL_DEVICE_PROFILE": True,
        "env": {
            "GUNNCHDEVICE_LAB_BACKEND": os.environ.get("GUNNCHDEVICE_LAB_BACKEND"),
            "GUNNCHDEVICE_LAB_NETNS": os.environ.get("GUNNCHDEVICE_LAB_NETNS"),
        },
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(path)
    manifest["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest
