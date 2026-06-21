#!/usr/bin/env python3
"""Validate firmware compatibility harness artifacts and rules."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firmware_compat.compatibility.firmware_compatibility_engine import evaluate_firmware_compatibility
from firmware_compat.probes.firmware_probe import run_probes

REQUIRED_PATHS = [
    "firmware_compat/README.md",
    "firmware_compat/CLAIM_BOUNDARY.md",
    "firmware_compat/host_probe_schema.json",
    "firmware_compat/probes/firmware_probe.py",
    "firmware_compat/compatibility/firmware_compatibility_engine.py",
    "firmware_compat/imported_hardware_contracts/manifests/student_14_5_firmware_manifest.yaml",
    "cross_repo_firmware_bridge/sync_firmware_contracts.py",
]

DEMO_OUTPUTS = [
    "results/firmware_probe_demo_output.json",
    "results/firmware_compatibility_demo_output.json",
    "results/capsule_update_client_demo_output.json",
]

FORBIDDEN_SUCCESS_CLAIMS = [
    "physical gunnchos hardware boot proven",
    "hlk certification complete",
    "real firmware flashed successfully",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            errors.append(f"Missing required path: {rel}")

    for rel in DEMO_OUTPUTS:
        if not (ROOT / rel).exists():
            errors.append(f"Missing demo output: {rel}")

    # Wearables developer blocked
    probe = run_probes(
        "wearables_arena_set",
        fixture_path=ROOT / "firmware_compat/fixtures/sample_host_probe_wearables_arena_set.json",
    )
    r = evaluate_firmware_compatibility("wearables_arena_set", probe, mode="Developer")
    if r["compatible"]:
        errors.append("Wearables must reject Developer mode in firmware compatibility engine")

    # Research consent required
    probe2 = run_probes(
        "student_14_5",
        fixture_path=ROOT / "firmware_compat/fixtures/sample_host_probe_student_14_5.json",
    )
    r2 = evaluate_firmware_compatibility("student_14_5", probe2, mode="Research Measurement", consent=False)
    if r2["compatible"]:
        errors.append("Research measurement must require consent")

    # Probe CLI smoke
    import subprocess
    out = ROOT / "results/_validate_firmware_probe_smoke.json"
    cmd = [
        sys.executable,
        str(ROOT / "firmware_compat/probes/firmware_probe.py"),
        "--device",
        "student_14_5",
        "--output",
        str(out),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)})
    if proc.returncode != 0:
        errors.append(f"firmware_probe CLI failed: {proc.stderr}")

    imported = ROOT / "firmware_compat/imported_hardware_contracts"
    if not any(imported.rglob("*.yaml")):
        errors.append("No imported hardware contracts available")

    if errors:
        print("VALIDATE_FIRMWARE_COMPAT FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_firmware_compat: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
