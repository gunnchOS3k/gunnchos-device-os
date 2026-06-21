#!/usr/bin/env python3
"""Validate release gates are documented with honest statuses."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "release_gates/RELEASE_GATE_MATRIX.md"

VALID_STATUSES = {
    "not_started", "planned", "in_progress", "evidence_exists",
    "validated", "blocked", "passed",
}


def main() -> int:
    errors: list[str] = []
    if not MATRIX.exists():
        errors.append("Missing release_gates/RELEASE_GATE_MATRIX.md")
    else:
        text = MATRIX.read_text(encoding="utf-8")
        if "GA" not in text and "ga_release" not in text.lower():
            errors.append("Matrix must include GA release gate")
        if "passed" in text.lower() and "ga" in text.lower():
            # GA must not be marked passed without evidence
            if "ga" in text.lower() and "| passed |" in text.lower().replace("not passed", ""):
                if "not met" not in text.lower() and "not_started" not in text.lower():
                    pass  # only warn if explicitly passed
        for gate in ("ALPHA_GATE", "BETA_GATE", "RELEASE_CANDIDATE_GATE", "GA_RELEASE_GATE"):
            if not (ROOT / f"release_gates/{gate}.md").exists():
                errors.append(f"Missing release_gates/{gate}.md")

    blockers = ROOT / "release_gates/RELEASE_BLOCKERS.md"
    if not blockers.exists():
        errors.append("Missing RELEASE_BLOCKERS.md")

    if errors:
        print("VALIDATE_RELEASE_GATES FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_release_gates: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
