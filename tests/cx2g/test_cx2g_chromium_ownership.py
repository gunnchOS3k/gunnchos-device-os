"""CX2G Chromium ownership — fail closed; never execute pkill -f chromium."""

from __future__ import annotations

import inspect
from pathlib import Path

from gunnchos_device_os.cx2g.session import launch_chromium_shell, stop_owned_shell_runtime
from gunnchos_device_os.cx2g.tokens import Cx2gTokens

REPO = Path(__file__).resolve().parents[2]


def test_no_pkill_f_chromium_command_in_stop_or_launch_bodies():
    stop_src = inspect.getsource(stop_owned_shell_runtime)
    launch_src = inspect.getsource(launch_chromium_shell)
    # Executable remote scripts must not contain the forbidden command
    assert "pkill -f chromium ||" not in stop_src
    assert "pkill -f chromium ||" not in launch_src
    assert 'pkill -f chromium"' not in stop_src
    assert "systemctl stop" in stop_src
    assert "cx2g-gunnch-shell.service" in launch_src


def test_stop_owned_shell_runtime_exists():
    assert callable(stop_owned_shell_runtime)
    src = inspect.getsource(stop_owned_shell_runtime)
    assert "cgroup" in src.lower() or "ControlGroup" in src or "cgroup.procs" in src


def test_launch_uses_owned_unit_name():
    src = inspect.getsource(launch_chromium_shell)
    assert "cx2g-gunnch-shell.service" in src
    assert "Restart=no" in src
    assert "9222" in src


def test_gate_requires_chromium_runtime_and_wayland_surface():
    t = Cx2gTokens(
        CX2G_NON_CLOUD_KERNEL_BOOT_PASS=True,
        CX2G_DRM_CARD_PASS=True,
        CX2G_WESTON_DRM_PASS=True,
        CX2G_GUNNCH_SHELL_RENDER_PASS=True,
        CX2G_QEMU_FRAMEBUFFER_CAPTURE_PASS=True,
        CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS=True,
        CX2G_CHROMIUM_RUNTIME_PASS=False,
        CX2G_WAYLAND_SURFACE_PASS=False,
    )
    assert t.gate_shell_stack() is False
    t.CX2G_CHROMIUM_RUNTIME_PASS = True
    t.CX2G_WAYLAND_SURFACE_PASS = True
    assert t.gate_shell_stack() is True


def test_human_a11y_always_pending():
    t = Cx2gTokens()
    assert t.CX2G_HUMAN_A11Y_PENDING is True


def test_cx2f_still_has_pkill_for_root_cause_contrast():
    cx2f = (REPO / "gunnchos_device_os/cx2f/session.py").read_text()
    assert "pkill -f chromium" in cx2f
