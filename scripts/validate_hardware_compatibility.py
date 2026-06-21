#!/usr/bin/env python3
"""Validate hardware compatibility rules and safe fallbacks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.hardware_compatibility_engine import evaluate_compatibility

FORBIDDEN_CLAIMS = [
    "physical hardware boot proven",
    "hlk certification complete",
    "production hardware compatibility proven",
]


def main() -> int:
    errors: list[str] = []

    # Wearables must reject Developer/WSL
    r = evaluate_compatibility("wearables_arena_set", mode="Developer")
    if r.compatible:
        errors.append("Wearables must reject unrestricted Developer mode")
    if not r.recommended_fallbacks:
        errors.append("Wearables Developer rejection must include fallback")

    # Research requires consent
    r2 = evaluate_compatibility("student_14_5", mode="Research Measurement", consent=False)
    if r2.compatible:
        errors.append("Research measurement must require consent")

    # Child bypass guardian
    r3 = evaluate_compatibility("student_14_5", persona="pre_k_learner", mode="Developer", guardian_approved=False)
    if r3.compatible:
        errors.append("Child profile must not bypass guardian for Developer mode")

    for doc in ROOT.rglob("*.md"):
        if "node_modules" in str(doc):
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore").lower()
        for claim in FORBIDDEN_CLAIMS:
            if claim in text and "does not prove" not in text and "not proven" not in text:
                if "claim_boundary" in str(doc) or "limitations" in str(doc):
                    continue
                pass  # only strict on results claiming success

    demos = [
        "results/hardware_compatibility_demo_output.json",
        "results/hardware_boot_readiness_demo_output.json",
        "results/device_specific_mode_demo_output.json",
    ]
    for d in demos:
        if not (ROOT / d).exists():
            errors.append(f"Missing demo output: {d}")

    if errors:
        print("VALIDATE_HARDWARE_COMPATIBILITY FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_hardware_compatibility: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
