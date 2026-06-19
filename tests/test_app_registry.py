from gunnchos_device_os.app_registry import list_apps

def test_gaming_apps():
    assert "steam" in list_apps("gaming")
