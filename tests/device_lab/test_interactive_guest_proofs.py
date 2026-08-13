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
