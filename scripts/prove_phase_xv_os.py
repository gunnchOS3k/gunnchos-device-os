#!/usr/bin/env python3
"""Prove Phase XV OS final digital closure — residual gates.

PHYSICAL_EXECUTION_FREEZE=ACTIVE. Never claims GUNNCHOS_FRONTIER_OS_PARITY=true.
auto_merge_request remains null. Zero INCOMPLETE_DIGITAL at exit.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "phase_xv"
sys.path.insert(0, str(ROOT))

DIGITALLY_VALIDATED = "DIGITALLY_VALIDATED"
INCOMPLETE_DIGITAL = "INCOMPLETE_DIGITAL"
PHYSICAL_PENDING = "PHYSICAL_PENDING"
EXTERNAL_PENDING = "EXTERNAL_PENDING"

ACCEPTED_MAIN = "2c4fd5de439b3fcf49893eacfac38b8ec62b463e"


def run_pytest(nodeid: str) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", nodeid],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT}:src"},
    )
    return {
        "nodeid": nodeid,
        "rc": r.returncode,
        "out": (r.stdout or "")[-2000:],
        "err": (r.stderr or "")[-2000:],
    }


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    gates: dict[str, str] = {}
    tokens: dict[str, bool] = {}
    details: dict[str, object] = {}

    from gunnchos_device_os.phase_xv.accessibility import AccessibilitySubsystem
    from gunnchos_device_os.phase_xv.audio_media import AlsaPipewireStack
    from gunnchos_device_os.phase_xv.connectivity_5ga import Connectivity5GA
    from gunnchos_device_os.phase_xv.driver_hal import DriverHal
    from gunnchos_device_os.phase_xv.files_storage import FilesStorage
    from gunnchos_device_os.phase_xv.identity import UnifiedIdentityPlane
    from gunnchos_device_os.phase_xv.ntn_migration import NtnMigrationHarness
    from gunnchos_device_os.phase_xv.performance_power import PerformancePowerPolicy
    from gunnchos_device_os.phase_xv.support_lifecycle import SupportLifecycle
    from gunnchos_device_os.phase_xv.user_experience import UserExperience

    # Expected exit states (doctrine)
    expected = {
        "driver-hal": DIGITALLY_VALIDATED,
        "audio-media": DIGITALLY_VALIDATED,
        "identity": DIGITALLY_VALIDATED,
        "files-storage": DIGITALLY_VALIDATED,
        "accessibility": DIGITALLY_VALIDATED,
        "connectivity-5ga": DIGITALLY_VALIDATED,
        "ntn-migration": DIGITALLY_VALIDATED,
        "performance-power": PHYSICAL_PENDING,
        "support-lifecycle": DIGITALLY_VALIDATED,
        "user-experience": EXTERNAL_PENDING,
    }

    results = {
        "driver-hal": DriverHal(ART / "prove_hal").e2e(),
        "audio-media": AlsaPipewireStack(ART / "prove_audio").e2e(),
        "identity": UnifiedIdentityPlane(ART / "prove_identity").e2e(),
        "files-storage": FilesStorage(ART / "prove_storage").e2e(ART),
        "accessibility": AccessibilitySubsystem(ART / "prove_a11y").e2e(),
        "connectivity-5ga": Connectivity5GA(ART / "prove_5ga").e2e(),
        "ntn-migration": NtnMigrationHarness(ART / "prove_ntn").e2e(),
        "performance-power": PerformancePowerPolicy(ART / "prove_perf").e2e(),
        "support-lifecycle": SupportLifecycle(ART / "prove_support").e2e(),
        "user-experience": UserExperience(ART / "prove_ux").e2e(),
    }

    token_map = {
        "driver-hal": "DRIVER_HAL_DIGITAL_PASS",
        "audio-media": "AUDIO_MEDIA_DIGITAL_PASS",
        "identity": "IDENTITY_DIGITAL_PASS",
        "files-storage": "FILES_STORAGE_DIGITAL_PASS",
        "accessibility": "ACCESSIBILITY_DIGITAL_PASS",
        "connectivity-5ga": "CONNECTIVITY_5GA_DIGITAL_PASS",
        "ntn-migration": "NTN_MIGRATION_DIGITAL_PASS",
        "performance-power": "PERFORMANCE_POWER_DIGITAL_POLICY_PASS",
        "support-lifecycle": "SUPPORT_LIFECYCLE_DIGITAL_PASS",
        "user-experience": "USER_EXPERIENCE_DIGITAL_POLISH_PASS",
    }

    for gate, result in results.items():
        digital_ok = bool(result.get("ok"))
        want = expected[gate]
        if not digital_ok:
            gates[gate] = INCOMPLETE_DIGITAL
            tokens[token_map[gate]] = False
        else:
            gates[gate] = want
            tokens[token_map[gate]] = True
        details[gate] = {
            "ok": digital_ok,
            "module_exit_state": result.get("exit_state"),
            "assigned_exit_state": gates[gate],
        }

    pytest_jobs = {
        "driver-hal": "tests/phase_xv/test_phase_xv.py::test_driver_hal",
        "audio-media": "tests/phase_xv/test_phase_xv.py::test_audio_media",
        "identity": "tests/phase_xv/test_phase_xv.py::test_identity",
        "files-storage": "tests/phase_xv/test_phase_xv.py::test_files_storage",
        "accessibility": "tests/phase_xv/test_phase_xv.py::test_accessibility",
        "connectivity-5ga": "tests/phase_xv/test_phase_xv.py::test_connectivity_5ga",
        "ntn-migration": "tests/phase_xv/test_phase_xv.py::test_ntn_migration",
        "performance-power": "tests/phase_xv/test_phase_xv.py::test_performance_power",
        "support-lifecycle": "tests/phase_xv/test_phase_xv.py::test_support_lifecycle",
        "user-experience": "tests/phase_xv/test_phase_xv.py::test_user_experience",
        "security-regression": "tests/phase_xv/test_phase_xv.py::test_security_regression",
        "a11y-regression": "tests/phase_xv/test_phase_xv.py::test_accessibility_regression",
    }
    pytest_results = {}
    for gate, node in pytest_jobs.items():
        pr = run_pytest(node)
        pytest_results[gate] = {"rc": pr["rc"]}
        if pr["rc"] != 0:
            if gate in ("security-regression", "a11y-regression"):
                # Security/a11y regressions demote related digital gates
                for g in ("identity", "accessibility", "files-storage"):
                    gates[g] = INCOMPLETE_DIGITAL
                    tokens[token_map[g]] = False
            elif gate in gates:
                gates[gate] = INCOMPLETE_DIGITAL
                tokens[token_map[gate]] = False

    report = {
        "schema": "gunnchos.phase_xv.os_prove_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accepted_main_base": ACCEPTED_MAIN,
        "physical_execution_freeze": True,
        "auto_merge_request": None,
        "frontier_os_parity_claimed": False,
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "gates": gates,
        "tokens": tokens,
        "digitally_validated_gates": sorted(g for g, s in gates.items() if s == DIGITALLY_VALIDATED),
        "incomplete_gates": sorted(g for g, s in gates.items() if s == INCOMPLETE_DIGITAL),
        "physical_pending_gates": sorted(g for g, s in gates.items() if s == PHYSICAL_PENDING),
        "external_pending_gates": sorted(g for g, s in gates.items() if s == EXTERNAL_PENDING),
        "pytest": pytest_results,
        "details": details,
        "handheld_storage_note": {
            "field_kit_npi": "NPI_DEFECT-HANDHELD-STORAGE-HEADROOM-001",
            "local_artifact": "artifacts/phase_xv/HANDHELD_32G_HEADROOM.json",
            "local_npi": "artifacts/phase_xv/NPI_DEFECT-STORAGE-HANDHELD-32G.json",
            "wp002_decision_outcome": "A",
            "status": "CLOSED_OUTCOME_A_PENDING_V1",
            "v1_certification": "NOT_SELF_CERTIFIED",
        },
        "artifacts": {
            "os_prove_report": "artifacts/phase_xv/OS_PROVE_REPORT.json",
        },
    }

    def _scrub(obj):
        if isinstance(obj, dict):
            return {k: _scrub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_scrub(x) for x in obj]
        if isinstance(obj, str) and ("/Users/" in obj or obj.startswith("/home/")):
            return "artifacts/phase_xv/(scrubbed)"
        return obj

    report = _scrub(report)
    out = ART / "OS_PROVE_REPORT.json"
    text = json.dumps(report, indent=2) + "\n"
    if "/Users/" in text:
        raise SystemExit("host path leaked into prove report")
    out.write_text(text, encoding="utf-8")
    summary = {
        "ok": not report["incomplete_gates"],
        "report": str(out.relative_to(ROOT)),
        "digitally_validated_gates": report["digitally_validated_gates"],
        "incomplete_gates": report["incomplete_gates"],
        "physical_pending_gates": report["physical_pending_gates"],
        "external_pending_gates": report["external_pending_gates"],
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "auto_merge_request": None,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
