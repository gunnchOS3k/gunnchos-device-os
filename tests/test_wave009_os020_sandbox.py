"""Wave009 OS-PLATFORM-020 sandbox validation tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from gunnchos_device_os.platform.sandbox_executor import SandboxExecutor
from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine
from gunnchos_device_os.wave009_os020.behavioral_negative_controls import prove_behavioral_negative_controls
from gunnchos_device_os.wave009_os020.evaluator import (
    evaluate_os_platform_020,
    run_completion_gate_negative_controls,
)
from gunnchos_device_os.wave009_os020.evaluator_integrity import inspect_wave009_evaluator


def test_plain_subprocess_never_validates(tmp_path: Path) -> None:
    suite = SandboxExecutor(tmp_path, SandboxPolicyEngine()).run_enforcement_suite("t-plain")
    assert suite["PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX"] is False
    if suite.get("SANDBOX_BACKEND") in {"subprocess_broker", "sandbox_exec_unavailable", "none"}:
        assert suite["SANDBOX_EXECUTION_VALIDATED"] is False
        assert suite["LOCAL_SANDBOX_VALIDATION"] == "BLOCKED_ENVIRONMENT"
        assert suite["KERNEL_SANDBOX"] is False


def test_behavioral_sabotage_controls_pass() -> None:
    result = prove_behavioral_negative_controls()
    assert result["BEHAVIORAL_NEGATIVE_CONTROL_COUNT"] >= 12
    assert result["BEHAVIORAL_NEGATIVE_CONTROLS_PASS"] is True
    assert result["ok"] is True


def test_completion_gate_negatives_pass() -> None:
    result = run_completion_gate_negative_controls()
    assert result["ok"] is True
    assert result["BROKEN_EVALUATOR_REJECTED"] is True
    assert result["EMPTY_EVIDENCE_REJECTED"] is True


def test_evaluator_integrity_computed() -> None:
    integrity = inspect_wave009_evaluator(evaluate_os_platform_020)
    assert integrity["UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED"] is True
    assert integrity["UNCONDITIONAL_TRUE_CLASSIFIERS"] == 0
    assert integrity["ok"] is True


def test_wave009_ci_requires_validated_when_flagged(tmp_path: Path) -> None:
    suite = SandboxExecutor(tmp_path, SandboxPolicyEngine()).run_enforcement_suite("ci-flag")
    row = evaluate_os_platform_020(suite)
    if os.environ.get("WAVE009_REQUIRE_SANDBOX_VALIDATED") == "1":
        assert suite.get("SANDBOX_BACKEND") == "bubblewrap"
        assert suite.get("SANDBOX_EXECUTED_AS_ROOT") is False
        assert suite.get("BWRAP_INVOKED_WITH_SUDO") is False
        assert suite.get("SECCOMP_LOADED") is True
        assert suite.get("PRIVATE_ROOT_RW_PASS") is True
        assert row["classification"] == "IMPLEMENTED_AND_VALIDATED"
        assert row["ok"] is True
        assert suite.get("KERNEL_SANDBOX") is True
    else:
        assert row["classification"] in {
            "IMPLEMENTED_AND_VALIDATED",
            "BLOCKED_ENVIRONMENT",
            "IMPLEMENTATION_OPEN",
        }
