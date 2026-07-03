#!/usr/bin/env python3
"""Validate beta_gate/beta_gate_status.yaml structure and honesty rules."""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "beta_gate" / "beta_gate_status.yaml"
BETA_REPORT = ROOT / "release_artifacts" / "BETA_CANDIDATE_REPORT.md"
KNOWN_ISSUES = ROOT / "docs" / "KNOWN_ISSUES.md"
PHYSICAL_HW_MARKER = ROOT / "hardware_validation" / "REFERENCE_HARDWARE_VALIDATION_TEMPLATE.md"
BOOT_VALIDATION = ROOT / "hardware_validation" / "BOOT_VALIDATION_TEMPLATE.md"
STREAMING_TRACKER = ROOT / "streaming_certification" / "SERVICE_CERTIFICATION_TRACKER.yaml"
REQUIRED_FIELDS = ("status", "evidence_paths", "tests", "blocker", "owner_area", "target_stage")
ALLOWED_STATUS = {"missing", "prototype", "implemented", "validated"}
P0_REQUIRES_IMPLEMENTED = {"policy_enforcement", "known_issues"}

# Items that cannot be validated without specific evidence markers
VALIDATION_RULES: dict[str, dict[str, str]] = {
    "hardware_evidence": {
        "marker_file": str(PHYSICAL_HW_MARKER),
        "marker_text": "Physical validation performed: Yes",
        "error": "hardware_evidence cannot be validated without physical report",
    },
    "bootable_image": {
        "marker_file": str(BOOT_VALIDATION),
        "marker_text": "boot_validation_performed: true",
        "error": "bootable_image cannot be validated without boot evidence",
    },
    "secure_boot": {
        "marker_file": str(ROOT / "security" / "secure_boot" / "SECURE_BOOT_CHECKLIST.md"),
        "marker_text": "Boot with Secure Boot enabled on reference device",
        "error": "secure_boot cannot be validated without boot-chain evidence",
        "require_checked": True,
    },
    "production_mdm": {
        "marker_file": str(ROOT / "mdm" / "enrollment_profile.example.json"),
        "marker_text": "Remote enrollment server",
        "error": "production_mdm cannot be validated without real enrollment/server evidence",
        "forbid_if_present": True,
    },
    "streaming_certification": {
        "marker_file": str(STREAMING_TRACKER),
        "marker_text": "certification_status: certified",
        "error": "streaming_certification cannot be validated without service/CDM evidence",
    },
    "legal_privacy_accessibility": {
        "marker_file": str(ROOT / "compliance" / "accessibility" / "ACCESSIBILITY_TEST_REPORT_TEMPLATE.md"),
        "marker_text": "Certification claim:** _None",
        "error": "legal_privacy_accessibility cannot be validated without formal review evidence",
    },
}


def check_validated_honesty(item_id: str, status: str) -> str | None:
    if status != "validated":
        return None
    rule = VALIDATION_RULES.get(item_id)
    if not rule:
        return None
    marker_path = Path(rule["marker_file"])
    if not marker_path.exists():
        return f"{item_id} cannot be validated — missing evidence file {marker_path.name}"
    text = marker_path.read_text(encoding="utf-8")
    marker = rule["marker_text"]
    if rule.get("forbid_if_present") and marker in text:
        return rule["error"]
    if rule.get("require_checked"):
        # Validated requires checklist item to be checked [x]
        pattern = re.escape(marker).replace(r"\ ", r"\s+")
        if not re.search(rf"- \[x\].*{pattern}", text, re.IGNORECASE):
            return rule["error"]
        return None
    if marker not in text:
        return rule["error"]
    if item_id == "streaming_certification" and marker_path.exists():
        try:
            tracker = yaml.safe_load(marker_path.read_text(encoding="utf-8"))
            services = tracker.get("services", {}) if isinstance(tracker, dict) else {}
            for sid, svc in services.items():
                if isinstance(svc, dict) and svc.get("certification_status") == "certified":
                    if not svc.get("evidence_path"):
                        return f"streaming service {sid} certified without evidence_path"
        except Exception:
            pass
    return None


def main() -> int:
    if yaml is None:
        print("PyYAML required: pip install pyyaml")
        return 1
    if not STATUS_FILE.exists():
        print(f"Missing {STATUS_FILE}")
        return 1

    data = yaml.safe_load(STATUS_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []

    if not BETA_REPORT.exists():
        errors.append("Missing release_artifacts/BETA_CANDIDATE_REPORT.md")

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
        if status in ("implemented", "validated") and not item.get("evidence_paths"):
            errors.append(f"{item_id}: {status} status requires evidence_paths")
        if status in ("implemented", "validated") and not item.get("tests"):
            errors.append(f"{item_id}: {status} status should list tests")

        honesty_error = check_validated_honesty(item_id, status or "")
        if honesty_error:
            errors.append(honesty_error)

        # Legacy hardware template check
        if item_id == "hardware_evidence" and status == "validated":
            text = PHYSICAL_HW_MARKER.read_text(encoding="utf-8") if PHYSICAL_HW_MARKER.exists() else ""
            if "Physical validation performed: Yes" not in text:
                errors.append("hardware_evidence cannot be validated without physical report")

    if not KNOWN_ISSUES.exists():
        errors.append("Missing docs/KNOWN_ISSUES.md")

    known = data["items"].get("known_issues", {})
    if known.get("status") in ("missing", "prototype"):
        errors.append("known_issues must be implemented for beta closure track")

    policy = data["items"].get("policy_enforcement", {})
    if policy.get("status") in ("missing", "prototype"):
        errors.append("policy_enforcement must be implemented for beta closure track")

    if data.get("beta_ready"):
        p0 = data.get("p0_items", [])
        for pid in p0:
            item = data["items"].get(pid)
            if not item:
                errors.append(f"p0 item missing from items: {pid}")
                continue
            if item["status"] in ("missing", "prototype"):
                errors.append(f"beta_ready true but P0 {pid} is {item['status']}")
        media = data["items"].get("media_player", {})
        if media.get("status") == "missing":
            errors.append("beta_ready true but media_player is missing (PR #35)")

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
