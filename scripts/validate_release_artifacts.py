#!/usr/bin/env python3
"""Validate release artifact docs do not fake installers/images."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md",
    "release_artifacts/BUILD_ARTIFACTS_STATUS.md",
    "release_artifacts/INSTALLER_STATUS.md",
    "release_artifacts/IMAGE_STATUS.md",
    "release_artifacts/SBOM_REQUIREMENTS.md",
    "release_artifacts/SIGNING_REQUIREMENTS.md",
]

FAKE_PATTERNS = [
    "installer is available for download",
    "installable image has been validated on hardware",
    "sbom has been signed and published",
]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing: {rel}")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        for pat in FAKE_PATTERNS:
            if pat in text and "not yet" not in text and "placeholder" not in text:
                errors.append(f"{rel} may falsely claim: {pat}")

    manifest = ROOT / "release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md"
    if manifest.exists():
        text = manifest.read_text(encoding="utf-8")
        if "Current alpha artifacts" not in text and "current alpha" not in text.lower():
            errors.append("ARTIFACT_MANIFEST must separate current alpha vs RC-required artifacts")

    if errors:
        print("VALIDATE_RELEASE_ARTIFACTS FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_release_artifacts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
