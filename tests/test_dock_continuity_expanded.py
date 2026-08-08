"""Expanded dock continuity suite — apps/saves/identity/network/AI-privacy/input/display/audio."""
from __future__ import annotations

from gunnchos_device_os.dock.continuity import DockContinuityEngine
from gunnchos_device_os.display_manager import DisplayManager, DeviceSurface
from gunnchos_device_os.identity import sha256_json
from gunnchos_device_os.permissions_manager import Permission, PermissionsManager


def test_continuity_preserves_apps_saves_identity_across_undock():
    eng = DockContinuityEngine()
    eng.apps = ["launcher", "notes", "media"]
    eng.save_blob = {"slot": 3, "progress": 88, "chapter": "mid"}
    eng.identity = {"user": "student-42", "auth": "device-bound", "session_role": "student"}
    checksum = sha256_json(eng.save_blob)
    eng.attach("dock-expand-1", external_display=True, ethernet=True, audio_dock=True)
    eng.safe_undock()
    assert eng.apps == ["launcher", "notes", "media"]
    assert eng.identity["user"] == "student-42"
    assert sha256_json(eng.save_blob) == checksum
    assert eng.network_route == "wlan"
    assert eng.audio_route == "internal"
    assert eng.display_state == {"internal": True, "external": False}
    assert eng.input_map["primary"] == "touch"


def test_continuity_network_and_audio_routes_on_attach():
    eng = DockContinuityEngine()
    eng.attach("dock-net", ethernet=True, audio_dock=True)
    assert eng.network_route == "ethernet-via-dock"
    assert eng.audio_route == "dock-audio"
    obs = eng.observe(phase="check")
    assert obs["network"] == "ethernet-via-dock"
    assert obs["audio"] == "dock-audio"
    assert obs["display"]["external"] is True
    assert obs["inputs"]["primary"] == "keyboard"


def test_continuity_ai_privacy_survives_detach_and_restore():
    eng = DockContinuityEngine()
    eng.set_ai_privacy(local_only=True, cloud_export=False, retain_prompts=False)
    eng.attach("dock-ai")
    eng.set_ai_privacy(cloud_export=False, policy="dock_session_locked")
    snap = eng.snapshot_session()
    assert snap["ai_privacy"]["local_only"] is True
    assert snap["ai_privacy"]["cloud_export"] is False
    eng.ai_privacy["cloud_export"] = True  # corrupt in-memory after snapshot
    # detach uses last_snapshot (pre-corruption), unlike safe_undock which re-snapshots first
    eng.detach(safe=True)
    assert eng.ai_privacy["cloud_export"] is False
    eng.ai_privacy = {"local_only": False, "cloud_export": True}
    eng.restore_from_snapshot(snap)
    assert eng.ai_privacy["local_only"] is True
    assert eng.ai_privacy["cloud_export"] is False


def test_continuity_input_display_profiles_with_display_manager():
    eng = DockContinuityEngine()
    dm = DisplayManager()
    dm.switch_for_device_class("handheld_hybrid")
    eng.attach("dock-dm", external_display=True)
    dm.set_docked(True)
    assert dm.active_surface == DeviceSurface.DOCK
    assert eng.layout_profile in ("docked-extend", "docked-mirror")
    assert eng.input_map["secondary"] == "mouse"
    eng.safe_undock()
    dm.set_docked(False)
    assert dm.active_surface == DeviceSurface.HANDHELD_HYBRID
    assert eng.layout_profile == "handheld"


def test_continuity_ai_privacy_gated_by_permissions():
    eng = DockContinuityEngine()
    pm = PermissionsManager(role="ai_local")
    eng.set_ai_privacy(local_only=True, cloud_export=False)
    denied = pm.request("gunnchai", Permission.AI_CLOUD_EXPORT, explicit_user_grant=True)
    assert denied["decision"] == "deny"
    # Continuity must not silently enable cloud export
    eng.attach("dock-priv")
    assert eng.ai_privacy["cloud_export"] is False
    eng.safe_undock()
    assert eng.ai_privacy["local_only"] is True


def test_interruption_recovery_restores_identity_apps_saves_ai_privacy():
    eng = DockContinuityEngine()
    eng.apps = ["launcher", "campus"]
    eng.identity = {"user": "u1", "auth": "pin"}
    eng.save_blob = {"slot": 1, "progress": 5}
    eng.set_ai_privacy(retain_prompts=False)
    eng.attach("dock-int")
    eng.snapshot_session()
    eng.apps = ["corrupt"]
    eng.identity = {"user": "evil"}
    eng.save_blob = {"slot": 9, "progress": 0}
    eng.ai_privacy = {"local_only": False, "cloud_export": True}
    ev = eng.recover_interruption()
    assert ev["ok"] is True
    assert eng.apps == ["launcher", "campus"]
    assert eng.identity["user"] == "u1"
    assert eng.save_blob["progress"] == 5
    assert eng.ai_privacy["cloud_export"] is False
