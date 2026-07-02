#!/usr/bin/env python3
"""Validate beta_gate/beta_gate_status.yaml structure and honesty rules."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "beta_gate" / "beta_gate_status.yaml"
REQUIRED_FIELDS = ("status", "evidence_paths", "tests", "blocker", "owner_area", "target_stage")
ALLOWED_STATUS = {"missing", "prototype", "implemented", "validated"}


def main() -> int:
    if yaml is None:
        print("PyYAML required: pip install pyyaml")
        return 1
    if not STATUS_FILE.exists():
        print(f"Missing {STATUS_FILE}")
        return 1

    data = yaml.safe_load(STATUS_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []

    if "items" not in data or not isinstance(data["items"], dict):
        errors.append("Missing items map")
        return report(errors)

    for item_id, item in data["items"].items():
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"{item_id}: missing field {field}")
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{item_id}: invalid status {status!r}")
        if status == "validated" and not item.get("evidence_paths"):
            errors.append(f"{item_id}: validated status requires evidence_paths")
        if status in ("implemented", "validated") and not item.get("tests"):
            errors.append(f"{item_id}: {status} status should list tests")

    if data.get("beta_ready"):
        p0 = data.get("p0_items", [])
        for pid in p0:
            item = data["items"].get(pid)
            if not item:
                errors.append(f"p0 item missing from items: {pid}")
                continue
            if item["status"] in ("missing", "prototype"):
                errors.append(f"beta_ready true but P0 {pid} is {item['status']}")

    return report(errors)


def report(errors: list[str]) -> int:
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print("beta_gate_status.yaml is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
