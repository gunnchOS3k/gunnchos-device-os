from gunnchos_device_os.mode_manager import get_mode_policy, MODES

def test_modes_count():
    assert len(MODES) == 6

def test_school_blocks_steam():
    p = get_mode_policy("School")
    assert "steam" in p["blocked_apps"]
