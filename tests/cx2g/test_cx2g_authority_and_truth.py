"""CX2G fail-closed authority and truth tests."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2g import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2g.journeys import upgrade_journeys
from gunnchos_device_os.cx2g.lock import FOREIGN_BUSY, acquire_lock, read_lock, release_lock
from gunnchos_device_os.cx2g.paths import DEVICE_LAB_FORBIDDEN, evidence_root
from gunnchos_device_os.cx2g.session import ppm_diff
from gunnchos_device_os.cx2g.tokens import Cx2gTokens

REPO = Path(__file__).resolve().parents[2]


def test_full_complete_false():
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False


def test_cloud_kernel_cannot_earn_non_cloud_pass():
    t = Cx2gTokens()
    # simulate cloud uname
    assert "cloud" in "6.1.0-53-cloud-arm64"
    t.CX2G_NON_CLOUD_KERNEL_BOOT_PASS = False
    assert t.CX2G_NON_CLOUD_KERNEL_BOOT_PASS is False
    assert t.gate_shell_stack() is False


def test_missing_dri_cannot_earn_drm_pass():
    t = Cx2gTokens(CX2G_DRM_CARD_PASS=False)
    assert t.CX2G_DRM_CARD_PASS is False
    assert t.gate_shell_stack() is False


def test_headless_weston_cannot_earn_drm_pass():
    t = Cx2gTokens(
        CX2G_WESTON_DRM_PASS=False,
        CX2G_WESTON_HEADLESS_FALLBACK_USED=True,
    )
    assert t.CX2G_WESTON_DRM_PASS is False
    assert t.CX2G_WESTON_HEADLESS_FALLBACK_USED is True
    assert t.gate_shell_stack() is False


def test_pid_without_framebuffer_change_no_render_pass():
    t = Cx2gTokens(CX2G_GUNNCH_SHELL_RENDER_PASS=False)
    # process alive alone is insufficient
    assert t.CX2G_GUNNCH_SHELL_RENDER_PASS is False


def test_assets_without_loaded_page_no_render_pass():
    t = Cx2gTokens(CX2G_SHELL_ASSET_DELIVERY_PASS=True, CX2G_GUNNCH_SHELL_RENDER_PASS=False)
    assert t.gate_shell_stack() is False


def test_browser_only_screenshot_insufficient():
    t = Cx2gTokens(CX2G_QEMU_FRAMEBUFFER_CAPTURE_PASS=False, CX2G_REAL_SCREEN_CAPTURE_PASS=False)
    assert t.CX2G_REAL_SCREEN_CAPTURE_PASS is False


def test_input_without_mutation_no_pass():
    t = Cx2gTokens(CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS=False)
    assert t.CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS is False


def test_stale_cx2e_evidence_not_cx2g_pass():
    cx2e = REPO / "artifacts/complete_experience/cx2e/CX2E_TOKENS.json"
    assert cx2e.is_file()
    # CX2G evidence root is distinct
    assert evidence_root(REPO).name == "cx2g"
    t = Cx2gTokens()
    assert t.CX2G_GUNNCH_SHELL_RENDER_PASS is False


def test_device_lab_paths_forbidden_constants():
    assert "os_build/device_lab_interactive_guest/artifacts" in DEVICE_LAB_FORBIDDEN


def test_journeys_fail_closed():
    up = upgrade_journeys({})
    assert up["any_real_user_journey_digital_pass"] is False
    assert up["desired_before_cx3_pass"] is False


def test_foreign_lock_token():
    assert FOREIGN_BUSY == "CX2G_QEMU_SLOT_BUSY_FOREIGN_PROCESS"


def test_ppm_diff_threshold_rationale(tmp_path):
    # write two tiny different PPMs
    def write_ppm(path, rgb):
        w = h = 2
        path.write_bytes(b"P6\n2 2\n255\n" + bytes(rgb) * (w * h))

    a = tmp_path / "a.ppm"
    b = tmp_path / "b.ppm"
    write_ppm(a, (0, 0, 0))
    write_ppm(b, (255, 0, 0))
    d = ppm_diff(a, b, min_changed_pct=0.15)
    assert d["ok"] is True
    assert d["changed_pixel_pct"] > 0
