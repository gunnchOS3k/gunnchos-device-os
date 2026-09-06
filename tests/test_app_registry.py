from gunnchos_device_os.app_registry import list_apps, get_app, LEARNING_OS_REGISTRY_ID, resolve_app_id

def test_gaming_apps():
    assert "steam" in list_apps("gaming")


def test_learning_os_registered():
    assert LEARNING_OS_REGISTRY_ID in list_apps("education")
    assert "waike_offline" in list_apps("education")
    assert resolve_app_id("waike_offline") == LEARNING_OS_REGISTRY_ID
    assert get_app(LEARNING_OS_REGISTRY_ID)["bundle_id"] == "com.gunnchos.waike.learning"