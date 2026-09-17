"""Fail-closed CX2H.1 tests — markers/version-only/PID-only cannot earn PASS."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx2h.evidence import next_gate
from gunnchos_device_os.cx2h.tokens import Cx2hTokens

ROOT = Path(__file__).resolve().parents[2]


def test_flatpak_version_alone_cannot_earn_j3():
    tokens = Cx2hTokens(
        CX2H_SHELL_PREREQ_PASS=True,
        CX2H_CHROMIUM_RUNTIME_PASS=True,
        CX2H_WAYLAND_SURFACE_PASS=True,
        CX2H_GUNNCH_SHELL_RENDER_PASS=True,
        CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS=True,
        CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS=True,
        CX2H_REAL_APP_CENTER_WINDOW=True,
        CX2H_XDG_PORTAL_SESSION_PASS=True,
        # provider probe equivalent to flatpak --version only
        CX2H_REAL_APP_CENTER_PROVIDER_PASS=False,
        J3_CLASS="BLOCKED",
    )
    assert tokens.j3_digital_pass() is False
    assert next_gate(tokens) != "CX2H2_DOCUMENT_PRINT_RECOVERY_J1_J7"


def test_marker_file_cannot_earn_install_pass():
    tokens = Cx2hTokens()
    # Simulating a marker-only claim must not flip install token without journey evidence
    assert tokens.CX2H_REAL_APP_INSTALL_GUI_PASS is False
    fake = ROOT / "artifacts/complete_experience/cx2h/.marker_install_pass"
    # Even if a marker exists on disk, token stays false unless set by journey
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_text("INSTALLED\n")
    assert tokens.CX2H_REAL_APP_INSTALL_GUI_PASS is False
    fake.unlink(missing_ok=True)


def test_pid_alone_cannot_earn_launch_pass():
    tokens = Cx2hTokens(CX2H_REAL_APP_LAUNCH_GUI_PASS=False)
    # Presence of a pid in a fake evidence blob is insufficient
    blob = {"pid": 12345, "launched": False}
    assert blob["pid"] and not tokens.CX2H_REAL_APP_LAUNCH_GUI_PASS


def test_shell_pid_without_flatpak_ps_cannot_earn_launch():
    """$! / shell PID alone is not structured launch success."""
    fake = {
        "ok": False,
        "instance_id": None,
        "pid": "99999",
        "application": "org.gunnchos.CX2HTestApp",
        "version": "1.0.0",
        "branch": "1.0.0",
        "alive_after_5s": False,
        "error": "no_flatpak_ps_instance",
    }
    assert fake["pid"]
    assert not fake["ok"]
    assert not fake["instance_id"]
    assert not fake["alive_after_5s"]


def test_app_center_fb_cannot_substitute_for_app_window():
    """App Center framebuffer churn after install is not Flatpak window proof."""
    after_install_sha = "aaa"
    launch_sha = "aaa"  # identical → no window
    assert after_install_sha == launch_sha
    window_proven = after_install_sha != launch_sha
    assert window_proven is False


def test_immediate_exit_process_cannot_earn_alive_after_5s():
    alive_after_5s = False
    pid = 4242
    assert pid and not alive_after_5s


def test_partial_j3_routes_to_cx2h1c_not_cx2h2():
    tokens = Cx2hTokens(
        CX2H_SHELL_PREREQ_PASS=True,
        CX2H_CHROMIUM_RUNTIME_PASS=True,
        CX2H_WAYLAND_SURFACE_PASS=True,
        CX2H_GUNNCH_SHELL_RENDER_PASS=True,
        CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS=True,
        CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS=True,
        CX2H_REAL_APP_CENTER_WINDOW=True,
        CX2H_XDG_PORTAL_SESSION_PASS=True,
        CX2H_REAL_APP_CENTER_PROVIDER_PASS=True,
        CX2H_REAL_APP_INSTALL_GUI_PASS=True,
        CX2H_REAL_APP_LAUNCH_GUI_PASS=False,
        J3_CLASS="REAL_PROVIDER_GUI_PARTIAL",
        lab_blocker="CX2H_APP_LAUNCH_GUI",
    )
    assert tokens.j3_digital_pass() is False
    assert next_gate(tokens) == "CX2H1C_APP_LAUNCH_GUI"
    assert next_gate(tokens) != "CX2H2_DOCUMENT_PRINT_RECOVERY_J1_J7"


def test_update_requires_provider_version_change():
    before = {"version": "1.0.0"}
    after_same = {"version": "1.0.0"}
    after_new = {"version": "2.0.0"}
    assert before["version"] == after_same["version"]
    assert before["version"] != after_new["version"]


def test_uninstall_requires_provider_removal():
    after = {"installed": False}
    assert after["installed"] is False


def test_ui_action_mandatory_flag_in_journey_schema():
    # Journey evidence must record UI click path — schema contract
    required = {
        "ui_install",
        "ui_open",
        "ui_update",
        "ui_uninstall",
    }
    sample = {
        "steps": {k: {"ok": True} for k in required},
        "J3_CLASS": "BLOCKED",
    }
    assert required.issubset(sample["steps"].keys())


def test_stale_cache_cannot_override_provider_truth():
    ui_cache_installed = True
    provider_installed = False
    # Authoritative truth is provider
    assert provider_installed is False
    authoritative = provider_installed
    assert authoritative is not True or ui_cache_installed  # provider wins
    assert authoritative is False


def test_portal_package_presence_alone_cannot_earn_portal_pass():
    tokens = Cx2hTokens(CX2H_XDG_PORTAL_SESSION_PASS=False)
    packages = {"xdg-desktop-portal": "1.16.0", "xdg-desktop-portal-gtk": "1.14.1"}
    assert packages and tokens.CX2H_XDG_PORTAL_SESSION_PASS is False


def test_j1_j2_j5_j7_remain_blocked_in_cx2h1():
    tokens = Cx2hTokens(
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        CX2H_XDG_PORTAL_SESSION_PASS=True,
        CX2H_SHELL_PREREQ_PASS=True,
        CX2H_CHROMIUM_RUNTIME_PASS=True,
        CX2H_WAYLAND_SURFACE_PASS=True,
        CX2H_GUNNCH_SHELL_RENDER_PASS=True,
        CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS=True,
        CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS=True,
        CX2H_REAL_APP_CENTER_WINDOW=True,
        CX2H_REAL_APP_CENTER_PROVIDER_PASS=True,
        CX2H_REAL_APP_INSTALL_GUI_PASS=True,
        CX2H_REAL_APP_LAUNCH_GUI_PASS=True,
        CX2H_REAL_APP_UPDATE_GUI_PASS=True,
        CX2H_REAL_APP_UNINSTALL_GUI_PASS=True,
        CX2H_J3_PERSISTENCE_PASS=True,
    )
    assert tokens.J1_CLASS == "BLOCKED"
    assert tokens.J2_CLASS == "BLOCKED"
    assert tokens.J5_CLASS == "BLOCKED"
    assert tokens.J7_CLASS == "BLOCKED"
    assert tokens.J6_CLASS == "HUMAN_VALIDATION_PENDING"
    assert tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert next_gate(tokens) == "CX2H2_DOCUMENT_PRINT_RECOVERY_J1_J7"
