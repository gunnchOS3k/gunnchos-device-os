"""Fail-closed tests for current-pin harness authority + lifecycle matrix."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import current_pin_manifest as cpm
from gunnchos_device_os.device_lab import owner_four_game_artifacts as art


def _write_pin(tmp_path: Path, pins: list[dict], *, corrupt_hash: bool = False) -> dict:
    doc = {
        "schema": "gunnchos.device_lab.current_pin_manifest.v1",
        "convention": "test",
        "frozen_at_utc": "2026-09-09T00:00:00Z",
        "pins": pins,
        "windows_pilot0_accepted_main_pass": True,
        "windows_ceased_to_be_digital_blocker": True,
    }
    digest = cpm.compute_manifest_sha256(doc)
    doc["manifest_sha256"] = "deadbeef" if corrupt_hash else digest
    out = tmp_path / "artifacts/device_lab_current_pin"
    out.mkdir(parents=True)
    (out / "ACCEPTED_MAIN_PIN_MANIFEST.json").write_text(json.dumps(doc, indent=2) + "\n")
    (out / "ACCEPTED_MAIN_PIN_MANIFEST.sha256").write_text(doc["manifest_sha256"] + "\n")
    return doc


def test_load_pin_manifest_rejects_hash_mismatch(tmp_path: Path):
    _write_pin(
        tmp_path,
        [{"repository": "anime-aggressors", "sha": "a" * 40}],
        corrupt_hash=True,
    )
    with pytest.raises(cpm.PinManifestError, match="pin_manifest_sha256_mismatch"):
        cpm.load_pin_manifest(tmp_path)


def test_overlay_accepted_mains_uses_pin_over_hardcoded(tmp_path: Path, monkeypatch):
    pin_sha = "258cc0c45991ac9dded0c3d7813894d9fd7ca56d"
    pins = [
        {"repository": name, "sha": ("b" * 39) + str(i)}
        for i, name in enumerate(cpm.FOUR_GAME_REPOS)
    ]
    pins[0]["sha"] = pin_sha
    doc = _write_pin(tmp_path, pins)
    mains = {
        k: dict(v) for k, v in art.ACCEPTED_MAINS.items()
    }
    # Ensure hardcoded differs for anime
    assert mains["anime-aggressors"]["accepted_main_sha"] != pin_sha
    report = cpm.overlay_accepted_mains_from_pin(mains, doc)
    assert report["ok"] is True
    assert mains["anime-aggressors"]["accepted_main_sha"] == pin_sha
    assert any(x["repository"] == "anime-aggressors" for x in report["stale_hardcoded_rejected"])


def test_require_build_sha_matches_pin_fail_closed():
    with pytest.raises(cpm.PinManifestError, match="build_sha_mismatch"):
        cpm.require_build_sha_matches_pin(
            repository="beatlink-party",
            build_sha="0" * 40,
            pin_sha="1" * 40,
        )
    cpm.require_build_sha_matches_pin(
        repository="beatlink-party",
        build_sha="1" * 40,
        pin_sha="1" * 40,
    )


def _load_lifecycle_module():
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "run_current_pin_lifecycle_matrix.py"
    spec = importlib.util.spec_from_file_location("run_current_pin_lifecycle_matrix", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_lifecycle_matrix_fail_closed_without_authentic_evidence(tmp_path: Path, monkeypatch):
    life = _load_lifecycle_module()

    pins = [{"repository": name, "sha": ("c" * 39) + "0"} for name in cpm.LIFECYCLE_PRODUCTS]
    doc = _write_pin(tmp_path, pins)
    monkeypatch.setattr(life, "ROOT", tmp_path)
    monkeypatch.setattr(life, "OUT_DIR", tmp_path / "artifacts/device_lab_current_pin")
    monkeypatch.setattr(life, "MATRIX_PATH", tmp_path / "artifacts/device_lab_current_pin/LIFECYCLE_MATRIX.json")
    monkeypatch.setattr(
        life,
        "GATE_PATH",
        tmp_path / "artifacts/device_lab_current_pin/CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json",
    )
    matrix = life.derive_matrix(pin_doc=doc, execute_guest=False)
    assert matrix["CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS"] is False
    assert matrix["rows"]
    assert all(r.get("ok") is False for r in matrix["rows"])
    life.write_outputs(matrix)
    gate = json.loads(
        (tmp_path / "artifacts/device_lab_current_pin/CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json").read_text()
    )
    assert gate["CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS"] is False
    assert gate["verdict"] == "FAIL"


def test_lifecycle_rejects_host_resource_blocked_as_pass(tmp_path: Path, monkeypatch):
    life = _load_lifecycle_module()

    pins = [{"repository": name, "sha": ("d" * 39) + "1"} for name in cpm.LIFECYCLE_PRODUCTS]
    doc = _write_pin(tmp_path, pins)
    out = tmp_path / "artifacts/device_lab_current_pin"
    out.mkdir(parents=True, exist_ok=True)
    (out / "FOUR_GAME_CURRENT_PIN.json").write_text(
        json.dumps(
            {
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": True,
                "blocker": "HOST_RESOURCE_BLOCKED",
                "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
            }
        )
    )
    monkeypatch.setattr(life, "ROOT", tmp_path)
    matrix = life.derive_matrix(pin_doc=doc, execute_guest=False)
    anime_rows = [r for r in matrix["rows"] if r["product"] == "anime-aggressors"]
    assert anime_rows
    assert all(r["ok"] is False for r in anime_rows)
    assert matrix["CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS"] is False
