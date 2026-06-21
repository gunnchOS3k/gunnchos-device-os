"""Tests for deploy contract."""
from gunnchos_device_os.deploy_contract import (
    deploy_package,
    get_deploy_target,
    get_transport_policy,
    list_deploy_targets,
)


def test_all_targets_have_packages():
    for tid in list_deploy_targets():
        t = get_deploy_target(tid)
        assert t["allowed_package_types"]
        assert t["allowed_transports"]


def test_transport_safety_policy():
    for transport in ("local_wifi", "usb_c", "offline_export_bundle"):
        p = get_transport_policy(transport)
        assert p["safety_policy"]["no_silent_deploy"] is True


def test_failed_deploy_messages():
    r = deploy_package("ds_xl_coder", "student_14_5", "python_project", "local_wifi")
    assert r["success"] is False
    assert r["user_message"]
    assert r["technical_log"]
