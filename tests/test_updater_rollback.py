from gunnchos_device_os.updater import check_for_update
from gunnchos_device_os.rollback import rollback_to

def test_update_available():
    assert check_for_update("0.0.9-evt0")["update_available"] is True

def test_rollback():
    assert rollback_to("0.0.9-evt0")["success"] is True
