#!/usr/bin/env python3
"""Validate shippable OS requirements package exists."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "requirements/README.md",
    "requirements/SHIPPABLE_OS_REQUIREMENTS.md",
    "requirements/CLAIM_BOUNDARY.md",
    "requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md",
    "requirements/SECURITY_PRIVACY_REQUIREMENTS.md",
    "requirements/ACCESSIBILITY_REQUIREMENTS.md",
    "release_gates/RELEASE_GATE_MATRIX.md",
    "release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md",
    "qa/QA_MASTER_TEST_PLAN.md",
    "roadmap/SHIPPABLE_OS_ROADMAP.md",
    "roadmap/RELEASE_CANDIDATE_BACKLOG.md",
]

FORBIDDEN_CLAIMS = [
    "finished shipping os image is complete",
    "accessibility certified and validated on hardware",
    "secure boot complete on all devices",
    "production mdm deployed",
]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"Missing: {rel}")

    for doc in (ROOT / "requirements").rglob("*.md") if (ROOT / "requirements").exists() else []:
        text = doc.read_text(encoding="utf-8", errors="ignore").lower()
        for claim in FORBIDDEN_CLAIMS:
            if claim in text and "does not claim" not in text and "not claim" not in text:
                errors.append(f"{doc.name} may falsely claim: {claim}")

    if errors:
        print("VALIDATE_SHIPPABLE_REQUIREMENTS FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_shippable_requirements: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
