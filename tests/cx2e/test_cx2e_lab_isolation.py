"""CX2E lab must not touch Device Lab release evidence paths."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2e.paths import DEVICE_LAB_FORBIDDEN, ensure_lab_tree, evidence_root
from gunnchos_device_os.cx2e.qemu import host_prereqs, prepare_overlay

REPO = Path(__file__).resolve().parents[2]


def test_forbidden_paths_documented():
    assert any("device_lab_interactive_guest/artifacts" in p for p in DEVICE_LAB_FORBIDDEN)


def test_lab_tree_under_cx2e_namespace():
    lab = ensure_lab_tree(REPO)
    assert lab == REPO / "os_build" / "cx2e_linux_lab"
    assert evidence_root(REPO) == REPO / "artifacts" / "complete_experience" / "cx2e"


def test_overlay_prep_isolated():
    ov = prepare_overlay(REPO)
    assert "cx2e_linux_lab" in (ov.get("overlay") or ov.get("base_copy") or "")
    assert "device_lab_interactive_guest/artifacts" not in str(ov)


def test_host_prereqs_shape():
    p = host_prereqs()
    assert "qemu_system_aarch64" in p
    assert "accel" in p
