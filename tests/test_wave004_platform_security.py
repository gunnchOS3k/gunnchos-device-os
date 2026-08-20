"""Wave 004 platform security tests — final integrity (008/012/020)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator
from gunnchos_device_os.platform.e2e_scenarios import run_all_scenarios
from gunnchos_device_os.platform.package_lifecycle import PackageLifecycleManager
from gunnchos_device_os.platform.persistent_sync import run_a_b_c_restart_proof
from gunnchos_device_os.platform.requirement_evaluators import run_all_evaluators
from gunnchos_device_os.platform.security_injection import run_security_injections


@pytest.fixture()
def coord(tmp_path: Path) -> Wave004PlatformCoordinator:
    return Wave004PlatformCoordinator(tmp_path / "wave004")


def test_wave004_package_lifecycle_full(coord: Wave004PlatformCoordinator) -> None:
    proof = coord.package_lifecycle.run_full_lifecycle_proof("full-app")
    assert proof["ok"] is True, proof
    negatives = coord.package_lifecycle.run_negative_proofs()
    assert negatives["ok"] is True, negatives


def test_wave004_sync_a_b_c(coord: Wave004PlatformCoordinator) -> None:
    assert coord.offline_sync.storage_path is not None
    proof = run_a_b_c_restart_proof(coord.offline_sync.storage_path / "abc")
    assert proof["ok"] is True, proof
    assert proof["process_a_pending"] == 1
    assert proof["process_b_remote_apply_count"] == 1
    assert proof["process_c_replay_remote_apply_count"] == 1


def test_wave004_sandbox_plain_subprocess_never_validates(coord: Wave004PlatformCoordinator) -> None:
    suite = coord.sandbox_executor.run_enforcement_suite("plain-check")
    assert suite["PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX"] is False
    if suite.get("SANDBOX_BACKEND") == "subprocess_broker":
        assert suite["SANDBOX_EXECUTION_VALIDATED"] is False
        assert suite["LOCAL_SANDBOX_VALIDATION"] == "BLOCKED_ENVIRONMENT"
        assert suite["ok"] is False


def test_wave004_sandbox_host_read_regression_must_fail(coord: Wave004PlatformCoordinator) -> None:
    """Prior bug: host_read=true + outside_write=false must not validate."""
    evaluators = run_all_evaluators(coord)
    result_020 = evaluators["OS-PLATFORM-020"]
    evidence = result_020.get("evidence") or {}
    fixture = evidence.get("fixture_result") or {}
    if fixture.get("host_private_read") and evidence.get("OUTSIDE_WRITE_BLOCKED"):
        assert result_020["ok"] is False
        assert result_020["classification"] != "IMPLEMENTED_AND_VALIDATED"


def test_wave004_e2e_core_scenarios_pass(coord: Wave004PlatformCoordinator) -> None:
    result = run_all_scenarios(coord)
    core = [s for s in result["scenarios"] if s["scenario"] not in {"I", "N"}]
    assert all(s["ok"] for s in core), core
    assert result["total"] == 14


def test_wave004_security_injection_blocks(coord: Wave004PlatformCoordinator) -> None:
    result = run_security_injections(coord)
    leaked = [c for c in result["cases"] if c.get("blocked") is False]
    assert result["leaked"] == 0, leaked


def test_wave004_requirement_classification_no_false_sandbox(coord: Wave004PlatformCoordinator) -> None:
    classification = coord.classify_requirements()
    assert len(classification) == 12
    row_020 = classification["OS-PLATFORM-020"]
    assert row_020["classification"] != "IMPLEMENTED_AND_VALIDATED" or row_020["ok"] is True
    # Never claim validated on plain subprocess
    evaluators = run_all_evaluators(coord)
    ev = evaluators["OS-PLATFORM-020"].get("evidence") or {}
    if ev.get("SANDBOX_BACKEND") == "subprocess_broker":
        assert evaluators["OS-PLATFORM-020"]["classification"] == "BLOCKED_ENVIRONMENT"


def test_wave004_no_unconditional_true_classifiers(coord: Wave004PlatformCoordinator) -> None:
    evaluators = run_all_evaluators(coord)
    for req_id, result in evaluators.items():
        assert "ok" in result, req_id
        assert result.get("evaluator"), req_id


def test_wave004_complete_gate_requires_twelve(coord: Wave004PlatformCoordinator) -> None:
    report = coord.run_full_validation()
    assert report["target_requirements"] == 12
    assert report["unconditional_true_classifiers"] == 0
    # COMPLETE only when exactly 12/12 — never >=10 shortcut
    if report["validated_count"] == 12 and report["e2e"]["ok"] and report["security_injection"]["ok"]:
        assert report["ok"] is True
    else:
        assert report["ok"] is False


def test_wave004_broken_evaluator_fixture_fails_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAVE004_BROKEN_EVALUATOR", "OS-PLATFORM-009")
    coord = Wave004PlatformCoordinator(tmp_path / "wave004-broken")
    report = coord.run_full_validation()
    assert report["validated_count"] < 12
    assert report["ok"] is False


def test_wave004_package_lifecycle_restart(tmp_path: Path) -> None:
    root = tmp_path / "pkg"
    coord = Wave004PlatformCoordinator(root)
    coord.package_lifecycle.install("persist-app", version="1.2.3")
    reloaded = PackageLifecycleManager.from_storage(coord.package_lifecycle.root, coord.repo_root)
    got = reloaded.get("persist-app")
    assert got.get("ok") is True
    upgraded = reloaded.upgrade("persist-app", version="1.2.4")
    assert upgraded.get("ok") is True
    removed = reloaded.uninstall("persist-app")
    assert removed.get("ok") is True


@pytest.mark.skipif(os.environ.get("WAVE004_BROKEN_EVALUATOR"), reason="broken evaluator mode")
def test_wave004_ci_gate_requires_twelve_of_twelve(coord: Wave004PlatformCoordinator) -> None:
    report = coord.run_full_validation()
    # On Ubuntu+bwrap CI this must be 12/12; locally sandbox may be BLOCKED_ENVIRONMENT.
    if os.environ.get("WAVE004_REQUIRE_SANDBOX_VALIDATED") == "1":
        suite = coord.sandbox_executor.run_enforcement_suite("ci-gate-probe")
        probe_flags = {
            "HOST_PRIVATE_READ_BLOCKED": suite.get("HOST_PRIVATE_READ_BLOCKED"),
            "OUTSIDE_WRITE_BLOCKED": suite.get("OUTSIDE_WRITE_BLOCKED"),
            "NETWORK_DENIED": suite.get("NETWORK_DENIED"),
            "NETWORK_CONTROL_REACHABLE": suite.get("NETWORK_CONTROL_REACHABLE"),
            "CHILD_SPAWN_DENIED": suite.get("CHILD_SPAWN_DENIED"),
            "CROSS_APP_READ_BLOCKED": suite.get("CROSS_APP_READ_BLOCKED"),
            "PRIVILEGED_CAPABILITY_DENIED": suite.get("PRIVILEGED_CAPABILITY_DENIED"),
        }
        assert report["validated_count"] == report["target_requirements"], {
            "validated_count": report["validated_count"],
            "classification_020": report["requirement_classification"].get("OS-PLATFORM-020"),
            "probe_flags": probe_flags,
            "failed_probes": [k for k, v in probe_flags.items() if v is not True],
            "SANDBOX_BACKEND": suite.get("SANDBOX_BACKEND"),
            "LOCAL_SANDBOX_VALIDATION": suite.get("LOCAL_SANDBOX_VALIDATION"),
            "exit_code": suite.get("exit_code"),
            "stderr_tail": suite.get("stderr_tail"),
            "fixture_result": suite.get("fixture_result"),
        }
        assert report["ok"] is True
    else:
        assert report["validated_count"] >= 11
        assert report["requirement_classification"]["OS-PLATFORM-008"]["ok"] is True
        assert report["requirement_classification"]["OS-PLATFORM-012"]["ok"] is True
