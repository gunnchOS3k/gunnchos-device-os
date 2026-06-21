#!/usr/bin/env python3
"""Sync firmware manifests and contracts from gunnchos-hardware-industrial-design."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HW_REPO = ROOT.parent / "gunnchos-hardware-industrial-design"
IMPORTED = ROOT / "firmware_compat" / "imported_hardware_contracts"
REPORT_PATH = ROOT / "results" / "firmware_contract_sync_report.json"

SYNC_MAP = {
    "manifests": "firmware/manifests/*.yaml",
    "interfaces": "firmware/interfaces/*.yaml",
    "boot": "firmware/boot/*.yaml",
    "capsule_update": "firmware/capsule_update/sample_capsule_manifest.yaml",
    "descriptors/acpi": "firmware/descriptors/acpi/*",
    "descriptors/devicetree": "firmware/descriptors/devicetree/*",
}


def sync_contracts(hardware_repo: Path, *, allow_fallback: bool = True) -> dict:
    errors: list[str] = []
    copied: list[str] = []
    fallback_used = False

    if not hardware_repo.exists():
        if allow_fallback and IMPORTED.exists() and any(IMPORTED.rglob("*.yaml")):
            fallback_used = True
        else:
            errors.append(
                f"Hardware repo not found at {hardware_repo}. "
                "Clone gunnchos-hardware-industrial-design or commit imported_hardware_contracts fallback."
            )
            return _report(hardware_repo, copied, errors, fallback_used)

    if hardware_repo.exists():
        for dest_key, pattern in SYNC_MAP.items():
            dest_dir = IMPORTED / dest_key
            dest_dir.mkdir(parents=True, exist_ok=True)
            if "*" in pattern:
                for src in sorted(hardware_repo.glob(pattern)):
                    if src.is_file():
                        target = dest_dir / src.name
                        shutil.copy2(src, target)
                        copied.append(str(target.relative_to(ROOT)))
            else:
                src = hardware_repo / pattern
                if src.exists():
                    target = dest_dir / src.name
                    shutil.copy2(src, target)
                    copied.append(str(target.relative_to(ROOT)))
                else:
                    errors.append(f"Missing source artifact: {src}")

    if not copied and not fallback_used:
        if allow_fallback and IMPORTED.exists() and any(IMPORTED.rglob("*.yaml")):
            fallback_used = True
        else:
            errors.append("No contracts copied and no imported fallback available")

    return _report(hardware_repo, copied, errors, fallback_used)


def _report(hw_repo: Path, copied: list[str], errors: list[str], fallback_used: bool) -> dict:
    report = {
        "sync_timestamp": datetime.now(timezone.utc).isoformat(),
        "hardware_repo_path": str(hw_repo),
        "hardware_repo_present": hw_repo.exists(),
        "fallback_used": fallback_used,
        "files_copied": copied,
        "copy_count": len(copied),
        "errors": errors,
        "status": "ok" if not errors else "error",
        "imported_root": str(IMPORTED.relative_to(ROOT)),
        "claim_boundary": "Contract sync for harness — not physical-board validation",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--hardware-repo",
        type=Path,
        default=DEFAULT_HW_REPO,
        help="Path to gunnchos-hardware-industrial-design",
    )
    ap.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail if hardware repo missing even when imported copies exist",
    )
    args = ap.parse_args()
    report = sync_contracts(args.hardware_repo, allow_fallback=not args.no_fallback)
    print(json.dumps(report, indent=2))
    if report["status"] == "error":
        print("SYNC_FIRMWARE_CONTRACTS FAILED:", file=sys.stderr)
        for err in report["errors"]:
            print(f"  - {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
