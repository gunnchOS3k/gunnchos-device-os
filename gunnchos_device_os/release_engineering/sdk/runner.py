"""gunnchSDK package runner — actually executes an installed app's
entrypoint inside a restricted subprocess sandbox, with real logs and
crash reports on disk.

Supports ``runtime: python`` (default) and ``runtime: godot`` (launches a
host Godot binary against an installed ``.pck`` + harness script).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class RunError(RuntimeError):
    pass


class PackageRunner:
    def __init__(self, install_root: Path, *, repo_root: Path | None = None) -> None:
        self.install_root = Path(install_root)
        self.repo_root = Path(repo_root) if repo_root is not None else None

    def _registry(self) -> dict[str, Any]:
        reg_path = self.install_root / "registry.json"
        if not reg_path.exists():
            raise RunError("no_apps_installed")
        return json.loads(reg_path.read_text(encoding="utf-8"))

    def _resolve_godot(self) -> str:
        from gunnchos_device_os.release_engineering.sdk.godot_runtime import resolve_godot_bin

        return resolve_godot_bin()

    def run(self, app_id: str, *, args: list[str] | None = None, timeout_s: float = 15.0) -> dict[str, Any]:
        try:
            reg = self._registry()
        except RunError as exc:
            return {"ok": False, "error": str(exc)}
        entry = reg["apps"].get(app_id)
        if entry is None:
            return {"ok": False, "error": "not_installed", "app_id": app_id}

        app_root = self.install_root / "apps" / app_id
        version_dir = self.install_root / entry["installed_path"]
        manifest = entry["manifest"]
        runtime = manifest.get("runtime", "python")

        sandbox_dir = app_root / "sandbox"
        data_dir = sandbox_dir / "data"
        logs_dir = sandbox_dir / "logs"
        crash_dir = sandbox_dir / "crash_reports"
        for d in (data_dir, logs_dir, crash_dir):
            d.mkdir(parents=True, exist_ok=True)

        sandbox_profile = manifest.get("sandbox_profile", {})
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(sandbox_dir / "home"),
            "GUNNCHOS_APP_ID": app_id,
            "GUNNCHOS_APP_VERSION": entry["version"],
            "GUNNCHOS_SANDBOX_DATA_DIR": str(data_dir),
            "GUNNCHOS_SANDBOX_NETWORK_POLICY": sandbox_profile.get("network_policy", "deny_all"),
        }
        (sandbox_dir / "home").mkdir(parents=True, exist_ok=True)
        if self.repo_root is not None:
            env["GUNNCHOS_REPO_ROOT"] = str(self.repo_root)
            env["PYTHONPATH"] = f"{self.repo_root}:{self.repo_root / 'src'}"

        if runtime == "godot":
            try:
                godot_bin = self._resolve_godot()
            except FileNotFoundError as exc:
                return {"ok": False, "error": f"godot_missing:{exc}", "app_id": app_id}
            godot_cfg = manifest.get("godot") or {}
            main_pack = version_dir / godot_cfg.get("main_pack", "godot/game.pck")
            if not main_pack.exists():
                return {"ok": False, "error": "godot_main_pack_missing", "path": str(main_pack)}
            harness = godot_cfg.get("harness_script", "res://tools/gunnchos_sdk_adoption_harness.gd")
            cmd = [
                godot_bin,
                "--headless",
                "--main-pack",
                str(main_pack),
                "--script",
                harness,
                *(args or []),
            ]
            # Godot launches can exceed the default python-app timeout.
            timeout_s = max(timeout_s, 60.0)
        else:
            entrypoint = version_dir / manifest["entrypoint"]
            if not entrypoint.exists():
                return {"ok": False, "error": "entrypoint_missing", "path": str(entrypoint)}
            cmd = [sys.executable, str(entrypoint), *(args or [])]

        run_id = f"run-{int(time.time() * 1000)}"
        started = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(data_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            exit_code = proc.returncode
            stdout, stderr = proc.stdout, proc.stderr
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            exit_code = -1
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\nTIMEOUT"
            timed_out = True
        duration_s = time.time() - started

        log_path = logs_dir / f"{run_id}.log"
        log_path.write_text(
            f"=== gunnchSDK run {run_id} ===\napp_id={app_id}\nversion={entry['version']}\n"
            f"runtime={runtime}\ncmd={' '.join(cmd)}\n"
            f"exit_code={exit_code}\nduration_s={duration_s:.4f}\n\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n",
            encoding="utf-8",
        )

        crash_report_path = None
        if exit_code != 0:
            crash_report_path = crash_dir / f"{run_id}_crash.json"
            crash_report_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "app_id": app_id,
                        "version": entry["version"],
                        "runtime": runtime,
                        "exit_code": exit_code,
                        "timed_out": timed_out,
                        "stderr_tail": stderr[-2000:],
                        "ts": time.time(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        return {
            "ok": exit_code == 0,
            "app_id": app_id,
            "version": entry["version"],
            "runtime": runtime,
            "run_id": run_id,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "duration_s": duration_s,
            "stdout": stdout,
            "stderr": stderr,
            "log_path": str(log_path),
            "crash_report_path": str(crash_report_path) if crash_report_path else None,
            "command": cmd,
        }
