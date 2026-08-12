import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_master_complete_false():
    gaps = json.loads((ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json").read_text())
    firewall = gaps.get("claim_firewall") or gaps.get("master_token") or {}
    tokens = gaps.get("pass_tokens") or gaps.get("tokens") or {}
    assert firewall["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    # Consistency: gap register tokens must match evidence files when present
    games_guest = ROOT / "artifacts/wp011r/games/four_games_in_guest.json"
    games = ROOT / "artifacts/wp011r/games/four_games_production.json"
    if games_guest.is_file():
        assert tokens["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] == bool(
            json.loads(games_guest.read_text()).get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        )
    elif games.is_file():
        assert tokens["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] == bool(
            json.loads(games.read_text()).get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        )
    visual = ROOT / "artifacts/wp011r/visual/LIVE_VISUAL_EVIDENCE.json"
    if visual.is_file():
        assert tokens["LIVE_GUNNCHOS_VISUAL_PASS"] == bool(
            json.loads(visual.read_text()).get("LIVE_GUNNCHOS_VISUAL_PASS")
        )
    else:
        assert tokens["LIVE_GUNNCHOS_VISUAL_PASS"] is False
    dsxl = ROOT / "artifacts/wp011r/dsxl/DSXL_COMPOSITOR_UX_EVIDENCE.json"
    if dsxl.is_file():
        assert tokens["DSXL_DUAL_COMPOSITOR_UX_PASS"] == bool(
            json.loads(dsxl.read_text()).get("DSXL_DUAL_COMPOSITOR_UX_PASS")
        )
    else:
        assert tokens["DSXL_DUAL_COMPOSITOR_UX_PASS"] is False
    evid = ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json"
    if evid.is_file():
        data = json.loads(evid.read_text())
        assert tokens["RING_TO_REAL_APP_STATE_MUTATION_PASS"] == bool(
            data.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        )
        if data.get("RING_TO_REAL_APP_STATE_MUTATION_PASS") is True:
            assert data.get("guest_os_input_present") is True
        if data.get("RING_HYBRID_LAB_SURFACE_MUTATION_PASS") is True:
            assert data.get("RING_TO_REAL_APP_STATE_MUTATION_PASS") is False
            # Real guest OS input may have been observed over virtio-serial
            # while the app-state mutation still landed on Lab-surface
            # simulacra (not real in-guest apps) — that nuance must be
            # explicitly labeled via RING_GUEST_OBSERVE_WITH_LAB_MUTATION,
            # never silently upgraded into the real state-mutation PASS.
            if data.get("guest_os_input_present") is True:
                assert data.get("RING_GUEST_OBSERVE_WITH_LAB_MUTATION") is True
            else:
                assert data.get("RING_GUEST_OBSERVE_WITH_LAB_MUTATION") is not True


def test_independent_score_exists():
    p = ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json"
    assert p.is_file()
    data = json.loads(p.read_text())
    assert data["hardcoded_tens_forbidden"] is True
    observed = data.get("tokens_observed") or {}
    five = all(
        bool(observed.get(k))
        for k in (
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "ECO010_SOAK_PASS",
        )
    )
    assert data["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is five
    # No hardcoded perfect 10s in numeric categories
    cats = data.get("baseline_12_grades") or data.get("categories") or {}
    for name, g in cats.items():
        if isinstance(g, dict) and "grade" in g:
            assert int(g["grade"]) < 10, name
        elif isinstance(g, (int, float)):
            assert float(g) < 10, name


def test_development_guest_labeled():
    from gunnchos_device_os.device_lab.image_builder import DEVICE_LAB_DEVELOPMENT_GUEST, SHIPPING_IMAGE

    assert DEVICE_LAB_DEVELOPMENT_GUEST is True
    assert SHIPPING_IMAGE is False
