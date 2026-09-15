"""Focused WAIKE Device Lab harness tests — process-only / fixture rejection."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.owner_waike_artifacts import (
    ACCEPTED_WAIKE_LP_SHA,
    ACCEPTED_WAIKE_OPS_SHA,
    GATE_D_LINUX_SHA256,
    locate_staged_linux_binary,
    resolve_waike_lp_checkout,
    stage_owner_waike_bundle,
    write_runtime_provenance,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def stub_pins(monkeypatch: pytest.MonkeyPatch) -> None:
    """CI has no sibling WAIKE checkouts; stub pin verification for unit tests."""

    def _pins(_repo_root: Path) -> dict:
        return {
            "ok": True,
            "learning_platform": {
                "path": "(stub)",
                "head": ACCEPTED_WAIKE_LP_SHA,
                "origin_main": ACCEPTED_WAIKE_LP_SHA,
                "expected": ACCEPTED_WAIKE_LP_SHA,
                "match": True,
                "dirty": False,
            },
            "research_ops": {
                "path": "(stub)",
                "head": ACCEPTED_WAIKE_OPS_SHA,
                "origin_main": ACCEPTED_WAIKE_OPS_SHA,
                "expected": ACCEPTED_WAIKE_OPS_SHA,
                "match": True,
                "dirty": False,
            },
            "note": "unit-test stub; live re-earn verifies real checkouts",
        }

    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.owner_waike_artifacts.verify_pin_checkouts",
        _pins,
    )


def test_provenance_rejects_seed_and_fixture_as_sor(tmp_path: Path, stub_pins: None):
    doc = write_runtime_provenance(ROOT, tmp_path / "out")
    assert doc["system_of_record"] == "platform_tauri_learning_os"
    rejected = " ".join(doc["rejected_surrogates"])
    assert "seed" in rejected.lower() or "waike_learning" in rejected
    assert "fixtures/learning_os" in rejected
    assert "static HTML" in rejected or "waike_guest_pack" in rejected
    assert doc["accepted_main"]["sha"] == ACCEPTED_WAIKE_LP_SHA
    assert doc["pin_verification"]["ok"] is True


def test_staged_linux_binary_is_gate_d_elf_not_fixture():
    binary = locate_staged_linux_binary(ROOT)
    if not binary.get("ok"):
        pytest.skip("Gate D linux artifact not staged under artifacts/device_lab_current_pin/waike")
    assert binary["fixture_rejected"] is True
    assert "fixtures/learning_os" not in binary["path"]
    assert binary["sha256"] == GATE_D_LINUX_SHA256
    assert binary["arch"] in {"x86_64", "aarch64"}


def test_owner_bundle_stage_writes_install_layout(tmp_path: Path):
    binary = locate_staged_linux_binary(ROOT)
    if not binary.get("ok"):
        pytest.skip("Gate D linux artifact not staged")
    staging = tmp_path / "stage"
    manifest = stage_owner_waike_bundle(ROOT, staging)
    assert manifest["ok"] is True
    exe = staging / "bin" / "waike-learning-os"
    assert exe.is_file()
    assert (staging / "bin" / "INSTALLED.json").is_file()
    meta = json.loads((staging / "bin" / "INSTALLED.json").read_text())
    assert meta["bundle_id"] == "com.gunnchos.waike.learning"
    assert meta["fixture"] is False
    assert meta["platform_sha"] == ACCEPTED_WAIKE_LP_SHA


def test_process_alive_alone_never_pass_token():
    """Contract: transport/process-alive alone must not flip WAIKE PASS."""
    from gunnchos_device_os.device_lab import owner_waike_guest as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "learner_journey_complete = False" in src or "learner_journey_complete=" in src
    assert "headless_launch_ack_only" in src or "learner_journey_depth_not_earned" in src


def test_missing_lp_checkout_is_explicit_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("WAIKE_LP_ROOT", raising=False)
    monkeypatch.delenv("WAIKE_ROOT", raising=False)
    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.owner_waike_artifacts._repos_root",
        lambda _root: tmp_path / "no-repos",
    )
    with pytest.raises(FileNotFoundError, match="waike_learning_platform_checkout_missing"):
        resolve_waike_lp_checkout(tmp_path / "device-os")
