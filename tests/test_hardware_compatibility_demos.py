"""Tests for hardware compatibility demo outputs."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ensure_demo(script: str, output: str) -> dict:
    path = ROOT / output
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)}, check=True)
    return json.loads(path.read_text())


def test_compatibility_demo():
    data = _ensure_demo("scripts/run_hardware_compatibility_demo.py", "results/hardware_compatibility_demo_output.json")
    assert data.get("hardware_compatibility_demo") is True
    assert len(data.get("scenarios", [])) >= 10


def test_boot_readiness_demo():
    data = _ensure_demo("scripts/run_hardware_boot_readiness_demo.py", "results/hardware_boot_readiness_demo_output.json")
    assert len(data.get("devices", {})) >= 4
