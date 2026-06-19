from gunnchos_device_os.policy_engine import evaluate

def test_steam_blocked_school():
    assert evaluate("student", "School", "steam")["allowed"] is False

def test_steam_allowed_play():
    assert evaluate("developer", "Play", "steam")["allowed"] is True
