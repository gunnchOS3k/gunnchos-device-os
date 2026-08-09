"""Third-party clean reproduction — container/CI, no laptop-only paths."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import re

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_REPRO_READY
from gunnchos_device_os.cont_viii.reproducibility import evaluate_reproducibility

FORBIDDEN = re.compile(r"/Users/gunnchos|/Users/[A-Za-z]+/Library|C:\\\\Users\\\\Edmund")


def evaluate_third_party_repro() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    base = evaluate_reproducibility(root)
    checks = dict(base.get("checks") or {})

    # Cont IX extensions
    paths = {
        "device_os_qemu": (root / "os_build" / "bootable_reference").exists(),
        "ring_firmware_bridge": (root / "cross_repo_firmware_bridge").exists(),
        "ai_service": (root / "gunnchos_device_os" / "gunnchai_integration.py").exists(),
        "games_packages": (root / "games").exists(),
        "archive_db_export": (root / "games" / "earth-species-web").exists(),
        "beat_link": (root / "games" / "beatlink-party-web").exists(),
        "hardware_exports_public": (root / "docs").exists(),
        "devcontainer": (root / ".devcontainer" / "devcontainer.json").exists(),
        "ci_workflow": (root / ".github" / "workflows" / "ci.yml").exists(),
    }
    checks.update({f"path_{k}": v for k, v in paths.items()})

    # Scan committed reproducibility surfaces only (not generated runtime artifacts)
    laptop_hits = []
    scan_files = [
        root / "REPRODUCIBILITY_MANIFEST.yaml",
        root / ".devcontainer" / "devcontainer.json",
        root / "sdk" / ".env.example",
        root / "config" / "productivity" / "stack.yaml",
        root / ".github" / "workflows" / "continuation-ix.yml",
    ]
    for path in scan_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in FORBIDDEN.finditer(text):
            laptop_hits.append({"path": str(path.relative_to(root)), "match": m.group(0)})

    software_repro = {
        "device_os_qemu": paths["device_os_qemu"],
        "ai_service": paths["ai_service"],
        "games": paths["games_packages"],
        "archive": paths["archive_db_export"],
        "beat_link": paths["beat_link"],
        "sdk": (root / "sdk").exists(),
    }
    restricted_vendor_hw = {
        "separated": True,
        "note": "Restricted-vendor HW exports are not required for software reproducibility token",
        "physical_validation_pending": True,
    }

    ok = (
        base.get("ok") is True
        and all(paths.values())
        and len(laptop_hits) == 0
        and all(software_repro.values())
        and not bool(os.environ.get("GUNNCHOS_HOST_ONLY_SECRET"))
    )
    report = {
        "schema": "gunnchos.reproducibility_digital_ready.v1",
        "ok": ok,
        "token": TOKEN_REPRO_READY if ok else None,
        "base_reproducibility": {"ok": base.get("ok"), "token": base.get("token")},
        "checks": checks,
        "software_repro": software_repro,
        "restricted_vendor_hw": restricted_vendor_hw,
        "laptop_hits": laptop_hits,
        "recreation_ready_conflated": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "repro_path_or_laptop_leak",
    }
    # Write report last so self-scan doesn't require it beforehand
    out = root / "artifacts" / "continuation_ix" / "reproducibility_digital_ready.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
