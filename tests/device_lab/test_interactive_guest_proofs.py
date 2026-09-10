"""WP-011R: Interactive Guest LIVE/DSXL/RING proof attempts — honesty tests.

These tests never boot real QEMU. They exercise the attempt functions with a
fake session (no bound guest agent, or an agent stub answering `stub: true`)
and assert every `*_PASS` token comes back `False` with an honest blocker —
never a hardcoded/optimistic True. Earning `True` for real requires a live
virtio-serial guest-agent session against the provisioned Debian guest,
which is exercised manually (long-running QEMU boot), not in unit tests.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gunnchos_device_os.device_lab.interactive_guest_proofs import (
    CLAIM,
    _require_real_virtio_serial,
    attempt_dsxl_dual_compositor_pass,
    attempt_live_visual_pass,
    attempt_ring_app_mutation_pass,
)


class _NoAgentSession:
    """Simulates a session where the guest agent never bound (boot failed)."""

    agent = None
    monitor_sock = None


class _StubAgent:
    """Simulates the honest host-side mailbox stub — must never count as proof."""

    timeout_sec = 5.0

    def call(self, cmd: str, **kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "stub": True, "transport": "mailbox_stub", "cmd": cmd}


class _StubSession:
    agent = _StubAgent()
    monitor_sock = None


def test_claim_never_claims_shipping_or_silicon_exact():
    assert "SHIPPING_IMAGE=false" in CLAIM
    assert "SILICON_EXACT_EMULATION=false" in CLAIM


def test_require_real_virtio_serial_rejects_stub_transport():
    assert _require_real_virtio_serial({"ok": True, "transport": "mailbox_stub"}) is False
    assert _require_real_virtio_serial({"ok": True, "agent_path_label": "host_stub"}) is False
    assert _require_real_virtio_serial("not-a-dict") is False


def test_require_real_virtio_serial_accepts_real_transport_or_honest_failure():
    assert _require_real_virtio_serial({"ok": True, "transport": "virtio_serial"}) is True
    assert _require_real_virtio_serial({"ok": False, "reason": "timeout"}) is True


@pytest.mark.parametrize(
    "session_cls",
    [_NoAgentSession, _StubSession],
)
def test_attempt_live_visual_pass_is_honest_false_without_real_agent(tmp_path: Path, session_cls: type):
    result = attempt_live_visual_pass(session_cls(), tmp_path)
    assert result["LIVE_GUNNCHOS_VISUAL_PASS"] is False
    assert "blocker" in result
    written = json.loads((tmp_path / "LIVE_VISUAL_EVIDENCE.json").read_text(encoding="utf-8"))
    assert written["LIVE_GUNNCHOS_VISUAL_PASS"] is False


@pytest.mark.parametrize(
    "session_cls",
    [_NoAgentSession, _StubSession],
)
def test_attempt_dsxl_dual_compositor_pass_is_honest_false_without_real_agent(
    tmp_path: Path, session_cls: type
):
    result = attempt_dsxl_dual_compositor_pass(session_cls(), tmp_path)
    assert result["DSXL_DUAL_COMPOSITOR_UX_PASS"] is False
    written = json.loads((tmp_path / "DSXL_COMPOSITOR_UX_EVIDENCE.json").read_text(encoding="utf-8"))
    assert written["DSXL_DUAL_COMPOSITOR_UX_PASS"] is False


@pytest.mark.parametrize(
    "session_cls",
    [_NoAgentSession, _StubSession],
)
def test_attempt_ring_app_mutation_pass_is_honest_false_without_real_agent(
    tmp_path: Path, session_cls: type
):
    result = attempt_ring_app_mutation_pass(session_cls(), tmp_path)
    assert result["RING_TO_REAL_APP_STATE_MUTATION_PASS"] is False
    assert result["marker_found_in_after"] is False
    written = json.loads((tmp_path / "RING_APP_MUTATION_EVIDENCE.json").read_text(encoding="utf-8"))
    assert written["RING_TO_REAL_APP_STATE_MUTATION_PASS"] is False


def test_attempt_functions_never_hardcode_pass_true_in_source():
    """Static guard: the attempt functions must compute `earned`/`mutated`
    from real response data, never assign a literal `True` to a `*_PASS` key."""
    import inspect

    import gunnchos_device_os.device_lab.interactive_guest_proofs as mod

    src = inspect.getsource(mod)
    for token in (
        '"LIVE_GUNNCHOS_VISUAL_PASS": True',
        '"DSXL_DUAL_COMPOSITOR_UX_PASS": True',
        '"RING_TO_REAL_APP_STATE_MUTATION_PASS": True',
    ):
        assert token not in src


def test_ring_browser_memo_server_refuses_marker_wipe():
    """Regression: Wayland Chromium must not overwrite a committed Ring marker."""
    import inspect

    import gunnchos_device_os.device_lab.interactive_guest_proofs as mod

    src = inspect.getsource(mod.attempt_ring_app_mutation_pass)
    assert "drive_marker" in src
    assert "drive_marker not in body" in src
    assert "chmod a-w" in src
    assert "browser_hl_committed_freeze" in src
    # Seed reset must kill Chromium before rewriting MemoStart.
    assert "killall -q oosplash soffice.bin mousepad chromium" in src


def test_ring_game_requires_godot45_not_zombie_pgrep():
    """Pedestrian Ring target is Godot 4.5; zombies must not count as ALIVE."""
    import inspect

    import gunnchos_device_os.device_lab.interactive_guest_proofs as mod

    src = inspect.getsource(mod.attempt_ring_app_mutation_pass)
    assert "RING_BLOCKED_BY_GODOT_GUEST_RUNTIME" in src
    assert "_ensure_godot45_in_guest" in src
    assert "_launch_godot_wayland" in src
    assert "_pid_alive_non_zombie" in src
    assert "zombie_rejected" in src
    assert 'test "$alive" = 1 && echo ALIVE' not in src
    assert "pgrep -af '[g]odot' | head; test" not in src



def test_pedestrian_overlay_uses_parse_input_event_and_progression_save():
    from gunnchos_device_os.device_lab.guest_agent_overlays import PEDESTRIAN_OVERLAY_GD

    assert "Input.parse_input_event" in PEDESTRIAN_OVERLAY_GD
    assert 'call("add_xp"' in PEDESTRIAN_OVERLAY_GD or "ProgressionSave.add_xp" in PEDESTRIAN_OVERLAY_GD
    assert 'call("unlock"' in PEDESTRIAN_OVERLAY_GD or "ProgressionSave.unlock" in PEDESTRIAN_OVERLAY_GD
    assert 'call("save"' in PEDESTRIAN_OVERLAY_GD or "ProgressionSave.save()" in PEDESTRIAN_OVERLAY_GD
    assert "production_gate_harness" in PEDESTRIAN_OVERLAY_GD
    assert "Not --quit-after" in PEDESTRIAN_OVERLAY_GD


def test_ring_skips_virtio_godot_put_when_env_set():
    """Ring must not hang on multi-MB Godot virtio file_put (17E A5)."""
    import inspect
    import gunnchos_device_os.device_lab.interactive_guest_proofs as mod
    src = inspect.getsource(mod.attempt_ring_app_mutation_pass)
    assert "godot45_http_failed_virtio_put_skipped" in src
    assert "GUNNCH_RING_SKIP_VIRTIO" in src
    assert "game_seed_verify" in src


def test_pedestrian_overlay_writes_ring_receipt():
    from gunnchos_device_os.device_lab.guest_agent_overlays import PEDESTRIAN_OVERLAY_GD
    assert "ring_mutation_receipt.txt" in PEDESTRIAN_OVERLAY_GD
    assert "ring:mutation" in PEDESTRIAN_OVERLAY_GD


def test_deploy_pedestrian_skips_virtio_when_env_set():
    import inspect
    from gunnchos_device_os.device_lab import interactive_guest_four_games as mod
    src = inspect.getsource(mod._deploy_pedestrian_pursuit)
    assert "pp_http_failed_virtio_put_skipped" in src
    assert "GUNNCH_RING_SKIP_VIRTIO_PP_PUT" in src


def test_pedestrian_patch_py_compiles_and_patches():
    import subprocess, tarfile, tempfile
    from pathlib import Path
    from gunnchos_device_os.device_lab.guest_agent_overlays import (
        PEDESTRIAN_PATCH_PY,
        PEDESTRIAN_OVERLAY_GD,
    )
    compile(PEDESTRIAN_PATCH_PY, "<patch>", "exec")
    root = Path(__file__).resolve().parents[2]
    tar = root / "artifacts/wp011r/owner_games_guest_bundle/pedestrian-pursuit.tar.gz"
    if not tar.is_file():
        return
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(tar) as tf:
            tf.extractall(td)
        proj = Path(td) / "pedestrian-pursuit"
        (proj / "device_lab_ring_input_overlay.gd").write_text(PEDESTRIAN_OVERLAY_GD, encoding="utf-8")
        script = Path(td) / "patch.py"
        script.write_text(PEDESTRIAN_PATCH_PY, encoding="utf-8")
        r = subprocess.run(["python3", str(script), str(proj)], capture_output=True, text=True, check=False)
        assert r.returncode == 0, r.stderr
        assert "OVERLAY_PATCHED True" in r.stdout
        assert "DeviceLabRingInputOverlay=" in (proj / "project.godot").read_text(encoding="utf-8")
