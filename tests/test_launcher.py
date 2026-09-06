from gunnchos_device_os.launcher import launch_app, list_launchable

def test_launch_denied_school_steam():
    r = launch_app("student", "School", "steam")
    assert r["launched"] is False

def test_launch_allowed_play_steam():
    r = launch_app("developer", "Play", "steam")
    assert r["launched"] is True

def test_list_launchable():
    apps = list_launchable("student", "School")
    assert len(apps) > 0


def test_waike_offline_uses_first_party_runtime():
    r = launch_app("student", "School", "waike_offline")
    assert r["launched"] is True
    assert r["mock"] is False
    assert r["runtime_id"] == "waike"
    # Thin launcher handoff — Learning OS is SoR, not seed HTML alone.
    assert r["relationship"] == "thin_launcher_companion"
    assert r["seed_is_system_of_record"] is False
    assert r["system_of_record"] == "platform_tauri_learning_os"
