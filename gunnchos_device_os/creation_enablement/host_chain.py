"""Creation enablement harness — create→edit→build→test→package→install→run.

Honest: host SDK pipeline only unless guest install evidence is supplied.
CREATOR_END_TO_END_DIGITAL_PASS stays false until guest install+run is also proven.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder
from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

APP_ID = "gunnchos.stream_a_sample_memo"
APP_REL = Path("sdk/apps/stream_a_sample_memo")


def run_host_creator_chain(repo_root: Path, work: Path) -> dict[str, Any]:
    started = time.time()
    work.mkdir(parents=True, exist_ok=True)
    out_dir = work / "packages"
    install_root = work / "install"
    builder = PackageBuilder(repo_root)
    installer = PackageInstaller(repo_root, install_root)
    runner = PackageRunner(install_root, repo_root=repo_root)

    steps: dict[str, Any] = {}
    app_dir = repo_root / APP_REL
    steps["create_edit_sources_present"] = {
        "ok": (app_dir / "main.py").exists() and (app_dir / "manifest.json").exists(),
        "app_dir": str(app_dir),
    }

    # Lightweight source "test": import/exec create+edit in-process via runner after install.
    build = builder.build(app_dir, out_dir)
    steps["build_package"] = build
    if not build.get("ok"):
        return _finalize(steps, started, guest=False)

    pkg = Path(build["package_path"])
    install = installer.install(pkg)
    steps["install"] = install
    if not install.get("ok"):
        return _finalize(steps, started, guest=False)

    # Default entry creates+edits
    run_default = runner.run(APP_ID)
    steps["run_create_edit"] = run_default
    # Explicit edit/show
    run_edit = runner.run(APP_ID, args=["edit", "stream_a_hello", "Second edit via harness."])
    steps["run_edit"] = run_edit
    run_show = runner.run(APP_ID, args=["show", "stream_a_hello"])
    steps["run_show"] = run_show

    host_ok = all(
        bool(steps[k].get("ok"))
        for k in ("create_edit_sources_present", "build_package", "install", "run_create_edit", "run_edit", "run_show")
    )
    return _finalize(steps, started, guest=False, host_ok=host_ok)


def _finalize(
    steps: dict[str, Any],
    started: float,
    *,
    guest: bool,
    host_ok: bool = False,
) -> dict[str, Any]:
    return {
        "schema": "gunnchos.creation_enablement.chain.v1",
        "packet": "STREAM-A-PKT-001",
        "app_id": APP_ID,
        "ok_host_chain": host_ok,
        "ok_guest_install_run": False,
        "CREATOR_END_TO_END_DIGITAL_PASS": False,
        "guest_chain_executed": guest,
        "steps": steps,
        "duration_ms": int((time.time() - started) * 1000),
        "claim_boundary": (
            "Host SDK create/edit/build/package/install/run dogfood only. "
            "CREATOR_END_TO_END_DIGITAL_PASS remains false until guest install+run also proven. "
            "SILICON_EXACT_EMULATION=false."
        ),
        "SILICON_EXACT_EMULATION": False,
    }


def write_evidence(repo_root: Path, result: dict[str, Any]) -> Path:
    out = repo_root / "artifacts" / "stream_a_pkt_001" / "CREATION_HOST_CHAIN_EVIDENCE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    work = root / "artifacts" / "stream_a_pkt_001" / "creation_work"
    result = run_host_creator_chain(root, work)
    path = write_evidence(root, result)
    print(json.dumps({"wrote": str(path), "ok_host_chain": result["ok_host_chain"], "CREATOR_END_TO_END_DIGITAL_PASS": False}))
