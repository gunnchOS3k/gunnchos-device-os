"""Tests for firmware host probe."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from firmware_compat.probes.firmware_probe import run_probes

ROOT = Path(__file__).resolve().parents[1]


def test_run_probes_all_modules():
    result = run_probes("student_14_5")
    assert result["device_id"] == "student_14_5"
    assert result["host_environment"] is True
    assert len(result["probes"]) == 10
    for probe in result["probes"].values():
        assert probe["status"] in ("pass", "warn", "fail", "skip")


def test_fixture_probe_passes():
    fixture = ROOT / "firmware_compat/fixtures/sample_host_probe_student_14_5.json"
    result = run_probes("student_14_5", fixture_path=fixture)
    assert result["device_id"] == "student_14_5"
    assert result["probes"]["display"]["status"] == "pass"


def test_firmware_probe_cli():
    out = ROOT / "results/_test_firmware_probe_cli.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "firmware_compat/probes/firmware_probe.py"),
         "--device", "student_14_5", "--output", str(out)],
        cwd=ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    data = json.loads(out.read_text())
    assert data["device_id"] == "student_14_5"
