"""CX2F lab isolation — Device Lab untouched; CX2E overlay immutable policy."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2f.paths import CX2E_OVERLAY_REL, DEVICE_LAB_FORBIDDEN, cx2f_lab_root

REPO = Path(__file__).resolve().parents[2]


def test_lab_namespace():
    assert cx2f_lab_root(REPO).as_posix().endswith("os_build/cx2f_linux_lab")


def test_device_lab_forbidden_not_cx2f():
    for p in DEVICE_LAB_FORBIDDEN:
        assert "cx2f" not in p


def test_parent_overlay_path():
    assert CX2E_OVERLAY_REL.endswith("cx2e-aarch64.qcow2")
