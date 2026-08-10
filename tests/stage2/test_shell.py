"""Lane B — gunnchShell contract + adaptive profile E2E transitions."""
from __future__ import annotations

from gunnchos_device_os.stage2.shell.contract import ShellContract, COMPOSITOR_FOUNDATION
from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile, PROFILE_TABLE


def test_weston_foundation_documented():
    from pathlib import Path

    doc = Path("os_build/stage2/shell/FOUNDATION.md")
    text = doc.read_text()
    assert "Weston" in text
    assert COMPOSITOR_FOUNDATION == "weston"


def test_all_profiles_defined():
    expected = {
        "STUDENT_DESKTOP",
        "DSXL_DUAL_SCREEN",
        "HANDHELD_GAMEPAD",
        "HANDHELD_DOCKED",
        "OFFICE_DOCKED",
        "TOUCH_TABLET",
    }
    assert {p.value for p in AdaptiveProfile} == expected
    assert set(PROFILE_TABLE) == set(AdaptiveProfile)


def test_shell_contract_apis():
    shell = ShellContract(AdaptiveProfile.STUDENT_DESKTOP)
    assert shell.compositor == "weston"
    assert shell.open_launcher()["open"] is True
    assert shell.manage_window("tile")["last_action"]["action"] == "tile"
    assert shell.set_quick_setting("bluetooth", False)["bluetooth"] is False
    assert shell.notify("hi")["title"] == "hi"
    assert shell.media_control("play", "song")["playing"] is True
    assert shell.search("x")["results"]
    assert shell.file_share_action("/tmp/a")["action"] == "share"
    assert shell.session_info()["compositor"] == "weston"
    assert shell.set_accessibility(high_contrast=True)["high_contrast"] is True
    snap = shell.snapshot()
    for key in (
        "launcher",
        "window_management",
        "quick_settings",
        "notifications",
        "media",
        "search",
        "file_share",
        "session",
        "display_topology",
        "input_modality",
        "dock_state",
        "device_role",
        "accessibility",
    ):
        assert key in snap["api"]


def test_e2e_handheld_dock_desktop_undock():
    shell = ShellContract(AdaptiveProfile.HANDHELD_GAMEPAD)
    log = shell.run_transition(["dock", "desktop", "undock"])
    assert [e["profile"] for e in log] == [
        "HANDHELD_DOCKED",
        "STUDENT_DESKTOP",
        "HANDHELD_GAMEPAD",
    ]
    assert log[0]["docked"] is True
    assert log[2]["docked"] is False


def test_e2e_dsxl_external_attach_detach():
    shell = ShellContract(AdaptiveProfile.STUDENT_DESKTOP)
    log = shell.run_transition(["external_attach", "external_detach"])
    assert log[0]["profile"] == "DSXL_DUAL_SCREEN"
    assert log[0]["dual_screen"] is True
    assert any(d["id"] == "external" for d in log[0]["displays"])
    assert log[1]["profile"] == "STUDENT_DESKTOP"
    assert len(log[1]["displays"]) == 1
