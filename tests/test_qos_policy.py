from gunnchos_launcher.qos_policy import get_qos_profile


def test_urllc():
    q = get_qos_profile("urllc_strict")
    assert q["latency_target_ms"] == 10.0
