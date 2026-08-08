"""Runtime profiles — behavior changes across Student/DS-XL/Handheld/Dock."""
from __future__ import annotations

import pytest

from gunnchos_device_os.display_manager import DeviceSurface
from gunnchos_device_os.runtime_profiles import (
    AiTier,
    DeviceProfileId,
    RuntimeProfileController,
)


def test_all_family_profiles_listed():
    ctl = RuntimeProfileController()
    ids = ctl.list_profiles()
    assert set(ids) == {
        "student_14_5",
        "ds_xl_coder",
        "handheld_hybrid",
        "dock",
    }


def test_apply_student_changes_power_and_blocks_cloud():
    ctl = RuntimeProfileController()
    result = ctl.apply(DeviceProfileId.STUDENT)
    assert result["mock"] is False
    caps = ctl.effective_power_caps()
    assert caps["cpu_cap_percent"] == 70
    assert caps["gpu_cap_percent"] == 50
    assert ctl.allow_ai_request(100, cloud=True)["allowed"] is False
    assert ctl.allow_ai_request(100, cloud=False)["allowed"] is True
    assert ctl.display_manager.active_surface == DeviceSurface.STUDENT_14_5


def test_apply_handheld_is_more_constrained_than_student():
    ctl = RuntimeProfileController()
    ctl.apply(DeviceProfileId.STUDENT)
    student_cpu = ctl.effective_power_caps()["cpu_cap_percent"]
    ctl.apply(DeviceProfileId.HANDHELD)
    hand_cpu = ctl.effective_power_caps()["cpu_cap_percent"]
    assert hand_cpu < student_cpu
    assert ctl.ai_state["tier"] == AiTier.TINY_LOCAL.value
    assert ctl.allow_ai_request(600)["reason"] == "token_budget_exceeded"


def test_apply_ds_xl_sets_dual_topology_and_local_plus():
    ctl = RuntimeProfileController()
    r = ctl.apply("ds_xl_coder")
    assert r["display"]["dual_role"] == "top_bottom"
    assert set(r["display"]["displays"]) == {"ds-xl-top", "ds-xl-bottom"}
    assert r["ai"]["tier"] == AiTier.LOCAL_PLUS.value
    assert r["power"]["tdp_boost"] is True
    assert ctl.display_manager.active_surface == DeviceSurface.DS_XL_CODER


def test_apply_dock_enables_cloud_and_performance():
    ctl = RuntimeProfileController()
    ctl.apply(DeviceProfileId.DOCK)
    assert ctl.ai_state["cloud_requests_enabled"] is True
    assert ctl.allow_ai_request(1000, cloud=True)["allowed"] is True
    assert ctl.effective_power_caps()["cpu_cap_percent"] == 100
    assert ctl.topology_state["extend"] is True
    assert ctl.display_manager.active_surface == DeviceSurface.DOCK


def test_profile_switch_changes_behavior_not_json_only():
    ctl = RuntimeProfileController()
    ctl.apply(DeviceProfileId.HANDHELD)
    before = (
        ctl.effective_power_caps()["cpu_cap_percent"],
        ctl.ai_state["tier"],
        ctl.display_manager.active_surface,
    )
    ctl.apply(DeviceProfileId.DOCK)
    after = (
        ctl.effective_power_caps()["cpu_cap_percent"],
        ctl.ai_state["tier"],
        ctl.display_manager.active_surface,
    )
    assert before != after
    assert before[0] != after[0]
    assert before[1] != after[1]
    assert before[2] != after[2]


def test_governor_invoked_for_each_profile():
    ctl = RuntimeProfileController()
    for pid in DeviceProfileId:
        r = ctl.apply(pid)
        assert "profile" in r["governor"]
        assert r["governor"]["cpu_cap_percent"] > 0


def test_unknown_profile_raises():
    ctl = RuntimeProfileController()
    with pytest.raises(ValueError):
        ctl.apply("toaster")


def test_hooks_fire_on_apply():
    ctl = RuntimeProfileController()
    seen = []
    ctl.on_apply(lambda a: seen.append(a.profile_id))
    ctl.apply(DeviceProfileId.STUDENT)
    assert seen == ["student_14_5"]


def test_status_tracks_history():
    ctl = RuntimeProfileController()
    ctl.apply(DeviceProfileId.STUDENT)
    ctl.apply(DeviceProfileId.DS_XL)
    st = ctl.status()
    assert st["history_len"] == 2
    assert st["active_profile"] == "ds_xl_coder"
    assert st["mock"] is False
