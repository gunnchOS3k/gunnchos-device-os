from gunnchos_device_os.mode_manager import get_mode_policy, MODES

def test_modes_count():
    assert len(MODES) == 7

def test_school_blocks_steam():
    p = get_mode_policy("School")
    assert "steam" in p["blocked_apps"]

def test_coder_mode_exists():
    p = get_mode_policy("Coder")
    assert "vscode" in p["allowed_apps"]
