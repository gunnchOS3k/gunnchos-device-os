#!/usr/bin/env python3
"""Gate 6 dry-run for gunnchos-device-os.

Emulated OS validation packet only. Explicitly does NOT claim physical boot
evidence (OS_PHYSICAL_BOOT_PENDING).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHYS = ROOT / "physical_evidence"
OSV = PHYS / "os_validation"
REPORT = PHYS / "GATE6_DRY_RUN_REPORT.json"
FIXTURE = PHYS / "fixtures" / "synthetic_os_validation_dry_run.json"

REQUIRED = [
    "os_validation/BOOT_EVIDENCE_TEMPLATE.json",
    "os_validation/DRIVER_INVENTORY_TEMPLATE.json",
    "os_validation/SUSPEND_RESUME_CHECKLIST.md",
    "os_validation/UPDATE_ROLLBACK_CHECKLIST.md",
    "os_validation/OFFLINE_MODE_CHECKLIST.md",
    "os_validation/ACCESSIBILITY_CHECKLIST.md",
    "os_validation/GAME_APP_COMPATIBILITY_TEMPLATE.json",
    "fixtures/synthetic_os_validation_dry_run.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    return data


def check_files() -> dict:
    missing = [name for name in REQUIRED if not (PHYS / name).is_file()]
    return {"ok": not missing, "missing": missing, "required": REQUIRED}


def check_fixture() -> dict:
    errors: list[str] = []
    data = load_json(FIXTURE)
    for key in (
        "evidence_id",
        "evidence_label",
        "domain",
        "status",
        "emulated",
        "physical_boot",
        "claim_boundary",
        "notes",
    ):
        if key not in data:
            errors.append(f"missing field: {key}")
    if data.get("evidence_label") != "SYNTHETIC_EXPERIMENT":
        errors.append("evidence_label must be SYNTHETIC_EXPERIMENT")
    if data.get("emulated") is not True:
        errors.append("fixture must set emulated=true")
    if data.get("physical_boot") is not False:
        errors.append("fixture must set physical_boot=false")
    if data.get("claim_boundary") != "OS_PHYSICAL_BOOT_PENDING":
        errors.append("claim_boundary must be OS_PHYSICAL_BOOT_PENDING")
    note = str(data.get("notes", "")).upper()
    if "NOT PHYSICAL" not in note and "OS_PHYSICAL_BOOT_PENDING" not in note:
        errors.append("notes must state emulated profiles are not physical boot evidence")

    boot = load_json(OSV / "BOOT_EVIDENCE_TEMPLATE.json")
    if boot.get("claim_boundary") != "OS_PHYSICAL_BOOT_PENDING":
        errors.append("boot template claim_boundary must be OS_PHYSICAL_BOOT_PENDING")
    if boot.get("physical_boot") is not False:
        errors.append("boot template physical_boot must be false by default")

    return {"ok": not errors, "errors": errors, "path": str(FIXTURE)}


def main() -> int:
    PHYS.mkdir(parents=True, exist_ok=True)
    (PHYS / "fixtures").mkdir(parents=True, exist_ok=True)
    OSV.mkdir(parents=True, exist_ok=True)

    files = check_files()
    fixture = check_fixture() if files["ok"] else {"ok": False, "errors": ["required files missing"]}
    harness_ok = files["ok"] and fixture["ok"]

    report = {
        "gate": "6",
        "repository": "gunnchos-device-os",
        "mode": "dry_run",
        "started": utc_now(),
        "files": files,
        "fixture": fixture,
        "statuses": {
            "GATE6_HARNESS": "GATE6_HARNESS_PASS" if harness_ok else "GATE6_HARNESS_FAIL",
            "OS_PHYSICAL_BOOT": "OS_PHYSICAL_BOOT_PENDING",
            "PHYSICAL_EVIDENCE": "PHYSICAL_EVIDENCE_PENDING",
        },
        "claim": (
            "GATE6_HARNESS_PASS only — emulated profiles are NOT physical boot evidence "
            "(OS_PHYSICAL_BOOT_PENDING)"
        ),
        "finished": utc_now(),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": harness_ok, "report": str(REPORT), "statuses": report["statuses"]}, indent=2))
    return 0 if harness_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
