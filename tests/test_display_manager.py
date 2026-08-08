"""Display manager — layout profiles for family surfaces."""
from __future__ import annotations

import pytest

from gunnchos_device_os.display_manager import (
    DeviceSurface,
    DisplayManager,
    LAYOUT_PROFILES,
    SimulatedDisplayBackend,
)


def test_all_family_profiles_present():
    dm = DisplayManager()
    profiles = dm.list_profiles()
    for key in ("student_14_5", "ds_xl_coder", "handheld_hybrid", "dock"):
        assert key in profiles
        assert profiles[key]["primary"]
        assert profiles[key]["resolution"]["w"] > 0


def test_apply_each_surface():
    dm = DisplayManager(backend=SimulatedDisplayBackend())
    for surface in DeviceSurface:
        event = dm.apply_surface(surface)
        assert event["mock"] is False
        assert event["surface"] == surface.value
        assert event["applied"]["active"] is True
        assert dm.active_surface == surface
        assert dm.backend.current()["profile"]["name"] == surface.value


def test_switch_for_device_class_and_dock_toggle():
    dm = DisplayManager()
    dm.switch_for_device_class("student_14_5")
    assert dm.active_surface == DeviceSurface.STUDENT_14_5
    dm.set_docked(True)
    assert dm.active_surface == DeviceSurface.DOCK
    assert "external-dock" in dm.backend.current()["profile"]["displays"]
    dm.set_docked(False)
    assert dm.active_surface == DeviceSurface.HANDHELD_HYBRID


def test_unknown_surface_raises():
    dm = DisplayManager()
    with pytest.raises(ValueError):
        dm.apply_surface("crt_television")
    with pytest.raises(ValueError):
        dm.switch_for_device_class("unknown")


def test_status_not_mock():
    dm = DisplayManager()
    dm.apply_surface(DeviceSurface.DS_XL_CODER)
    status = dm.status()
    assert status["mock"] is False
    assert status["active_surface"] == "ds_xl_coder"
    assert sorted(status["profiles"]) == sorted(LAYOUT_PROFILES.keys())
