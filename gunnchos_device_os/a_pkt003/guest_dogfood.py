"""In-guest A-PKT-003 dogfood: recovery stamps + three creation workflows."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _paths() -> tuple[Path, Path, Path]:
    evidence = Path(os.environ.get("GUNNCHOS_APKT003_EVIDENCE", "/var/lib/gunnchos/a_pkt003"))
    work = Path(os.environ.get("GUNNCHOS_APKT003_WORK", "/var/lib/gunnchos/a_pkt003_work"))
    payload = Path(os.environ.get("GUNNCHOS_APKT003_PAYLOAD", "/mnt/gdlgames"))
    return evidence, work, payload


def _run_recovery(work: Path, repo_python: Path, payload: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo_python))
    from gunnchos_device_os.a_pkt003.recovery_journeys import (
        journey_jr1_interrupted_app_update,
        journey_jr2_os_update_rollback,
        journey_jr3_disk_pressure,
        journey_jr4_service_crash,
        journey_jr5_network_loss,
    )

    repo_root = work / "repo_stub"
    if repo_root.exists():
        shutil.rmtree(repo_root)
    repo_root.mkdir(parents=True)
    apps = repo_root / "sdk" / "apps"
    apps.mkdir(parents=True)
    src_app = payload / "apps" / "stream_a_sample_memo"
    if src_app.exists():
        shutil.copytree(src_app, apps / "stream_a_sample_memo")
    staged = payload / "python_root" / "gunnchos_device_os"
    if staged.exists():
        shutil.copytree(staged, repo_root / "gunnchos_device_os")

    results = {
        "J-R1": journey_jr1_interrupted_app_update(repo_root, work / "jr1"),
        "J-R2": journey_jr2_os_update_rollback(repo_root, work / "jr2"),
        "J-R3": journey_jr3_disk_pressure(repo_root, work / "jr3"),
        "J-R4": journey_jr4_service_crash(repo_root, work / "jr4"),
        "J-R5": journey_jr5_network_loss(repo_root, work / "jr5"),
    }
    return {
        "ok": all(v.get("ok") for v in results.values()),
        "journeys": results,
        "executed_in_guest": True,
    }


def _run_workflows(work: Path, payload: Path, repo_python: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo_python))
    from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder
    from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
    from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

    repo_root = work / "repo_stub"
    app_dir = repo_root / "sdk" / "apps" / "stream_a_sample_memo"
    builder = PackageBuilder(repo_root)
    built = builder.build(app_dir, work / "pkgs", sign=True)
    inst = PackageInstaller(repo_root, work / "install")
    installed = inst.install(Path(built["package_path"]))
    runner = PackageRunner(work / "install", repo_root=repo_root)
    memo = f"guest_memo_{int(time.time())}"
    run1 = runner.run(installed["app_id"], args=["create", memo])
    app_ok = bool(built.get("ok") and installed.get("ok") and run1.get("ok"))

    godot_proj = payload / "apps" / "stream_a_pkt003_godot" / "godot"
    godot_builder = godot_proj / "build_godot_pack.py"
    godot: dict[str, Any] = {"ok": False}
    if godot_builder.exists():
        import importlib.util

        # Copy project off readonly 9p before building.
        godot_work = work / "godot_proj"
        if godot_work.exists():
            shutil.rmtree(godot_work)
        shutil.copytree(godot_proj, godot_work)
        spec = importlib.util.spec_from_file_location(
            "godot_pack_builder", godot_work / "build_godot_pack.py"
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        godot = mod.build(godot_work, work / "godot_out")
        godot["build_system"] = godot.get("build_system") or "godot_pack_v1"
        # Execute launcher against pack artifact
        env = {**os.environ, "GUNNCHOS_SANDBOX_DATA_DIR": str(work / "godot_out")}
        launch = subprocess.run(
            [sys.executable, str(payload / "apps" / "stream_a_pkt003_godot" / "main.py")],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )
        godot["launch_rc"] = launch.returncode
        godot["ok"] = bool(godot.get("ok") and launch.returncode == 0)

    research_src = payload / "apps" / "stream_a_pkt003_research"
    research: dict[str, Any] = {"ok": False}
    if (research_src / "research_pipeline.py").exists():
        import importlib.util

        research_app = work / "research_app"
        if research_app.exists():
            shutil.rmtree(research_app)
        shutil.copytree(research_src, research_app)
        sys.path.insert(0, str(research_app))
        spec = importlib.util.spec_from_file_location(
            "research_pipeline", research_app / "research_pipeline.py"
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        research = mod.run_experiment(research_app, work / "research_out", mutate="guest")
        research["build_system"] = "research_pipeline_v1"

    systems = {
        "gunnchsdk_package_builder_v1",
        str(godot.get("build_system")),
        str(research.get("build_system")),
    }
    ok = app_ok and bool(godot.get("ok")) and bool(research.get("ok")) and len(systems) == 3
    return {
        "ok": ok,
        "workflows": {
            "app": {"ok": app_ok, "build_system": "gunnchsdk_package_builder_v1", "run": run1},
            "godot": godot,
            "research": research,
        },
        "distinct_build_systems": sorted(systems),
        "executed_in_guest": True,
    }


def main() -> int:
    evidence, work, payload = _paths()
    evidence.mkdir(parents=True, exist_ok=True)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    repo_python = payload / "python_root"
    started = time.time()
    recovery_error = None
    workflows_error = None
    try:
        recovery = _run_recovery(work, repo_python, payload)
    except Exception as exc:  # noqa: BLE001
        recovery = {"ok": False, "error": str(exc)[:500], "executed_in_guest": True}
        recovery_error = str(exc)[:500]
    try:
        workflows = _run_workflows(work, payload, repo_python)
    except Exception as exc:  # noqa: BLE001
        workflows = {"ok": False, "error": str(exc)[:500], "executed_in_guest": True}
        workflows_error = str(exc)[:500]
    doc = {
        "schema": "gunnchos.a_pkt003.guest_dogfood.v1",
        "executed_in_guest": True,
        "hostname_probe": Path("/etc/hostname").read_text(encoding="utf-8").strip()
        if Path("/etc/hostname").exists()
        else None,
        "ok": bool(recovery.get("ok") and workflows.get("ok")),
        "recovery": recovery,
        "workflows": workflows,
        "recovery_error": recovery_error,
        "workflows_error": workflows_error,
        "duration_ms": int((time.time() - started) * 1000),
        "SILICON_EXACT_EMULATION": False,
        "completed_at_utc": _utc(),
    }
    (evidence / "RESULT.json").write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"ok": doc["ok"], "evidence": str(evidence / "RESULT.json")}))
    return 0 if doc["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
