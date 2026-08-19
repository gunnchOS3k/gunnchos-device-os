"""Pinned gunnchAI ↔ device-os compatibility contract tests."""
from __future__ import annotations

from gunnchos_device_os.cross_repo_gunnchai.contract import (
    CONTRACT_PATH,
    load_contract,
    validate_contract,
    verify_owner_artifacts,
)


GUNNCHAI_PIN = "d357846810b952ed49a2c168c05720143b32796b"
DEVICE_OS_PIN = "d5c2d179ae21efe5191b7d35a2080878112f18e4"


def test_contract_file_exists():
    assert CONTRACT_PATH.is_file()


def test_contract_validates_against_schema():
    assert validate_contract()["ok"] is True


def test_accepted_main_pins():
    doc = load_contract()
    assert doc["evidence_class"] == "ACCEPTED_MAIN"
    assert doc["gunnchai"]["accepted_main_sha"] == GUNNCHAI_PIN
    assert doc["gunnchai"]["merged_pr"] == 43
    assert doc["device_os"]["accepted_main_sha"] == DEVICE_OS_PIN
    assert doc["coupling_policy"]["blocks_device_os_ci"] is False


def test_device_os_assumptions_fail_closed():
    assumptions = load_contract()["device_os_assumptions"]
    assert assumptions["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert assumptions["GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS"] is True
    assert assumptions["HUMAN_E6"] is False


def test_api_surface_lists_stage2_capabilities():
    api = load_contract()["api_surface"]["stage2_capability_http"]
    assert "POST /v1/capability/" in api["invoke"]
    assert "user_id" in api["request_body"]


def test_sibling_verify_without_repo_is_non_fatal():
    result = verify_owner_artifacts(gunnchai_root=None)
    assert result["sibling_present"] is False
    assert result["ok"] is False
    assert "note" in result
