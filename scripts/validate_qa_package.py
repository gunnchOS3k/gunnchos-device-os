#!/usr/bin/env python3
"""Validate QA package covers personas and device classes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PLANS = [
    "qa/QA_MASTER_TEST_PLAN.md",
    "qa/USER_ACCEPTANCE_TEST_PLAN.md",
    "qa/ACCESSIBILITY_TEST_PLAN.md",
    "qa/OFFLINE_MODE_TEST_PLAN.md",
    "qa/SCHOOL_LIBRARY_TEST_PLAN.md",
    "qa/GUARDIAN_CONTROLS_TEST_PLAN.md",
    "qa/REGRESSION_TEST_PLAN.md",
    "qa/TEST_REPORT_TEMPLATE.md",
]

PERSONA_MARKERS = ["pre-k", "pre_k", "high school", "researcher", "accessibility"]
DEVICE_MARKERS = ["student 14.5", "handheld", "ds-xl", "wearable"]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_PLANS:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing: {rel}")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        if "purpose" not in text:
            errors.append(f"{rel} missing purpose section")
        if "pass/fail" not in text and "pass criteria" not in text:
            errors.append(f"{rel} missing pass/fail criteria")

    master = ROOT / "qa/QA_MASTER_TEST_PLAN.md"
    if master.exists():
        text = master.read_text(encoding="utf-8", errors="ignore").lower()
        if not any(m in text for m in PERSONA_MARKERS):
            errors.append("QA_MASTER_TEST_PLAN missing persona coverage")
        if not any(m in text for m in DEVICE_MARKERS):
            errors.append("QA_MASTER_TEST_PLAN missing device class coverage")

    if errors:
        print("VALIDATE_QA_PACKAGE FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_qa_package: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
