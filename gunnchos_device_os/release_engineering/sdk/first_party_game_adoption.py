"""FIRST_PARTY_GAME_SDK_ADOPTION_PASS — real Pedestrian Pursuit pipeline.

Accepted main SHA → Godot import/export-pack → gunnchSDK manifest →
``.gunnchpkg`` (DEV/TEST sign) → install → launch Godot runtime
(``--main-pack`` + adoption harness) → process/save/input/state evidence →
update → incompatible rejection → uninstall.

This is intentionally NOT a Python PACKAGE_MANIFEST checker.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering.sdk.godot_runtime import (
    ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
    default_pedestrian_repo,
    ensure_accepted_worktree,
    export_godot_pack,
    inject_adoption_harness,
    resolve_godot_bin,
)
from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
from gunnchos_device_os.release_engineering.sdk.manifest import new_manifest
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder
from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

APP_ID = "gunnchos.pedestrian_pursuit"
HARNESS_REL = "tools/gunnchos_sdk_adoption_harness.gd"
PCK_REL = "godot/pedestrian_pursuit.pck"


def _harness_src(repo_root: Path) -> Path:
    return (
        repo_root
        / "sdk"
        / "apps"
        / "pedestrian_pursuit"
        / "tools"
        / "gunnchos_sdk_adoption_harness.gd"
    )


def _write_app_dir(
    app_dir: Path,
    *,
    pck_src: Path,
    version: str,
    accepted_sha: str,
    export_meta: dict[str, Any],
    min_os_version: str = "0.1.0",
) -> Path:
    if app_dir.exists():
        shutil.rmtree(app_dir)
    godot_dir = app_dir / "godot"
    godot_dir.mkdir(parents=True)
    shutil.copy2(pck_src, godot_dir / "pedestrian_pursuit.pck")

    manifest = new_manifest(
        app_id=APP_ID,
        name="Pedestrian Pursuit",
        version=version,
        min_os_version=min_os_version,
        entrypoint="launch_godot.py",
        permissions=["storage_read", "storage_write", "display_output"],
        capabilities_required=["storage.read", "storage.write", "display.render"],
    )
    manifest["runtime"] = "godot"
    manifest["stub_content"] = False
    manifest["source"] = {
        "repo": "pedestrian-pursuit",
        "accepted_sha": accepted_sha,
        "github": "gunnchOS3k/pedestrian-pursuit",
    }
    manifest["godot"] = {
        "main_pack": PCK_REL,
        "harness_script": "res://tools/gunnchos_sdk_adoption_harness.gd",
        "export_mode": export_meta.get("export_mode"),
        "export_preset": export_meta.get("preset"),
        "pck_sha256": export_meta.get("pck_sha256"),
        "godot_version": export_meta.get("godot_version"),
    }
    (app_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # Entrypoint kept for python-runtime fallback / inspection; PackageRunner
    # uses runtime=godot and launches the engine directly.
    (app_dir / "launch_godot.py").write_text(
        "#!/usr/bin/env python3\n"
        "print('gunnchos.pedestrian_pursuit godot package — use PackageRunner runtime=godot')\n",
        encoding="utf-8",
    )
    return app_dir


def run_first_party_game_sdk_adoption(repo_root: Path) -> dict[str, Any]:
    """Execute the full adoption pipeline; prefer FAIL when Godot/export missing."""
    repo_root = Path(repo_root)
    out: dict[str, Any] = {
        "schema": "gunnchos.wp013.first_party_game_sdk_adoption.v1",
        "app_id": APP_ID,
        "accepted_sha_required": ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
        "PRODUCTION_RELEASE_CLAIMED": False,
        "python_manifest_wrapper_rejected": True,
        "ok": False,
        "FIRST_PARTY_GAME_SDK_ADOPTION_PASS": False,
        "steps": {},
        "claim_boundary": (
            "Digital host Godot 4.5 export-pack + gunnchSDK install/run of Pedestrian "
            "Pursuit at an accepted main SHA. Not a shipping store build, not Android "
            "APK certification, not PRODUCTION signed. PRODUCTION_RELEASE_CLAIMED=false."
        ),
    }

    harness = _harness_src(repo_root)
    if not harness.exists():
        out["error"] = "adoption_harness_missing"
        out["steps"]["harness"] = {"ok": False, "path": str(harness)}
        return out

    try:
        godot_bin = resolve_godot_bin()
    except FileNotFoundError as exc:
        out["error"] = str(exc)
        out["steps"]["godot_resolve"] = {"ok": False, "error": str(exc)}
        return out

    try:
        pp_repo = default_pedestrian_repo(repo_root)
    except FileNotFoundError as exc:
        out["error"] = str(exc)
        out["steps"]["pedestrian_repo"] = {"ok": False, "error": str(exc)}
        return out

    cache = repo_root / ".cache" / "wp013_game_sdk"
    cache.mkdir(parents=True, exist_ok=True)
    worktree = cache / "pp_accepted"
    try:
        wt = ensure_accepted_worktree(
            pedestrian_repo=pp_repo,
            worktree_dir=worktree,
            accepted_sha=ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
        )
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"worktree_failed:{exc}"
        out["steps"]["worktree"] = {"ok": False, "error": str(exc)}
        return out
    out["steps"]["worktree"] = wt

    inject_adoption_harness(Path(wt["worktree"]), harness)
    pck_path = cache / "export" / "pedestrian_pursuit.pck"
    export_meta = export_godot_pack(worktree=Path(wt["worktree"]), out_pck=pck_path, godot_bin=godot_bin)
    out["steps"]["godot_export"] = export_meta
    if not export_meta.get("ok"):
        out["error"] = export_meta.get("error", "godot_export_failed")
        return out

    evidence_dir = repo_root / "artifacts" / "wp013" / "first_party_game_sdk"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="wp013_game_sdk_") as tmp:
        tmp_path = Path(tmp)
        app_v1 = tmp_path / "app_v1"
        _write_app_dir(
            app_v1,
            pck_src=pck_path,
            version="0.4.0",
            accepted_sha=ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
            export_meta=export_meta,
        )

        builder = PackageBuilder(repo_root)
        installer = PackageInstaller(repo_root, tmp_path / "install")
        runner = PackageRunner(tmp_path / "install", repo_root=repo_root)

        build_v1 = builder.build(app_v1, tmp_path / "pkgs")
        out["steps"]["package_v1"] = {
            "ok": bool(build_v1.get("ok")),
            "signed": bool(build_v1.get("signed")),
            "package_path": build_v1.get("package_path"),
            "package_digest": build_v1.get("package_digest"),
            "file_count": build_v1.get("file_count"),
        }
        if not build_v1.get("ok") or not build_v1.get("signed"):
            out["error"] = "package_build_or_sign_failed"
            return out

        install_v1 = installer.install(Path(build_v1["package_path"]))
        out["steps"]["install_v1"] = {
            "ok": bool(install_v1.get("ok")),
            "action": install_v1.get("action"),
            "error": install_v1.get("error"),
        }
        if not install_v1.get("ok"):
            out["error"] = "install_failed"
            return out

        run_v1 = runner.run(APP_ID, timeout_s=60.0)
        # Copy evidence JSON out of sandbox if present.
        sandbox_evidence = (
            Path(tmp_path)
            / "install"
            / "apps"
            / APP_ID
            / "sandbox"
            / "data"
            / "godot_adoption_evidence.json"
        )
        copied_evidence = None
        if sandbox_evidence.exists():
            copied_evidence = evidence_dir / "godot_adoption_evidence.json"
            shutil.copy2(sandbox_evidence, copied_evidence)
        out["steps"]["launch_runtime"] = {
            "ok": bool(run_v1.get("ok")),
            "exit_code": run_v1.get("exit_code"),
            "timed_out": run_v1.get("timed_out"),
            "log_path": run_v1.get("log_path"),
            "stdout_tail": (run_v1.get("stdout") or "")[-1500:],
            "stderr_tail": (run_v1.get("stderr") or "")[-800:],
            "evidence_json": str(copied_evidence.relative_to(repo_root)) if copied_evidence else None,
            "godot_pid_marker": "process_pid" in (run_v1.get("stdout") or ""),
            "harness_pass_marker": "GUNNCHOS_FIRST_PARTY_GAME_SDK_ADOPTION_HARNESS_PASS=true"
            in (run_v1.get("stdout") or ""),
        }
        if not run_v1.get("ok"):
            out["error"] = "godot_runtime_launch_failed"
            return out

        harness_evidence: dict[str, Any] = {}
        if copied_evidence and copied_evidence.exists():
            harness_evidence = json.loads(copied_evidence.read_text(encoding="utf-8"))
        out["steps"]["game_state"] = {
            "ok": bool(harness_evidence.get("ok")),
            "input_events": (harness_evidence.get("input") or {}).get("events_injected"),
            "save_exists": (harness_evidence.get("progression") or {}).get("save_exists"),
            "mode_label": (harness_evidence.get("game_manager") or {}).get("mode_label"),
            "process_pid": harness_evidence.get("process_pid"),
            "failures": harness_evidence.get("failures"),
        }
        if not harness_evidence.get("ok"):
            out["error"] = "game_state_evidence_failed"
            return out

        # Update path: bump version, re-package, update install.
        app_v2 = tmp_path / "app_v2"
        _write_app_dir(
            app_v2,
            pck_src=pck_path,
            version="0.4.1",
            accepted_sha=ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
            export_meta=export_meta,
        )
        build_v2 = builder.build(app_v2, tmp_path / "pkgs")
        update = installer.update(Path(build_v2["package_path"]))
        out["steps"]["update"] = {
            "ok": bool(update.get("ok")),
            "action": update.get("action"),
            "previous_version": update.get("previous_version"),
            "version": update.get("version"),
        }
        if not (
            update.get("ok")
            and update.get("action") == "updated"
            and update.get("previous_version") == "0.4.0"
            and update.get("version") == "0.4.1"
        ):
            out["error"] = "update_path_failed"
            return out

        # Incompatible package must be rejected by API compatibility gate.
        app_bad = tmp_path / "app_incompatible"
        _write_app_dir(
            app_bad,
            pck_src=pck_path,
            version="0.4.2",
            accepted_sha=ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
            export_meta=export_meta,
            min_os_version="9.9.9",
        )
        build_bad = builder.build(app_bad, tmp_path / "pkgs")
        reject = installer.install(Path(build_bad["package_path"]))
        out["steps"]["incompatible_rejection"] = {
            "ok": reject.get("ok") is False
            and reject.get("error") == "api_compatibility_gate_rejected",
            "error": reject.get("error"),
        }
        if not out["steps"]["incompatible_rejection"]["ok"]:
            out["error"] = "incompatible_rejection_failed"
            return out

        uninstall = installer.uninstall(APP_ID)
        still = installer.list_installed()["apps"]
        out["steps"]["uninstall"] = {
            "ok": bool(uninstall.get("ok")) and APP_ID not in still,
            "removed_version": uninstall.get("removed_version"),
        }
        if not out["steps"]["uninstall"]["ok"]:
            out["error"] = "uninstall_failed"
            return out

    required_steps = (
        "worktree",
        "godot_export",
        "package_v1",
        "install_v1",
        "launch_runtime",
        "game_state",
        "update",
        "incompatible_rejection",
        "uninstall",
    )
    all_ok = all(bool((out["steps"].get(s) or {}).get("ok")) for s in required_steps)
    out["ok"] = all_ok
    out["FIRST_PARTY_GAME_SDK_ADOPTION_PASS"] = all_ok
    out["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    (evidence_dir / "ADOPTION_EVIDENCE.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    out["evidence_path"] = str(
        (evidence_dir / "ADOPTION_EVIDENCE.json").relative_to(repo_root)
    )
    return out
