"""Tests for silent destructive uncertain gestures guard (RING-RELIAB-016)."""
from __future__ import annotations

from gunnchos_device_os.silent_destructive_uncertain_gestures import (
    TOKEN_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_PASS,
    SilentDestructiveUncertainGesturesGuard,
    run_silent_destructive_uncertain_gestures,
)


def test_silent_destructive_uncertain_gestures_suite_pass():
    report = run_silent_destructive_uncertain_gestures()
    assert report["ok"] is True
    assert report["token"] == TOKEN_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_PASS
    assert report["requirement_id"] == "RING-RELIAB-016"
    assert report["physical_ring_claimed"] is False
    assert all(not s["silent_accept"] for s in report["scenarios"])


def test_silent_destructive_uncertain_gestures_blocks_low_confidence():
    guard = SilentDestructiveUncertainGesturesGuard()
    decision = guard.evaluate(
        event_type="destructive_confirm",
        confidence=0.4,
        action="delete_files",
        explicit_confirm=False,
    )
    assert decision.allowed is False
    assert decision.silent_accept is False
    assert "uncertain" in decision.reason


def test_silent_destructive_uncertain_gestures_requires_explicit_confirm():
    guard = SilentDestructiveUncertainGesturesGuard()
    denied = guard.evaluate(
        event_type="destructive_confirm",
        confidence=0.99,
        action="approve_payments",
        explicit_confirm=False,
    )
    assert denied.allowed is False
    allowed = guard.evaluate(
        event_type="destructive_confirm",
        confidence=0.99,
        action="approve_payments",
        explicit_confirm=True,
    )
    assert allowed.allowed is True
    assert allowed.silent_accept is False
