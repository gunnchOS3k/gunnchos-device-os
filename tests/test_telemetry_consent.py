from gunnchos_device_os.telemetry_consent import ConsentState

def test_opt_out_no_record():
    c = ConsentState(opted_in=False)
    c.record("x", 1)
    assert c.export()["events"] == 0
