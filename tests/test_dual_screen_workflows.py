"""Dual-screen workflow stubs — one automated validation per workflow type."""
from __future__ import annotations

import pytest

from gunnchos_device_os.dual_screen import DualScreenFramework
from gunnchos_device_os.dual_screen_workflows import (
    WORKFLOW_TYPES,
    place_app_stubs,
    run_all_workflow_validations,
    validate_workflow,
)


@pytest.mark.parametrize("name", sorted(WORKFLOW_TYPES.keys()))
def test_each_workflow_type_validates(name: str):
    fw = DualScreenFramework()
    placed = place_app_stubs(fw, name)
    assert placed["apps"]["top"]
    assert placed["apps"]["bottom"]
    result = validate_workflow(fw, name)
    assert result.ok, result.checks
    assert result.workflow == name


def test_run_all_workflow_validations_token():
    report = run_all_workflow_validations()
    assert report["ok"] is True
    assert report["workflow_count"] == len(WORKFLOW_TYPES)
    assert report["token"] == "GUNNCHOS_DUAL_SCREEN_WORKFLOW_DIGITAL_PASS"
    assert report["full_operational_product_claimed"] is False
    for r in report["results"]:
        assert r["ok"] is True


def test_unknown_workflow_type_raises():
    fw = DualScreenFramework()
    with pytest.raises(ValueError):
        validate_workflow(fw, "cinema")
