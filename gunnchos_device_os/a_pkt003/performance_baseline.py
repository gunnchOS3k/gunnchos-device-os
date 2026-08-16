"""A6 — Digital performance baseline (emulated/host only)."""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET
from gunnchos_device_os.a_pkt003.evidence_scrub import write_scrubbed_json
from gunnchos_device_os.device_lab.ecosystem import continuity as cont
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session
from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder
from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner
from gunnchos_device_os.update_recovery_completeness import UpdateRecoverySuite


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ms(started: float) -> int:
    return int((time.time() - started) * 1000)


def run_performance_baseline(repo_root: Path) -> dict[str, Any]:
    out = repo_root / ARTIFACT_REL
    out.mkdir(parents=True, exist_ok=True)
    work = out / "perf_work"
    work.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, Any] = {}

    t0 = time.time()
    sess = start_session("student_14_5", repo_root=repo_root)
    metrics["boot_to_session_ms"] = _ms(t0)
    metrics["boot_to_session_backend"] = "device_lab_session"
    stop_session(sess["instance_id"])

    app = repo_root / "sdk" / "apps" / "stream_a_sample_memo"
    builder = PackageBuilder(repo_root)
    t0 = time.time()
    built = builder.build(app, work / "pkgs", sign=True)
    metrics["creator_build_ms"] = _ms(t0)
    inst = PackageInstaller(repo_root, work / "install")
    t0 = time.time()
    installed = inst.install(Path(built["package_path"]))
    metrics["package_install_ms"] = _ms(t0)
    runner = PackageRunner(work / "install", repo_root=repo_root)
    t0 = time.time()
    run = runner.run(installed["app_id"], args=["create", "perf_memo"])
    metrics["app_launch_ms"] = _ms(t0)
    metrics["app_launch_ok"] = bool(run.get("ok"))

    t0 = time.time()
    waike = repo_root / "sdk" / "templates" / "waike_lab" / "main.py"
    if waike.exists():
        proc = subprocess.run(
            [sys.executable, str(waike)], capture_output=True, text=True, timeout=20, check=False
        )
        metrics["waike_launch_ms"] = _ms(t0)
        metrics["waike_launch_ok"] = proc.returncode == 0
    else:
        metrics["waike_launch_ms"] = None
        metrics["waike_launch_ok"] = False

    t0 = time.time()
    ai = repo_root / "sdk" / "templates" / "ai_skill_agent" / "main.py"
    if ai.exists():
        proc = subprocess.run(
            [sys.executable, str(ai)], capture_output=True, text=True, timeout=20, check=False
        )
        metrics["ai_startup_ms"] = _ms(t0)
        metrics["ai_startup_ok"] = proc.returncode == 0
    else:
        metrics["ai_startup_ms"] = None
        metrics["ai_startup_ok"] = False

    a = start_session("student_14_5", repo_root=repo_root)
    b = start_session("dsxl_coder", repo_root=repo_root)
    try:
        student = get_session(a["instance_id"])
        dsxl = get_session(b["instance_id"])
        cont.seed_student_project(student.work, title="perf")
        t0 = time.time()
        bundle = work / "mig_bundle"
        cont.export_bundle(
            source_work=student.work,
            bundle_dir=bundle,
            identity={"user": "perf", "device_from": "student_14_5"},
        )
        cont.import_bundle(
            bundle_dir=bundle,
            dest_work=dsxl.work,
            expected_identity={"user": "perf", "device_from": "student_14_5"},
        )
        metrics["state_migration_ms"] = _ms(t0)
    finally:
        stop_session(a["instance_id"])
        stop_session(b["instance_id"])

    t0 = time.time()
    suite = UpdateRecoverySuite()
    suite.scenario_rollback_after_bad_health()
    metrics["recovery_time_ms"] = _ms(t0)

    doc = {
        "schema": "gunnchos.a_pkt003.digital_performance_baseline.v1",
        "packet": PACKET,
        "base_sha": BASE_SHA,
        "generated_at_utc": _utc(),
        "environment": {
            "host": "<lab-host>",
            "platform": platform.system(),
            "python": platform.python_version(),
            "measurement_class": "HOST_OBSERVED",
            "emulated_or_host_only": True,
        },
        "metrics_ms": metrics,
        "physical_fps": None,
        "physical_battery": None,
        "physical_rf": None,
        "physical_thermal": None,
        "silicon_performance": None,
        "SILICON_EXACT_EMULATION": False,
        "ok": True,
        "claim_boundary": (
            "Emulated/host digital timings only. Never infer physical FPS, battery, RF, "
            "thermal, or silicon performance."
        ),
    }
    path = out / "DIGITAL_PERFORMANCE_BASELINE_PKT003.json"
    cleaned = write_scrubbed_json(path, doc, repo_root)
    cleaned["path"] = "artifacts/a_pkt003/DIGITAL_PERFORMANCE_BASELINE_PKT003.json"
    return cleaned
