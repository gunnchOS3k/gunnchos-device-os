"""Unit tests for honest FOUR_GAME earn criteria (no guest required)."""
from __future__ import annotations

from gunnchos_device_os.device_lab.four_game_honest import (
    anime_cfg_mutated,
    anime_default_career_save,
    archive_save_mutated_from_default,
    beatlink_native_keys_present,
    five_gate_and,
    honest_sha_entry,
    launched_pid_alive_non_zombie,
    master_complete_forbidden,
    parse_ps_pid_stat_args,
    pedestrian_cfg_mutated,
    pid_stat_is_alive_non_zombie,
    substring_alive_godot_forbidden,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import verify_accepted_shas


def test_zombie_godot_is_not_alive():
    stdout = "1891 Z    [godot] <defunct>\n"
    rows = parse_ps_pid_stat_args(stdout)
    assert rows[0]["zombie"] is True
    assert launched_pid_alive_non_zombie(1891, rows) is False
    assert substring_alive_godot_forbidden(stdout) is True
    assert pid_stat_is_alive_non_zombie("Z", "[godot] <defunct>") is False


def test_live_godot_pid_is_alive():
    stdout = "1556 Ssl  /opt/gunnchos/bin/godot --path /root/pedestrian-pursuit\n"
    rows = parse_ps_pid_stat_args(stdout)
    assert launched_pid_alive_non_zombie(1556, rows) is True
    assert pid_stat_is_alive_non_zombie("Ssl", stdout) is True


def test_ps_header_skipped():
    stdout = "PID STAT COMMAND\n687 S /root/owner-games/beatlink-node/node dist/index.js\n"
    rows = parse_ps_pid_stat_args(stdout)
    assert len(rows) == 1
    assert rows[0]["pid"] == 687


def test_pedestrian_default_presence_is_not_mutation():
    after = "[meta]\nsave_version=2\n[career]\nxp=0\ntutorial_completed=false\nfirst_run_complete=false\n"
    r = pedestrian_cfg_mutated("", after)
    assert r["ok"] is False
    assert r["first_run_create_only"] is True


def test_pedestrian_seeded_v1_to_v2_is_mutation():
    before = "[meta]\nsave_version=1\n[career]\nxp=11\n"
    after = "[meta]\nsave_version=2\n[career]\nxp=11\nunlocked={ \"mode:challenges\": true }\n"
    r = pedestrian_cfg_mutated(before, after)
    assert r["ok"] is True
    assert r["via"] == "seeded_v1_to_v2"


def test_anime_harness_first_run_create_not_mutation():
    after = "[tutorial]\ncompleted=true\nskipped=false\n"
    r = anime_cfg_mutated("", after)
    assert r["ok"] is False


def test_anime_seeded_skip_is_mutation():
    before = "[tutorial]\ncompleted=false\nskipped=false\n"
    after = "[tutorial]\ncompleted=false\nskipped=true\n"
    r = anime_cfg_mutated(before, after)
    assert r["ok"] is True


def test_anime_hid_qemu_key_map_covers_ui_accept_and_skip():
    from gunnchos_device_os.device_lab.owner_four_game_guest import _QEMU_KEY

    assert _QEMU_KEY["ret"] == "ret"
    assert _QEMU_KEY["spc"] == "spc"
    assert _QEMU_KEY["tab"] == "tab"
    assert _QEMU_KEY["down"] == "down"


def test_anime_default_career_save_is_not_mutation():
    default = "[meta]\nsave_version=2\n[career]\nwins=0\nlosses=0\nmatches=0\n"
    assert anime_default_career_save(default) is True
    played = "[meta]\nsave_version=2\n[career]\nwins=1\nlosses=0\nmatches=1\n"
    assert anime_default_career_save(played) is False


def test_anime_aa_save_after_hid_is_mutation_boot_create_is_not():
    from gunnchos_device_os.device_lab.owner_four_game_guest import (
        _anime_mutation_from_snapshot,
    )

    first = "[tutorial]\ncompleted=false\nskipped=false"
    default = "[meta]\nsave_version=2\n[career]\nwins=0\nlosses=0\nmatches=0\n"
    played = "[meta]\nsave_version=2\n[career]\nwins=1\nlosses=0\nmatches=1\n"
    boot = _anime_mutation_from_snapshot(
        first, {"first": first, "save": default}, save_before_hid=default
    )
    assert boot["ok"] is False
    default_create = _anime_mutation_from_snapshot(
        first, {"first": first, "save": default}, save_before_hid=""
    )
    assert default_create["ok"] is False
    hid = _anime_mutation_from_snapshot(
        first, {"first": first, "save": played}, save_before_hid=""
    )
    assert hid["ok"] is True
    assert hid["via"] == "aa_save_cfg_after_input"


def test_archive_default_museum_spawn_is_not_mutation():
    raw = {
        "version": 4,
        "player": {"x": 400, "y": 300, "currentRegion": "museum", "visitedRegions": ["museum"]},
    }
    r = archive_save_mutated_from_default(raw)
    assert r["ok"] is False
    assert r["default_spawn"] is True


def test_archive_position_change_is_mutation():
    raw = {
        "version": 4,
        "player": {"x": 480, "y": 300, "currentRegion": "museum", "visitedRegions": ["museum"]},
    }
    r = archive_save_mutated_from_default(raw)
    assert r["ok"] is True


def test_beatlink_room_api_is_not_save():
    r = beatlink_native_keys_present({"beatlink_host": None, "beatlink_player": None}, "")
    assert r["ok"] is False
    assert r["room_api_not_accepted_as_save"] is True


def test_beatlink_native_host_key_is_save():
    r = beatlink_native_keys_present(
        {"beatlink_host": '{"roomCode":"YHSN7","hostToken":"abc"}'}, ""
    )
    assert r["ok"] is True
    assert "beatlink_host" in r["keys_found"]


def test_sha_pin_does_not_report_drifted_sibling_as_observed():
    entry = honest_sha_entry(
        accepted_main_sha="64fcf3a73d9a0db4e13523f762cf3fd651d7ddaa",
        sibling_head="858e8e8fa7e103989e519180fb8da5444ca17594",
        meta={"accepted_main_sha": "64fcf3a73d9a0db4e13523f762cf3fd651d7ddaa"},
        owner_repo="gunnchOS3k/archive-of-life-artifact-world",
        lab_id="earth-species",
        sibling_path="/tmp/archive",
    )
    assert entry["ok"] is True
    assert entry["source"] == "owner_artifact_pin"
    assert entry["observed_sha"] == "64fcf3a73d9a0db4e13523f762cf3fd651d7ddaa"
    assert entry["sibling_head"] == "858e8e8fa7e103989e519180fb8da5444ca17594"
    assert entry["successor_draft_not_accepted_main"] is True


def test_complete_stays_false_on_interactive_guest():
    assert master_complete_forbidden() is False
    assert five_gate_and(four=True, live=True, dsxl=True, ring=True, eco010=True) is True
    assert five_gate_and(four=False, live=True, dsxl=True, ring=True, eco010=True) is False


def test_guest_agent_overlays_are_honest_and_patch_live_project():
    from gunnchos_device_os.device_lab.guest_agent_overlays import (
        ANIME_OVERLAY_GD,
        ARCHIVE_OVERLAY_JS_SOURCE,
        overlay_is_honest,
        patch_index_html,
        patch_project_godot,
    )

    anime = overlay_is_honest(ANIME_OVERLAY_GD, kind="anime")
    assert anime["parse_input_event"] is True
    assert anime["waits_ready_to_start"] is True
    assert anime["skip_tutorial_ui"] is True
    assert "Start Battle" in ANIME_OVERLAY_GD
    assert "Mode Select" not in ANIME_OVERLAY_GD or "Tutorial" in ANIME_OVERLAY_GD
    assert anime["no_direct_skip_tutorial"] is True
    assert anime["no_complete_tutorial"] is True
    assert anime["no_tree_quit"] is True
    archive = overlay_is_honest(ARCHIVE_OVERLAY_JS_SOURCE, kind="archive")
    assert archive["real_new_game_click"] is True
    assert archive["keyboard_events"] is True
    assert archive["no_localstorage_write"] is True
    assert archive["no_aol_accept"] is True
    patched = patch_project_godot("[autoload]\nGameState=\"*res://scripts/core/GameState.gd\"\n\n[display]\n")
    assert 'DeviceLabInputOverlay="*res://device_lab_input_overlay.gd"' in patched
    html = patch_index_html("<html><body></body></html>")
    assert "lab_input_overlay.js" in html


def test_verify_accepted_shas_uses_honest_entry(tmp_path, monkeypatch):
    from gunnchos_device_os.device_lab import owner_four_game_artifacts as art

    monkeypatch.setattr(art, "_discover_sibling", lambda _root, name: tmp_path / name)
    monkeypatch.setattr(
        art,
        "_git_sha",
        lambda _p: {
            "anime-aggressors": "16df36d0025a6d124817a1800de65abef689d51f",
            "pedestrian-pursuit": "3f4dafd0e455a0cf22523bab48a094a542d3141d",
            "archive-of-life-artifact-world": "858e8e8fa7e103989e519180fb8da5444ca17594",
            "beatlink-party": "31a56a981ce5fcb8bea19e90eae280264e7a2a6f",
        }[_p.name],
    )

    def fake_meta(_root, key):
        sha = art.ACCEPTED_MAINS[key]["accepted_main_sha"]
        return {"accepted_main_sha": sha}

    monkeypatch.setattr(art, "load_owner_artifact_meta", fake_meta)
    out = verify_accepted_shas(tmp_path)
    assert out["ok"] is True
    archive = out["games"]["archive-of-life-artifact-world"]
    assert archive["observed_sha"] == "64fcf3a73d9a0db4e13523f762cf3fd651d7ddaa"
    assert archive["sibling_head"] == "858e8e8fa7e103989e519180fb8da5444ca17594"
    beat = out["games"]["beatlink-party"]
    assert beat["observed_sha"] == "4b3970c9bc327ba7a1cec43ff7a905d91cd3070b"
    assert beat["successor_draft_not_accepted_main"] is True
