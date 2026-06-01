from gunnchos_launcher.seven_gc_bridge import export_seven_gc_device_state


def test_export():
    s = export_seven_gc_device_state("ds_xl_coder", "research_measurement")
    assert s["site_id"] == "gary"
