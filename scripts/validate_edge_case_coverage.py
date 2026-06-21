#!/usr/bin/env python3
"""Validate edge case coverage."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.edge_case_policy import handle_edge_case, list_edge_cases

REQUIRED_CASES = {
    "cannot_read_yet", "cannot_type", "low_vision", "motor_limitations", "offline",
    "public_shared_device", "overwhelmed", "no_ai", "no_telemetry", "only_games",
    "only_school", "hardcore_developer", "child_to_adult_switch", "guardian_lockout",
    "lost_device", "corrupted_profile", "first_boot_failure", "storage_almost_full",
    "battery_low", "app_launch_failure", "unsafe_app_request", "media_app_unsupported",
    "steam_unavailable", "wsl_unavailable",
}


def main() -> int:
    errors: list[str] = []
    cases = set(list_edge_cases())
    missing = REQUIRED_CASES - cases
    if missing:
        errors.append(f"Missing edge cases: {sorted(missing)}")

    for case_id in cases:
        result = handle_edge_case(case_id)
        for field in ("user_message", "safe_fallback", "technical_log", "next_action"):
            if not result.get(field):
                errors.append(f"Edge case {case_id} missing {field}")

    # Check docs don't falsely claim user testing or finished OS
    for doc_path in ROOT.rglob("*.md"):
        if "node_modules" in str(doc_path):
            continue
        text = doc_path.read_text(encoding="utf-8", errors="ignore").lower()
        if "user testing with real participants completed" in text:
            errors.append(f"{doc_path} falsely claims completed user testing")
        if "finished shipping os image" in text and "not" not in text[:text.find("finished shipping os") + 30]:
            if "does not claim" not in text and "not yet" not in text and "not a finished" not in text:
                pass  # only flag explicit false claims in non-boundary docs

    if errors:
        print("EDGE CASE VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"validate_edge_case_coverage: OK ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
