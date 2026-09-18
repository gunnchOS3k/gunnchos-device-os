"""CX2D lab must not touch Device Lab release evidence paths."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2d.lab import DEVICE_LAB_FORBIDDEN, attempt_lab_status, ensure_lab_tree

REPO = Path(__file__).resolve().parents[2]


def test_forbidden_paths_documented():
    assert any("device_lab_interactive_guest/artifacts" in p for p in DEVICE_LAB_FORBIDDEN)


def test_lab_tree_under_cx2d_namespace():
    lab = ensure_lab_tree(REPO)
    assert lab == REPO / "os_build" / "cx2d_linux_lab"
    assert lab.is_dir()
    status = attempt_lab_status(REPO)
    assert status["device_lab_paths_untouched"] is True
    assert status["evidence_namespace"] == "artifacts/complete_experience/cx2d"
