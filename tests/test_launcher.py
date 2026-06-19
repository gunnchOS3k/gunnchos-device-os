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
