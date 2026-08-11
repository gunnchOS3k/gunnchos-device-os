"""WP-011 Wave 5: ecosystem topology, ECO journeys, games, chaos, score, twin handoff."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import (
    GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE,
    SILICON_EXACT_EMULATION,
)
from gunnchos_device_os.device_lab.chaos import ChaosEngine
from gunnchos_device_os.device_lab.ecosystem import (
    ecosystem_topology,
    run_eco_scenario,
    start_ecosystem,
    stop_ecosystem,
)
from gunnchos_device_os.device_lab.ecosystem.games import launch_all_four_games
from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP
from gunnchos_device_os.device_lab.session import lab_artifact_root
from gunnchos_device_os.device_lab.twin import HANDOFF_DOC, HANDOFF_SCHEMA


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def lab_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Writable Lab artifact root (sandbox / CI friendly)."""
    art = tmp_path / "device_lab"
    art.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GUNNCHDEVICE_LAB_ARTIFACT_ROOT", str(art))
    return art


def test_master_complete_still_false_wave5():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False
    tokens = json.loads((ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json").read_text(encoding="utf-8"))
    assert tokens["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert tokens["RING_SPATIAL_ACCURACY"] == "SIMULATED"
    assert tokens.get("VF4") == "PHYSICAL_PENDING"


def test_expanded_golden_catalog_mapped():
    for jid in ("GOLDEN-01", "GOLDEN-04", "GOLDEN-05", "GOLDEN-06", "GOLDEN-07", "GOLDEN-08", "GOLDEN-09"):
        assert jid in JOURNEY_SCENARIO_MAP


def test_twin_handoff_artifacts_present():
    assert HANDOFF_DOC.is_file()
    assert HANDOFF_SCHEMA.is_file()
    schema = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["SILICON_EXACT_EMULATION"]["const"] is False
    assert schema["properties"]["VF4"]["const"] == "PHYSICAL_PENDING"


def test_ecosystem_start_status_stop(lab_artifacts: Path):
    started = start_ecosystem(repo_root=ROOT, preset="compute")
    assert started.get("eco_id")
    assert started.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE") is False
    from gunnchos_device_os.device_lab.ecosystem import get_ecosystem

    rt = get_ecosystem(started["eco_id"])
    status = rt.status()
    assert status.get("running") is True
    assert "student_14_5" in rt.member_instances
    graph = rt.graph()
    assert graph.get("ok") is True
    assert any(e.get("kind") == "continuity" for e in graph.get("edges") or [])
    stopped = stop_ecosystem(started["eco_id"])
    assert stopped.get("ok") is True
    assert (lab_artifacts / "ecosystem" / "runtimes" / started["eco_id"]).exists()


def test_eco001_continuity_depth(lab_artifacts: Path):
    result = run_eco_scenario("ECO-001", repo_root=ROOT)
    assert result["scenario_id"] == "ECO-001"
    assert result["depth"] == "continuity_export_import_checksum"
    assert result["ok"] is True
    assert result["status"] == "PASS"
    assert result["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    evid = lab_artifact_root(ROOT) / "ecosystem/ECO-001/result.json"
    assert evid.is_file()


def test_eco008_four_games_launch(lab_artifacts: Path):
    games = launch_all_four_games(
        repo_root=ROOT, work=lab_artifacts / "ecosystem/ECO-008/games_unit"
    )
    assert games["ok"] is True
    for gid in ("anime-aggressors", "beatlink-party", "earth-species", "foot-racing"):
        assert games["games"][gid]["ok"] is True
        assert games["games"][gid].get("fixture_as_launch") is not True
        assert games["games"][gid].get("process_proof") or games["games"][gid].get(
            "process_proof_at_launch"
        )


def test_eco010_honest_partial(lab_artifacts: Path):
    result = run_eco_scenario("ECO-010", repo_root=ROOT)
    assert result["scenario_id"] == "ECO-010"
    assert result["status"] == "PARTIAL"
    assert result["ok"] is False  # refuse full soak PASS
    assert result["simultaneous_soak_complete"] is False
    assert result["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert result.get("partial_ok") is True


def test_chaos_suite_inject_cleanup(lab_artifacts: Path):
    from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session

    started = start_session("handheld_hybrid", repo_root=ROOT)
    sess = get_session(started["instance_id"])
    try:
        engine = ChaosEngine(
            repo_root=ROOT,
            evidence_dir=lab_artifacts / "chaos/unit",
        )
        faults = [
            "process.sigterm_lab_echo",
            "network.packet_loss",
            "storage.removable_remove",
            "display.output_remove",
            "audio.route_change",
            "ai.cloud_denied",
            "ring.low_confidence",
            "update.bad_image_rollback",
            "resource.cpu_brief",
        ]
        suite = engine.run_suite(session=sess, faults=faults)
        assert suite["ok"] is True
        assert suite["passed"] == suite["total"]
        assert suite["cleanup"]["ok"] is True
        assert suite["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    finally:
        stop_session(sess.instance_id)


def test_golden01_05_09_lab_paths(lab_artifacts: Path):
    from gunnchos_device_os.device_lab.scenarios.engine import run_scenario

    for jid in ("GOLDEN-01", "GOLDEN-05", "GOLDEN-09"):
        result = run_scenario(jid, repo_root=ROOT)
        assert result.get("ok") is True, jid
        assert result.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE", False) is not True


def test_score_cli_and_script():
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
    assert data["RING_SPATIAL_ACCURACY"] == "SIMULATED"
    twin = data["baseline_12_grades"]["physical_digital_twin_fidelity"]["grade"]
    assert twin <= 3

    from gunnchos_device_os.device_lab.cli import main

    rc = main(["score"])
    assert rc == 0


def test_topology_still_honest():
    topo = ecosystem_topology()
    assert topo["ok"] is True
    assert topo["simultaneous_soak"] is False
    assert topo["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
