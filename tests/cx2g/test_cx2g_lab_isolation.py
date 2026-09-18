"""CX2G lab isolation — Device Lab untouched; CX2F/CX2E overlay immutable policy."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2g.paths import (
    CX2E_OVERLAY_REL,
    CX2F_OVERLAY_REL,
    DEVICE_LAB_FORBIDDEN,
    cx2g_lab_root,
)

REPO = Path(__file__).resolve().parents[2]


def test_lab_namespace():
    assert cx2g_lab_root(REPO).as_posix().endswith("os_build/cx2g_linux_lab")


def test_device_lab_forbidden_not_cx2g():
    for p in DEVICE_LAB_FORBIDDEN:
        assert "cx2g" not in p


def test_parent_overlay_paths():
    assert CX2F_OVERLAY_REL.endswith("cx2f-aarch64.qcow2")
    assert CX2E_OVERLAY_REL.endswith("cx2e-aarch64.qcow2")
