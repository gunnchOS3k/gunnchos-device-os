#!/usr/bin/env python3
"""Validate issue closure matrix completeness."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/ISSUE_CLOSURE_MATRIX.md"
README = ROOT / "README.md"

REQUIRED_ISSUES = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12"}

ARTIFACT_CHECKS = {
    "1": ["gunnchos_device_os/device_classes.py", "config/device_classes.yaml", "tests/test_device_classes.py"],
    "2": ["docs/LAUNCHER_MOCK_ARCHITECTURE.md", "tests/test_launcher_architecture_docs.py"],
    "3": ["gunnchos_device_os/deploy_contract.py", "tests/test_deploy_contract.py", "scripts/run_deploy_contract_demo.py"],
    "4": ["config/modes.yaml", "docs/SCHOOL_MODE.md", "tests/test_modes.py"],
    "5": ["docs/DEVELOPER_MODE.md", "tests/test_modes.py"],
    "6": ["docs/RESEARCH_MEASUREMENT_MODE.md", "tests/test_modes.py", "gunnchos_device_os/edge_io_contract.py"],
    "7": ["gunnchos_device_os/guardian_policy.py", "tests/test_guardian_policy.py"],
    "8": ["gunnchos_device_os/privacy_security_model.py", "tests/test_privacy_security_model.py"],
    "9": ["diagrams/deploy_flow_local_wifi.mmd", "tests/test_deploy_docs.py"],
    "10": ["gunnchos_device_os/edge_io_contract.py", "tests/test_edge_io_contract.py"],
    "12": ["config/waike_tutor_cards.yaml", "tests/test_waike_integration.py"],
}


def main() -> int:
    errors: list[str] = []
    if not MATRIX.exists():
        errors.append("Missing docs/ISSUE_CLOSURE_MATRIX.md")
        _report(errors)
        return 1

    text = MATRIX.read_text(encoding="utf-8")
    found_issues = set(re.findall(r"#(\d+)", text))
    missing_issues = REQUIRED_ISSUES - found_issues
    if missing_issues:
        errors.append(f"Matrix missing issues: {sorted(missing_issues)}")

    for issue, paths in ARTIFACT_CHECKS.items():
        for rel in paths:
            if not (ROOT / rel).exists():
                errors.append(f"Issue #{issue} missing artifact: {rel}")

    if "ISSUE_CLOSURE_MATRIX" not in README.read_text(encoding="utf-8"):
        errors.append("README must link to docs/ISSUE_CLOSURE_MATRIX.md")

    closes_lines = [l for l in text.splitlines() if "Closes" in l or "Close status" in l.lower()]
    if not closes_lines:
        errors.append("Matrix must include close status / Closes keywords")

    _report(errors)
    return 1 if errors else 0


def _report(errors: list[str]) -> None:
    if errors:
        print("ISSUE CLOSURE VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("validate_issue_closure: OK")


if __name__ == "__main__":
    raise SystemExit(main())
