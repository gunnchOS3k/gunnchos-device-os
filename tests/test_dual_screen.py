"""Dual-screen framework API — DS-XL top/bottom roles."""
from __future__ import annotations

import pytest

from gunnchos_device_os.dual_screen import (
    DualScreenFramework,
    Orientation,
    ScreenId,
    ScreenRole,
)


def test_rejects_non_ds_xl_device_class():
    with pytest.raises(ValueError):
        DualScreenFramework(device_class="student_14_5")


def test_default_layout_has_top_and_bottom():
    fw = DualScreenFramework()
    layout = fw.layout()
    assert layout["top"]["screen_id"] == "top"
    assert layout["bottom"]["screen_id"] == "bottom"
    assert layout["top"]["focused"] is True
    assert layout["mock"] is False


def test_apply_coder_workflow():
    fw = DualScreenFramework()
    snap = fw.apply_workflow("coder")
    assert snap["active_workflow"] == "coder"
    assert fw.screens["top"].role == ScreenRole.CODE
    assert fw.screens["bottom"].role == ScreenRole.PREVIEW


def test_all_workflows_apply():
    fw = DualScreenFramework()
    for name in fw.list_workflows():
        fw.apply_workflow(name)
        assert fw.active_workflow == name
        assert fw.screens["top"].role != ScreenRole.EMPTY


def test_assign_role_clears_named_workflow():
    fw = DualScreenFramework()
    fw.apply_workflow("coder")
    fw.assign_role(ScreenId.BOTTOM, ScreenRole.TERMINAL, app_id="term")
    assert fw.active_workflow is None
    assert fw.screens["bottom"].app_id == "term"


def test_swap_screens_exchanges_roles_and_orientation():
    fw = DualScreenFramework()
    fw.apply_workflow("coder")
    fw.swap_screens()
    assert fw.screens["top"].role == ScreenRole.PREVIEW
    assert fw.screens["bottom"].role == ScreenRole.CODE
    assert fw.orientation == Orientation.BOTTOM_TOP
    fw.swap_screens()
    assert fw.orientation == Orientation.TOP_BOTTOM


def test_focus_exactly_one():
    fw = DualScreenFramework()
    fw.focus(ScreenId.BOTTOM)
    assert fw.screens["bottom"].focused is True
    assert fw.screens["top"].focused is False
    assert fw.validate_roles() == [] or "focus_must_be_exactly_one" not in fw.validate_roles()


def test_place_app_assigns_and_focuses():
    fw = DualScreenFramework()
    fw.place_app("vscode", ScreenId.TOP, ScreenRole.CODE)
    fw.place_app("preview", ScreenId.BOTTOM, ScreenRole.PREVIEW)
    assert fw.screens["top"].app_id == "vscode"
    assert fw.screens["bottom"].focused is True


def test_unknown_workflow_raises():
    fw = DualScreenFramework()
    with pytest.raises(ValueError):
        fw.apply_workflow("cinema")


def test_validate_warns_when_both_empty():
    fw = DualScreenFramework()
    warnings = fw.validate_roles()
    assert "both_screens_empty" in warnings


def test_history_records_actions():
    fw = DualScreenFramework()
    fw.apply_workflow("debug")
    fw.swap_screens()
    actions = [h["action"] for h in fw.history]
    assert "apply_workflow" in actions
    assert "swap_screens" in actions
    assert all(h["mock"] is False for h in fw.history)
