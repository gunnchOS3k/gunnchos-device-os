"""WP-003 digital remediation paths — supporting tests (not independent verification)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_in_tree_beatlink_and_anime_launch(tmp_path: Path):
    from gunnchos_device_os.phase_xii.apps import games as games_mod

    beat = games_mod.launch_beatlink(ROOT, tmp_path / "beat")
    assert beat.get("fixture_json_used") is False
    # In-tree web package must resolve without inventing sibling repos
    assert games_mod.resolve_in_tree_web(ROOT, "beatlink-party") is not None
    assert games_mod.resolve_in_tree_web(ROOT, "anime-aggressors") is not None
    # Pedestrian remains fail-closed when sibling Godot missing (no invented alias)
    ped_web = games_mod.resolve_in_tree_web(ROOT, "pedestrian-pursuit")
    assert ped_web is None
    ped = games_mod.play_short_session(ROOT, "pedestrian-pursuit")
    if ped.get("ok") is False:
        assert ped.get("defect") == "XR-DEFECT-GAME-REPO" or ped.get("error", "").startswith("game_repo_missing")
        assert ped.get("fixture_json_used") is False


def test_offline_office_lms_reconnect_d6(tmp_path: Path):
    from gunnchos_device_os.golden_journeys.digital_paths import offline_office_lms_reconnect

    out = offline_office_lms_reconnect(ROOT, tmp_path / "g02")
    assert out["ok"] is True
    assert out["conflict_surfaced"] is True
    assert out["silent_overwrite"] is False
    assert out["lms_receipt"]
    assert out["cross_app"] == ["office", "offline_sync", "lms"]
    assert out["claim_boundary"]
    assert "independent verification" in out["claim_boundary"].lower() or "Not independent" in out["claim_boundary"] or "not independent" in out["claim_boundary"].lower()


def test_fleet_mdm_wipe_continuity_denial_d6(tmp_path: Path):
    from gunnchos_device_os.golden_journeys.digital_paths import fleet_mdm_wipe_continuity_denial

    out = fleet_mdm_wipe_continuity_denial(ROOT, tmp_path / "g10")
    assert out["ok"] is True
    assert out["private_gone"] is True
    assert out["files_denied"] is True
    assert out["handoff_denied"] is True
    assert out["physical_fleet"] is False
    assert out["wipe"]["destructive_physical"] is False


def test_education_mdm_wipe_marks_device():
    from gunnchos_device_os.phase_xiv.mdm import EducationMdm

    mdm = EducationMdm(root=ROOT / "artifacts" / "tmp_mdm_wipe_test")
    fleet = mdm.e2e_ten_device_fleet(ROOT)
    assert fleet["ok"] is True
    wipe = mdm.wipe_device("edu-04", reason="test")
    assert wipe["ok"] is True
    assert mdm.devices["edu-04"].wiped is True
    assert mdm.devices["edu-04"].enrolled is False
