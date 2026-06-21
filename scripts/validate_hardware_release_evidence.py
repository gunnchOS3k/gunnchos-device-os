#!/usr/bin/env python3
"""Validate hardware release evidence docs."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md",
    "hardware_release/HARDWARE_COMPATIBILITY_STATUS.md",
    "config/hardware_release_evidence.yaml",
]

FAKE = [
    "hardware-compatible release achieved",
    "hlk certification passed",
    "all devices physically validated",
]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"Missing: {rel}")

    matrix = ROOT / "hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md"
    if matrix.exists():
        text = matrix.read_text(encoding="utf-8")
        if "simulated" not in text.lower() and "needs_real_hardware" not in text.lower():
            errors.append("Evidence matrix must show simulated/needs_real_hardware status")
        for device in ("Student 14.5", "Handheld", "DS-XL", "Wearables"):
            if device not in text and "student_14" not in text:
                pass
        if "student_14" not in text.lower() and "Student 14" not in text:
            errors.append("Matrix must reference device classes")

    for doc in [matrix, ROOT / "hardware_release/HARDWARE_COMPATIBILITY_STATUS.md"]:
        if doc.exists():
            t = doc.read_text(encoding="utf-8").lower()
            for f in FAKE:
                if f in t and "not" not in t[:t.find(f)]:
                    errors.append(f"{doc.name} may falsely claim: {f}")

    if errors:
        print("VALIDATE_HARDWARE_RELEASE_EVIDENCE FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_hardware_release_evidence: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
