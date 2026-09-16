"""CX2E — shell authority, guest-fact truth, fail-closed tokens."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2e import (
    CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY,
    FULL_COMPLETE_EXPERIENCE_COMPLETE,
)
from gunnchos_device_os.cx2e.evidence import write_evidence
from gunnchos_device_os.cx2e.journeys import upgrade_journeys
from gunnchos_device_os.cx2e.tokens import Cx2eTokens, apply_session_facts, fail_closed_tokens

REPO = Path(__file__).resolve().parents[2]


def test_shell_authority():
    assert CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY is True
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert (REPO / "apps/gunnch_shell/package.json").is_file()


def test_truth_not_host_platform():
    # Darwin host with false guest facts must not pass
    t = apply_session_facts(
        fail_closed_tokens(),
        {
            "guest_booted": False,
            "guest_is_linux": False,
            "compositor_running": False,
            "wayland_socket_alive": False,
            "shell_window_rendered": False,
        },
    )
    assert t.graphical_truth() is False
    # Explicit guest facts earn truth regardless of host OS
    t2 = apply_session_facts(
        fail_closed_tokens(),
        {
            "guest_booted": True,
            "guest_is_linux": True,
            "compositor_running": True,
            "wayland_socket_alive": True,
            "shell_window_rendered": True,
        },
    )
    assert t2.graphical_truth() is True
    assert t2.CX2E_QEMU_GUEST_BOOT_PASS is True
    assert t2.CX2E_WESTON_SESSION_PASS is True


def test_journeys_fail_closed_without_facts():
    up = upgrade_journeys({})
    assert up["any_real_user_journey_digital_pass"] is False
    for j in up["journeys"].values():
        assert j["REAL_USER_JOURNEY_DIGITAL_PASS"] is False


def test_evidence_writer_fail_closed():
    report = write_evidence(REPO, facts={}, provision={"ok": False, "blocker": "unit_test"})
    assert report["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert report["firewall"]["device_lab_134_unaltered"] is True
    assert report["tokens"]["CX2E_REAL_HOME_WINDOW"] is False
    root = REPO / "artifacts/complete_experience/cx2e"
    assert (root / "CX2E_EVIDENCE_REPORT.json").exists()


def test_token_defaults():
    t = Cx2eTokens()
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert t.CX2E_HUMAN_A11Y_PENDING is True
