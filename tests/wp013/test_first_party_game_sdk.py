"""FIRST_PARTY_GAME_SDK_ADOPTION — Godot export-pack pipeline spot-check."""
from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.sdk.first_party_game_adoption import (
    run_first_party_game_sdk_adoption,
)
from gunnchos_device_os.release_engineering.sdk.godot_runtime import resolve_godot_bin

ROOT = Path(__file__).resolve().parents[2]


def _godot_available() -> bool:
    try:
        resolve_godot_bin()
        return True
    except FileNotFoundError:
        return False


def _pedestrian_repo_available() -> bool:
    sibling = ROOT.parent / "pedestrian-pursuit"
    return sibling.exists() and (sibling / "project.godot").exists()


@pytest.mark.skipif(
    not (_godot_available() and _pedestrian_repo_available()),
    reason="Godot 4.5 and/or sibling pedestrian-pursuit checkout missing",
)
def test_first_party_game_sdk_adoption_real_godot_pipeline():
    result = run_first_party_game_sdk_adoption(ROOT)
    assert result.get("python_manifest_wrapper_rejected") is True
    assert result.get("PRODUCTION_RELEASE_CLAIMED") is False
    assert result.get("FIRST_PARTY_GAME_SDK_ADOPTION_PASS") is True, result.get("error") or result.get("steps")
    assert result["steps"]["godot_export"]["ok"] is True
    assert result["steps"]["godot_export"]["export_mode"] == "export-pack"
    assert result["steps"]["launch_runtime"]["harness_pass_marker"] is True
    assert result["steps"]["game_state"]["save_exists"] is True
    assert result["steps"]["game_state"]["input_events"] == 2
    assert result["steps"]["update"]["ok"] is True
    assert result["steps"]["incompatible_rejection"]["ok"] is True
    assert result["steps"]["uninstall"]["ok"] is True
