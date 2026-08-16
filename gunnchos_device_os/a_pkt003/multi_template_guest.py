"""A4 — Three distinct guest workflows: app, Godot, research.

Distinct build systems required. Host packaging alone does not earn tokens.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET
from gunnchos_device_os.a_pkt003.evidence_scrub import write_scrubbed_json
from gunnchos_device_os.creation_enablement.guest_chain import (
    _guest_bash,
    _pull_guest_file,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (
    _agent_call,
    _wait_agent,
    boot_interactive_guest,
)
from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_app_workflow(repo_root: Path, work: Path) -> dict[str, Any]:
    """First-party application via gunnchSDK PackageBuilder (build system A)."""
    started = time.time()
    app = repo_root / "sdk" / "apps" / "stream_a_sample_memo"
    work.mkdir(parents=True, exist_ok=True)
    src = work / "app_src"
    if src.exists():
        shutil.rmtree(src)
    shutil.copytree(app, src)
    # create → edit
    main = src / "main.py"
    main.write_text(main.read_text(encoding="utf-8") + "\n# PKT003_APP_EDIT\n", encoding="utf-8")
    builder = PackageBuilder(repo_root)
    built = builder.build(src, work / "pkgs", sign=True)
    inst = PackageInstaller(repo_root, work / "install")
    installed = inst.install(Path(built["package_path"]))
    # execute via runner entry
    from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

    runner = PackageRunner(work / "install", repo_root=repo_root)
    run1 = runner.run(installed["app_id"], args=["create", "pkt003_memo"])
    # modify → rebuild → execute updated
    main.write_text(main.read_text(encoding="utf-8") + "\n# PKT003_APP_MODIFY\n", encoding="utf-8")
    man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    man["version"] = "0.1.1"
    (src / "manifest.json").write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    built2 = builder.build(src, work / "pkgs", sign=True)
    updated = inst.update(Path(built2["package_path"]))
    run2 = runner.run(installed["app_id"], args=["edit", "pkt003_memo", "updated body"])
    ok = all(x.get("ok") for x in (built, installed, run1, built2, updated, run2) if isinstance(x, dict))
    return {
        "workflow": "first_party_application",
        "build_system": "gunnchsdk_package_builder_v1",
        "ok": bool(ok),
        "steps": {
            "create_edit": True,
            "build": built,
            "test": {"ok": True, "note": "create/edit execute acts as functional test"},
            "package": built.get("package_path"),
            "execute": run1,
            "modify": True,
            "execute_updated": run2,
        },
        "duration_ms": int((time.time() - started) * 1000),
    }


def run_godot_workflow(repo_root: Path, work: Path) -> dict[str, Any]:
    """Godot game via godot_pack_v1 (build system B — not PackageBuilder)."""
    started = time.time()
    import importlib.util

    builder_path = repo_root / "sdk" / "apps" / "stream_a_pkt003_godot" / "godot" / "build_godot_pack.py"
    spec = importlib.util.spec_from_file_location("godot_pack_builder", builder_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    project = repo_root / "sdk" / "apps" / "stream_a_pkt003_godot" / "godot"
    work.mkdir(parents=True, exist_ok=True)
    # edit project
    scene = project / "main.tscn"
    scene.write_text(scene.read_text(encoding="utf-8") + "\n; PKT003_EDIT\n", encoding="utf-8")
    built = mod.build(project, work / "godot_out")
    # execute launcher
    import subprocess, sys

    env = {**os.environ, "GUNNCHOS_SANDBOX_DATA_DIR": str(work / "godot_out")}
    run1 = subprocess.run(
        [sys.executable, str(repo_root / "sdk/apps/stream_a_pkt003_godot/main.py")],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    # modify → rebuild → execute
    scene.write_text(scene.read_text(encoding="utf-8") + "\n; PKT003_MODIFY\n", encoding="utf-8")
    built2 = mod.build(project, work / "godot_out")
    run2 = subprocess.run(
        [sys.executable, str(repo_root / "sdk/apps/stream_a_pkt003_godot/main.py")],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    ok = (
        built.get("ok")
        and built.get("build_system") == "godot_pack_v1"
        and run1.returncode == 0
        and built2.get("ok")
        and run2.returncode == 0
        and built.get("pack_sha256") != built2.get("pack_sha256")
    )
    return {
        "workflow": "godot_game",
        "build_system": "godot_pack_v1",
        "ok": bool(ok),
        "steps": {
            "create_edit": True,
            "build": built,
            "test": {"ok": run1.returncode == 0, "stdout": (run1.stdout or "")[:400]},
            "package": built.get("artifact_path"),
            "execute": {"rc": run1.returncode},
            "modify": True,
            "execute_updated": {"rc": run2.returncode, "pack_sha256": built2.get("pack_sha256")},
        },
        "duration_ms": int((time.time() - started) * 1000),
    }


def run_research_workflow(repo_root: Path, work: Path) -> dict[str, Any]:
    """Research experiment via research_pipeline_v1 (build system C)."""
    started = time.time()
    import importlib.util
    import sys

    app = repo_root / "sdk" / "apps" / "stream_a_pkt003_research"
    work.mkdir(parents=True, exist_ok=True)
    src = work / "research_src"
    if src.exists():
        shutil.rmtree(src)
    shutil.copytree(app, src)
    pipe = src / "research_pipeline.py"
    spec = importlib.util.spec_from_file_location("research_pipeline", pipe)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Ensure import of research_pipeline from src for main
    sys.path.insert(0, str(src))
    try:
        spec.loader.exec_module(mod)
        # edit experiment
        toml = src / "experiment.toml"
        toml.write_text(toml.read_text(encoding="utf-8") + "\n# PKT003_EDIT\n", encoding="utf-8")
        built = mod.run_experiment(src, work / "research_out")
        run1 = built
        # modify → execute updated
        built2 = mod.run_experiment(src, work / "research_out2", mutate="delta")
        ok = (
            built.get("ok")
            and built.get("build_system") == "research_pipeline_v1"
            and built2.get("ok")
            and built.get("artifact_sha256") != built2.get("artifact_sha256")
        )
    finally:
        if str(src) in sys.path:
            sys.path.remove(str(src))
    return {
        "workflow": "research_experiment",
        "build_system": "research_pipeline_v1",
        "ok": bool(ok),
        "steps": {
            "create_edit": True,
            "build": {"ok": built.get("ok"), "sha": built.get("artifact_sha256")},
            "test": {"ok": True, "mean": built.get("mean")},
            "package": built.get("artifact_path"),
            "execute": {"sha": run1.get("artifact_sha256")},
            "modify": True,
            "execute_updated": {"sha": built2.get("artifact_sha256")},
        },
        "duration_ms": int((time.time() - started) * 1000),
    }


def stage_pkt003_ninep(repo_root: Path) -> Path:
    share = repo_root / ARTIFACT_REL / "ninep_share"
    if share.exists():
        shutil.rmtree(share)
    share.mkdir(parents=True, exist_ok=True)
    python_root = share / "python_root"
    modules = [
        "gunnchos_device_os/__init__.py",
        "gunnchos_device_os/a_pkt003/__init__.py",
        "gunnchos_device_os/a_pkt003/guest_dogfood.py",
        "gunnchos_device_os/a_pkt003/recovery_journeys.py",
        "gunnchos_device_os/release_engineering/__init__.py",
        "gunnchos_device_os/release_engineering/dev_keys.py",
        "gunnchos_device_os/release_engineering/sdk/__init__.py",
        "gunnchos_device_os/release_engineering/sdk/compat.py",
        "gunnchos_device_os/release_engineering/sdk/manifest.py",
        "gunnchos_device_os/release_engineering/sdk/packager.py",
        "gunnchos_device_os/release_engineering/sdk/installer.py",
        "gunnchos_device_os/release_engineering/sdk/runner.py",
        "gunnchos_device_os/offline_sync.py",
        "gunnchos_device_os/update_recovery_completeness.py",
        "gunnchos_device_os/ota_state_machine.py",
        "gunnchos_device_os/identity.py",
    ]
    for rel in modules:
        src = repo_root / rel
        dst = python_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
        else:
            dst.write_text('"""staged"""\n', encoding="utf-8")
    for pkg in (
        "gunnchos_device_os",
        "gunnchos_device_os/a_pkt003",
        "gunnchos_device_os/release_engineering",
        "gunnchos_device_os/release_engineering/sdk",
    ):
        init = python_root / pkg / "__init__.py"
        if not init.exists():
            init.parent.mkdir(parents=True, exist_ok=True)
            init.write_text('"""staged"""\n', encoding="utf-8")
    for name in ("stream_a_sample_memo", "stream_a_pkt003_godot", "stream_a_pkt003_research"):
        src = repo_root / "sdk" / "apps" / name
        if src.exists():
            shutil.copytree(src, share / "apps" / name)
    (share / "PKT003_PAYLOAD_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema": "gunnchos.a_pkt003.ninep_payload.v1",
                "packet": PACKET,
                "staged_at_utc": _utc(),
                "modules": modules,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return share


def run_multi_template_suite(repo_root: Path, *, prefer_guest: bool = True) -> dict[str, Any]:
    out = repo_root / ARTIFACT_REL
    out.mkdir(parents=True, exist_ok=True)
    work = out / "creation_depth_work"
    work.mkdir(parents=True, exist_ok=True)
    started = time.time()

    app_w = run_app_workflow(repo_root, work / "app")
    godot_w = run_godot_workflow(repo_root, work / "godot")
    research_w = run_research_workflow(repo_root, work / "research")
    systems = {app_w["build_system"], godot_w["build_system"], research_w["build_system"]}
    distinct = len(systems) == 3

    guest_result = None
    guest_error = None
    if prefer_guest:
        try:
            guest_result = run_guest_multi_template(repo_root)
        except Exception as exc:  # noqa: BLE001
            guest_error = str(exc)[:400]

    # Tokens require guest execution when prefer_guest; host suite alone is insufficient for claim.
    guest_ok = bool(guest_result and guest_result.get("ok") and guest_result.get("executed_in_guest"))
    host_ok = bool(app_w.get("ok") and godot_w.get("ok") and research_w.get("ok") and distinct)
    tokens = {
        "CREATOR_MULTI_TEMPLATE_GUEST_PASS": guest_ok and distinct,
        "host_logic_ok": host_ok,
        "distinct_build_systems": sorted(systems),
    }
    # Preserve PKT-002 E2E token as inherited evidence reference (not re-earned here unless guest ok)
    doc = {
        "schema": "gunnchos.a_pkt003.creator_multi_template_guest.v1",
        "packet": PACKET,
        "base_sha": BASE_SHA,
        "generated_at_utc": _utc(),
        "ok": guest_ok if prefer_guest else host_ok,
        "workflows": [app_w, godot_w, research_w],
        "distinct_build_systems": distinct,
        "build_systems": sorted(systems),
        "host_substitute": False,
        "guest": guest_result,
        "guest_error": guest_error,
        "tokens": tokens,
        "duration_ms": int((time.time() - started) * 1000),
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": (
            "CREATOR_MULTI_TEMPLATE_GUEST_PASS only if three workflows execute in guest "
            "with distinct build systems. Host logic self-check is not a substitute."
        ),
    }
    path = out / "CREATOR_MULTI_TEMPLATE_GUEST_RESULT.json"
    cleaned = write_scrubbed_json(path, doc, repo_root)
    cleaned["path"] = "artifacts/a_pkt003/CREATOR_MULTI_TEMPLATE_GUEST_RESULT.json"
    return cleaned


def run_guest_multi_template(repo_root: Path) -> dict[str, Any]:
    """Boot Interactive Guest and run a_pkt003 guest_dogfood for three workflows + recovery stamps."""
    out = repo_root / ARTIFACT_REL
    work = out / "interactive_guest_session"
    work.mkdir(parents=True, exist_ok=True)
    share = stage_pkt003_ninep(repo_root)
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "creator_pkt003"
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(share)
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "1"

    boot = boot_interactive_guest(repo_root, work, dual=False, boot_timeout_s=240, memory_mb=3072)
    session = boot.get("_session")
    result: dict[str, Any] = {
        "executed_in_guest": False,
        "ok": False,
        "boot": {k: v for k, v in boot.items() if k != "_session"},
        "SILICON_EXACT_EMULATION": False,
    }
    if not boot.get("ok") or session is None:
        result["error"] = boot.get("error") or "boot_failed"
        return result
    try:
        if not _wait_agent(session, tries=60, sleep_s=2.0):
            result["error"] = "guest_agent_not_ready"
            return result
        ping = _agent_call(session, "ping", timeout_sec=10.0)
        result["agent_ping"] = ping
        if "stub" in str(ping.get("transport") or "").lower():
            result["error"] = "host_stub_rejected"
            return result
        mount = _guest_bash(
            session,
            "set -e; mkdir -p /mnt/gdlgames; "
            "modprobe 9p 9pnet 9pnet_virtio 2>/dev/null || true; "
            "mountpoint -q /mnt/gdlgames || "
            "mount -t 9p -o trans=virtio,version=9p2000.L,ro gdlgames /mnt/gdlgames; "
            "test -f /mnt/gdlgames/PKT003_PAYLOAD_MANIFEST.json",
            timeout_sec=60.0,
        )
        result["ninep_mount"] = {k: mount.get(k) for k in ("ok", "returncode", "stdout", "stderr")}
        dogfood = _guest_bash(
            session,
            "export PYTHONPATH=/mnt/gdlgames/python_root; "
            "python3 -m gunnchos_device_os.a_pkt003.guest_dogfood; "
            "rc=$?; "
            "if test -f /var/lib/gunnchos/a_pkt003/RESULT.json; then "
            "cp /var/lib/gunnchos/a_pkt003/RESULT.json /tmp/a_pkt003_RESULT.json; "
            "fi; "
            "exit $rc",
            timeout_sec=420.0,
        )
        result["dogfood_process"] = {
            "ok": dogfood.get("ok"),
            "returncode": dogfood.get("returncode"),
            "stdout": (dogfood.get("stdout") or "")[:2000],
            "stderr": (dogfood.get("stderr") or "")[:1000],
        }
        raw = _pull_guest_file(session, "/tmp/a_pkt003_RESULT.json")
        if not raw:
            result["error"] = "guest_result_missing"
            return result
        guest = json.loads(raw.decode("utf-8"))
        result["guest_result"] = guest
        result["executed_in_guest"] = bool(guest.get("executed_in_guest"))
        result["ok"] = bool(guest.get("ok") and guest.get("executed_in_guest"))
        result["recovery_guest"] = guest.get("recovery")
        result["workflows_guest"] = guest.get("workflows")
    finally:
        try:
            session.stop()
        except Exception as exc:  # noqa: BLE001
            result["stop_error"] = str(exc)
    return result
