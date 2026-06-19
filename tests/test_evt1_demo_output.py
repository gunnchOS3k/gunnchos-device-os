def test_demo_json_keys():
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "results/device_os_evt1_demo_output.json"
    if not p.exists():
        import subprocess, sys
        subprocess.check_call([sys.executable, "scripts/run_device_os_demo.py"], cwd=p.parents[1])
    data = json.loads(p.read_text())
    for key in ("device_profile", "active_mode", "allowed_apps", "blocked_apps", "telemetry_policy", "update_status", "rollback_status", "walkthrough"):
        assert key in data
