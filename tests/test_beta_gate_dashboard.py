"""Beta gate dashboard validation tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_beta_gate_yaml_exists():
    assert (ROOT / "beta_gate" / "beta_gate_status.yaml").exists()


def test_validate_beta_gate_script_passes():
    rc = subprocess.call(["python3", str(ROOT / "scripts" / "validate_beta_gate.py")], cwd=ROOT)
    assert rc == 0


def test_beta_not_ready():
    import yaml

    data = yaml.safe_load((ROOT / "beta_gate" / "beta_gate_status.yaml").read_text(encoding="utf-8"))
    assert data["beta_ready"] is False
