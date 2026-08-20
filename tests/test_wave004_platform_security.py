"""Wave 004 platform security tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator
from gunnchos_device_os.platform.e2e_scenarios import run_all_scenarios
from gunnchos_device_os.platform.security_injection import run_security_injections


@pytest.fixture()
def coord(tmp_path: Path) -> Wave004PlatformCoordinator:
    return Wave004PlatformCoordinator(tmp_path / "wave004")


def test_wave004_e2e_scenarios_pass(coord: Wave004PlatformCoordinator) -> None:
    result = run_all_scenarios(coord)
    assert result["passed"] == 6, result


def test_wave004_security_injection_blocks(coord: Wave004PlatformCoordinator) -> None:
    result = run_security_injections(coord)
    assert result["leaked"] == 0, result


def test_wave004_requirement_classification(coord: Wave004PlatformCoordinator) -> None:
    classification = coord.classify_requirements()
    assert len(classification) == 12
    validated = [k for k, v in classification.items() if v["classification"] == "IMPLEMENTED_AND_VALIDATED"]
    assert len(validated) >= 10


def test_wave004_full_validation(coord: Wave004PlatformCoordinator) -> None:
    report = coord.run_full_validation()
    assert report["e2e"]["ok"] is True
    assert report["security_injection"]["ok"] is True
    assert report["validated_count"] >= 10
