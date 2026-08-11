"""WP-011 Wave 4: guest DRM dual + Ring virtio-serial observe + ecosystem scaffold."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import (
    GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE,
    SILICON_EXACT_EMULATION,
)
from gunnchos_device_os.device_lab.ecosystem import ecosystem_topology, run_eco001_smoke
from gunnchos_device_os.device_lab.session import register_lab_work_root, unregister_lab_work_root
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import high_fidelity_dual_gate


ROOT = Path(__file__).resolve().parents[2]


def test_master_complete_still_false_after_wave4():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False
    tokens = json.loads((ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json").read_text(encoding="utf-8"))
    assert tokens["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert tokens["RING_SPATIAL_ACCURACY"] == "SIMULATED"
    # Wave 4 earned tokens (Mac FORCE_REAL_GUEST proofs recorded in register).
    assert tokens["GUEST_DUAL_OUTPUT_PASS"] is True
    assert tokens["RING_TO_REAL_APPLICATION_INPUT_PASS"] is True


def test_device_attach_still_not_dual_pass():
    attached = [
        {
            "id": "guest-gpu0-out0",
            "connected": False,
            "source": "qemu_virtio_gpu_device_attached",
            "class": "host_device_intent",
        },
        {
            "id": "guest-gpu0-out1",
            "connected": False,
            "source": "qemu_virtio_gpu_device_attached",
            "class": "host_device_intent",
        },
    ]
    gate = high_fidelity_dual_gate(attached, claim_guest_dual=False)
    assert gate["GUEST_DUAL_OUTPUT_PASS"] is False


def test_guest_drm_dual_gate_pass():
    guest = [
        {"id": "card0-Virtual-1", "connected": True, "source": "guest_agent", "class": "guest_drm"},
        {"id": "card0-Virtual-2", "connected": True, "source": "guest_agent", "class": "guest_drm"},
    ]
    gate = high_fidelity_dual_gate(guest, claim_guest_dual=True)
    assert gate["ok"] is True
    assert gate["GUEST_DUAL_OUTPUT_PASS"] is True
    assert gate["gate"] == "PASS_GUEST_DUAL"


def test_ecosystem_topology_scaffold():
    topo = ecosystem_topology()
    assert topo["ok"] is True
    assert topo["simultaneous_soak"] is False
    assert topo["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert len(topo["members"]) >= 5


def test_eco001_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Keep evidence under writable artifact root (sandbox / CI).
    art = tmp_path / "device_lab"
    art.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GUNNCHDEVICE_LAB_ARTIFACT_ROOT", str(art))
    register_lab_work_root(tmp_path, repo_root=ROOT)
    try:
        result = run_eco001_smoke(repo_root=ROOT)
        assert result["ok"] is True
        assert result["scenario_id"] == "ECO-001"
        assert result["simultaneous_multi_device"] is False
        assert result["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
        assert result["depth"] == "smoke_topology_and_session"
    finally:
        unregister_lab_work_root(tmp_path)


def test_score_script_no_hardcoded_tens_and_master_false():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/device_lab_score_from_register.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["tokens_master_complete"] is False
    assert data["hardcoded_tens_forbidden"] is True
    assert data["GUEST_DUAL_OUTPUT_PASS"] is True
    assert data["RING_TO_REAL_APPLICATION_INPUT_PASS"] is True
    assert data["RING_SPATIAL_ACCURACY"] == "SIMULATED"
    grades = data["baseline_12_grades"]
    # Physical twin must not be a free 10
    twin = grades["physical_digital_twin_fidelity"]["grade"]
    assert twin <= 3
    # Mean must be computed, not hardcoded
    assert isinstance(data["grade_mean_of_12"], (int, float))
    assert 0 < data["grade_mean_of_12"] < 10
