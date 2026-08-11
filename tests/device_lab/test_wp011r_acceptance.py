"""WP-011R remediations: honest gaps, production runtime, visual, DS-XL UX, ring, soak, score."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import (
    GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE,
    SILICON_EXACT_EMULATION,
)
from gunnchos_device_os.device_lab.ecosystem.games import launch_all_four_games, launch_web_game
from gunnchos_device_os.device_lab.ecosystem.production_runtime import (
    discover_game_artifact,
    run_all_four_production,
    run_production_game,
)
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import (
    compositor_ux_gate,
    high_fidelity_dual_gate,
)
from gunnchos_device_os.device_lab.virtualization.live_visual_proof import run_live_visual_proof
from gunnchos_device_os.device_lab.scenarios.ring_app_mutation import run_ring_app_mutation_proof


ROOT = Path(__file__).resolve().parents[2]
GAPS = ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json"


@pytest.fixture()
def lab_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    art = tmp_path / "device_lab"
    art.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GUNNCHDEVICE_LAB_ARTIFACT_ROOT", str(art))
    return art


def test_master_and_silicon_tokens_remain_false():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False
    gaps = json.loads(GAPS.read_text(encoding="utf-8"))
    assert gaps["claim_firewall"]["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert gaps["claim_firewall"]["SILICON_EXACT_EMULATION"] is False
    tokens = gaps["pass_tokens"]
    # Initial audit marks these false until earned
    assert tokens["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] is False
    assert tokens["LIVE_GUNNCHOS_VISUAL_PASS"] is False
    assert tokens["DSXL_DUAL_COMPOSITOR_UX_PASS"] is False
    # Hybrid Lab surfaces ≠ Cycle 3A guest-OS Ring PASS
    assert tokens["RING_TO_REAL_APP_STATE_MUTATION_PASS"] is False
    evid = ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json"
    if evid.is_file():
        ring = json.loads(evid.read_text())
        assert ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS") is False


def test_http_server_labeled_process_proof_only(lab_artifacts: Path):
    r = launch_web_game(
        game_id="anime-aggressors",
        repo_root=ROOT,
        work=lab_artifacts / "http_only",
        keep=False,
    )
    assert r.get("PROCESS_PROOF_ONLY") is True
    assert r.get("NOT_PRODUCTION_RUNTIME") is True
    assert r.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") is False
    four = launch_all_four_games(repo_root=ROOT, work=lab_artifacts / "four_http")
    assert four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") is False
    assert four.get("NOT_PRODUCTION_RUNTIME") is True


def test_production_runtime_does_not_earn_pass_via_http_alone(lab_artifacts: Path):
    """PASS token only when real runtime proofs earned — never via http.server alone."""
    art = discover_game_artifact(game_id="anime-aggressors", repo_root=ROOT)
    assert art.get("ok") is True
    # Run production path; on hosts without Chromium this must stay false (not skip-as-pass)
    out = run_all_four_production(repo_root=ROOT, work=lab_artifacts / "prod_games")
    assert "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS" in out
    if out["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] is True:
        for gid, g in out["games"].items():
            assert g.get("FOUR_GAME_REAL_RUNTIME_EARNED") is True, gid
            assert g.get("PROCESS_PROOF_ONLY") is not True
            assert g.get("NOT_PRODUCTION_RUNTIME") is not True
    else:
        # Honest failure path: at least one game reports why
        assert out.get("ok") is False
        assert any(
            g.get("PROCESS_PROOF_ONLY") or g.get("reason") or g.get("partial")
            for g in out["games"].values()
        )


def test_guest_dual_drm_insufficient_for_dsxl_ux():
    outputs = [
        {"id": "a", "connected": True, "source": "qemu_virtio_gpu", "class": "guest"},
        {"id": "b", "connected": True, "source": "qemu_virtio_gpu", "class": "guest"},
    ]
    dual = high_fidelity_dual_gate(outputs, claim_guest_dual=True)
    assert dual.get("GUEST_DUAL_OUTPUT_PASS") is True
    assert dual.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is False
    ux = compositor_ux_gate(outputs=outputs, windows=[], focus_moves=[], disconnect_reconnect={})
    assert ux.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is False
    assert "two_compositor_surfaces" in ux.get("missing") or "window_placement_on_both_outputs" in ux.get(
        "missing"
    )


def test_dsxl_compositor_ux_gate_earns_with_full_evidence():
    outputs = [
        {"id": "a", "connected": True, "source": "WaylandSession", "compositor_surface": True},
        {"id": "b", "connected": True, "source": "WaylandSession", "compositor_surface": True},
    ]
    windows = [
        {"app_id": "creator_ide", "output_id": "a"},
        {"app_id": "terminal_docs", "output_id": "b"},
    ]
    focus_moves = [
        {"ok": True, "output_id": "a"},
        {"ok": True, "output_id": "b"},
    ]
    ux = compositor_ux_gate(
        outputs=outputs,
        windows=windows,
        focus_moves=focus_moves,
        disconnect_reconnect={
            "disconnect_ok": True,
            "reconnect_ok": True,
            "layout_restored": True,
        },
        layout_restore={"ok": True, "layout_restored": True},
    )
    assert ux.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is True


def test_live_visual_pass_false_without_guest_captures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Point artifacts into tmp by monkeypatching visual dir via repo copy? use ROOT but
    # run without monitor/agent — must not earn PASS and must not write synthetic PNGs.
    # Use a temp repo-root-like tree
    fake_root = tmp_path / "repo"
    (fake_root / "artifacts" / "wp011r").mkdir(parents=True)
    result = run_live_visual_proof(repo_root=fake_root, require_guest=True)
    assert result.get("LIVE_GUNNCHOS_VISUAL_PASS") is False
    assert result.get("synthetic_screenshots") is False
    evid = fake_root / "artifacts/wp011r/visual/LIVE_VISUAL_EVIDENCE.json"
    assert evid.is_file()
    # No synthetic png fabricated
    assert not list((fake_root / "artifacts/wp011r/visual").glob("*.png"))


def test_ring_app_mutation_evidence(lab_artifacts: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Redirect wp011r ring evidence under tmp by using repo root but evidence writes to artifacts/wp011r
    # Use monkeypatch on Path home? Instead run and check token honesty.
    result = run_ring_app_mutation_proof(repo_root=ROOT)
    assert "RING_TO_REAL_APP_STATE_MUTATION_PASS" in result
    assert result.get("pipeline_ok") is True
    # Mutations must be real before/after — not observe-only
    for t in ("libreoffice", "browser", "games"):
        m = result["mutations"][t]
        assert m.get("direct_file_write") is False
        if result["RING_TO_REAL_APP_STATE_MUTATION_PASS"]:
            assert m.get("mutated") is True
            assert m.get("before") != m.get("after")
    evid = ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json"
    assert evid.is_file()
    # input_observe alone must not be sufficient if before==after
    assert all(m.get("observe_only_rejected") is False or not m.get("mutated") for m in result["mutations"].values())


def test_eco010_soak_script_dry_check_partial(lab_artifacts: Path):
    import subprocess
    import sys

    out = lab_artifacts / "ECO010_SOAK.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_eco010_full_soak.py"),
            "--dry-check",
            "--duration-sec",
            "1800",
            "--poll-sec",
            "2",
            "--min-injects",
            "5",
            "--out",
            str(out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["status"] == "PARTIAL"
    assert data["ok"] is False
    assert data["simultaneous_soak_complete"] is False
    assert data["duration_shortened_to_pass"] is False
    assert data["dry_check"] is True
    assert data["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    # Requested duration remains 1800 even when dry-check bounds the run
    assert data["duration_sec_requested"] == 1800


def test_independent_score_no_hardcoded_tens():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/device_lab_score_independent.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    out = ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json"
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["hardcoded_tens_forbidden"] is True
    assert data["any_grade_is_10"] is False
    assert data["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    for name, g in data["baseline_12_grades"].items():
        assert int(g["grade"]) < 10, name
        assert g.get("hardcoded") is False


def test_completion_register_wp011r_not_master_complete():
    text = (ROOT / "gunnchos_device_os/device_lab/device_lab_v1/DEVICE_LAB_COMPLETION_REGISTER.yaml").read_text(
        encoding="utf-8"
    )
    assert "WP-011R" in text or "wp-011r" in text.lower() or "IMPLEMENTATION_PARTIAL_WAVE_011R" in text
    assert "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE: false" in text
    assert "SILICON_EXACT_EMULATION: false" in text
