"""Unit tests for GUNNCHDEVICE_BASE_IMAGE_PIPELINE (no multi-GB images)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import base_image_pipeline as bip


def test_stages_are_ordered_and_complete():
    assert "seal" in bip.STAGES
    assert "cow_overlays" in bip.STAGES
    assert bip.STAGES.index("validate_sentinel") < bip.STAGES.index("seal")
    assert bip.STAGES.index("seal") < bip.STAGES.index("cow_overlays")


def test_mark_stage_and_checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(bip, "interactive_guest_root", lambda root: tmp_path / "ig")
    (tmp_path / "ig").mkdir()
    cp = bip.mark_stage(tmp_path, "canonical_engineering_image")
    assert "canonical_engineering_image" in cp["stages_completed"]
    loaded = bip.load_checkpoint(tmp_path)
    assert loaded["stage"] == "canonical_engineering_image"


def test_safe_halt_and_resume_blocked_without_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(bip, "interactive_guest_root", lambda root: tmp_path / "ig")
    (tmp_path / "ig").mkdir()
    halt = bip.safe_halt(tmp_path, reason="test_leave")
    assert halt["ok"] is True
    assert (tmp_path / "ig" / "pipeline" / "SAFE_HALT.json").exists()
    resume = bip.safe_resume(tmp_path)
    assert resume["decision"] == "BLOCKED_SAFE_GUEST_RESUME"
    assert resume["blocked"] is True


def test_discard_overlay_refuses_missing_and_records_regenerable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(bip, "interactive_guest_root", lambda root: tmp_path / "ig")
    (tmp_path / "ig" / "pipeline" / "overlays").mkdir(parents=True)
    out = bip.discard_overlay(tmp_path, persona="G11")
    assert out["ok"] is True
    assert out["discarded"] is False


def test_resolve_boot_disk_honors_explicit_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(bip, "interactive_guest_root", lambda root: tmp_path / "ig")
    art = tmp_path / "ig" / "artifacts"
    art.mkdir(parents=True)
    base = art / "interactive-root-aarch64.qcow2"
    base.write_bytes(b"fake")
    ov = tmp_path / "session.qcow2"
    ov.write_bytes(b"ov")
    monkeypatch.setenv(bip.OVERLAY_ENV, str(ov))
    resolved = bip.resolve_boot_disk(tmp_path)
    assert resolved["ok"] is True
    assert resolved["kind"] == "explicit_overlay"
    assert resolved["disk"] == str(ov)
