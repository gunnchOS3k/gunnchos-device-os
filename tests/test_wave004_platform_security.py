"""Wave 004 platform security tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator
from gunnchos_device_os.platform.e2e_scenarios import run_all_scenarios
from gunnchos_device_os.platform.requirement_evaluators import run_all_evaluators
from gunnchos_device_os.platform.security_injection import run_security_injections


@pytest.fixture()
def coord(tmp_path: Path) -> Wave004PlatformCoordinator:
    return Wave004PlatformCoordinator(tmp_path / "wave004")


def test_wave004_e2e_scenarios_pass(coord: Wave004PlatformCoordinator) -> None:
    result = run_all_scenarios(coord)
    assert result["passed"] == 11, result


def test_wave004_security_injection_blocks(coord: Wave004PlatformCoordinator) -> None:
    result = run_security_injections(coord)
    assert result["leaked"] == 0, result


def test_wave004_requirement_classification(coord: Wave004PlatformCoordinator) -> None:
    classification = coord.classify_requirements()
    assert len(classification) == 12
    validated = [k for k, v in classification.items() if v["classification"] == "IMPLEMENTED_AND_VALIDATED"]
    assert len(validated) == 12, classification
    assert all("evaluator" in v for v in classification.values())


def test_wave004_no_unconditional_true_classifiers(coord: Wave004PlatformCoordinator) -> None:
    evaluators = run_all_evaluators(coord)
    for req_id, result in evaluators.items():
        assert "ok" in result, req_id
        assert result.get("evaluator"), req_id


def test_wave004_full_validation(coord: Wave004PlatformCoordinator) -> None:
    report = coord.run_full_validation()
    assert report["e2e"]["ok"] is True
    assert report["security_injection"]["ok"] is True
    assert report["validated_count"] == 12
    assert report["unconditional_true_classifiers"] == 0
    assert report["ok"] is True


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
    reloaded = coord.package_lifecycle.from_storage(coord.package_lifecycle.root, coord.repo_root)
    got = reloaded.get("persist-app")
    assert got.get("ok") is True
    upgraded = reloaded.upgrade("persist-app", version="1.2.4")
    assert upgraded.get("ok") is True
    removed = reloaded.uninstall("persist-app")
    assert removed.get("ok") is True


@pytest.mark.skipif(os.environ.get("WAVE004_BROKEN_EVALUATOR"), reason="broken evaluator mode")
def test_wave004_ci_gate_requires_twelve_of_twelve(coord: Wave004PlatformCoordinator) -> None:
    report = coord.run_full_validation()
    assert report["validated_count"] == report["target_requirements"]
