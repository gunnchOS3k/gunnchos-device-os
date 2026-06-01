from gunnchos_launcher.research_measurement_mode import run_measurement_session


def test_session():
    r = run_measurement_session("handheld_hybrid")
    assert r["status"] == "completed_synthetic"
    assert "edge_io_export" in r
