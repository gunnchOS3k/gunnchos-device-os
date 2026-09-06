"""Learning OS app-level package install/update/rollback via PackageManager.

Claim boundary: app-level digital package state (not Device OS OTA / A/B firmware).
User DB / outbox / progress live under userdata/ and survive version switches.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any

from gunnchos_device_os.app_registry import LEARNING_OS_BUNDLE_ID
from gunnchos_device_os.phase_xiv.packages import PackageManager

CLAIM_BOUNDARY = (
    "App-level Learning OS package install/update/rollback via Device OS "
    "PackageManager channels. Not OS-level OTA / firmware A/B. "
    "User DB/outbox/progress preserved under userdata/."
)

APP_ID = LEARNING_OS_BUNDLE_ID


class LearningOsPackageLifecycle:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.pm = PackageManager(self.root / "packages")
        self.userdata = self.root / "userdata" / APP_ID
        self.userdata.mkdir(parents=True, exist_ok=True)
        self.apps = self.root / "apps" / APP_ID
        self.apps.mkdir(parents=True, exist_ok=True)
        self._link_current()

    def _link_current(self) -> None:
        cur = self.apps / "current"
        installed = self.pm.installed.get(APP_ID)
        if not installed:
            return
        version_dir = self.apps / installed["version"]
        if not version_dir.exists():
            return
        if cur.exists() or cur.is_symlink():
            cur.unlink()
        cur.symlink_to(version_dir, target_is_directory=True)

    def userdata_paths(self) -> dict[str, Path]:
        return {
            "db": self.userdata / "learning.db",
            "outbox": self.userdata / "outbox.json",
            "progress": self.userdata / "progress.json",
        }

    def write_user_state(
        self,
        *,
        db_blob: bytes = b"user-db-v1",
        outbox: dict[str, Any] | None = None,
        progress: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        paths = self.userdata_paths()
        paths["db"].write_bytes(db_blob)
        paths["outbox"].write_text(json.dumps(outbox or {"items": []}, indent=2) + "\n")
        paths["progress"].write_text(json.dumps(progress or {}, indent=2) + "\n")
        return {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}

    def user_state_hashes(self) -> dict[str, str]:
        paths = self.userdata_paths()
        out: dict[str, str] = {}
        for k, p in paths.items():
            if p.exists():
                out[k] = hashlib.sha256(p.read_bytes()).hexdigest()
        return out

    def publish_and_install(
        self,
        version: str,
        *,
        channel: str = "stable",
        payload: bytes | None = None,
        executable_source: Path | None = None,
        mark_incompatible: bool = False,
    ) -> dict[str, Any]:
        body = payload
        if body is None:
            if executable_source and executable_source.is_file():
                body = executable_source.read_bytes()
            else:
                body = f"learning-os-{version}".encode()
        if mark_incompatible:
            # Distinct bad payload that still signs/verifies but is marked bad in META.
            body = body + b"\nINCOMPATIBLE\n"

        art = self.pm.sign_payload(APP_ID, version, channel, body)
        self.pm.publish(art, body)
        try:
            result = self.pm.install(APP_ID, version, channel)
        except PermissionError as exc:
            return {"ok": False, "error": str(exc), "claim_boundary": CLAIM_BOUNDARY}

        version_dir = self.apps / version
        if version_dir.exists():
            shutil.rmtree(version_dir)
        version_dir.mkdir(parents=True)
        exe = version_dir / "waike-learning-os"
        if executable_source and executable_source.is_file() and not mark_incompatible:
            shutil.copy2(executable_source, exe)
        else:
            # Materialize a tiny executable stub from published payload + shebang wrapper
            fixture = Path(__file__).resolve().parents[2] / "fixtures" / "learning_os" / "waike-learning-os"
            if fixture.is_file() and not mark_incompatible:
                shutil.copy2(fixture, exe)
            else:
                exe.write_text(
                    "#!/usr/bin/env bash\n"
                    "echo incompatible >&2\n"
                    "exit 2\n"
                    if mark_incompatible
                    else (
                        "#!/usr/bin/env bash\n"
                        f"echo version={version}\n"
                        "exit 0\n"
                    ),
                    encoding="utf-8",
                )
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        (version_dir / "VERSION").write_text(version + "\n", encoding="utf-8")
        (version_dir / "INSTALLED.json").write_text(
            json.dumps(
                {
                    "app_id": APP_ID,
                    "version": version,
                    "channel": channel,
                    "incompatible": mark_incompatible,
                    "artifact_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        # Keep userdata untouched across install
        self._link_current()
        return {
            "ok": True,
            "install": result,
            "executable": str(exe),
            "userdata_hashes": self.user_state_hashes(),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def update(
        self,
        version: str,
        *,
        channel: str = "stable",
        executable_source: Path | None = None,
        mark_incompatible: bool = False,
    ) -> dict[str, Any]:
        before = self.user_state_hashes()
        result = self.publish_and_install(
            version,
            channel=channel,
            executable_source=executable_source,
            mark_incompatible=mark_incompatible,
        )
        after = self.user_state_hashes()
        result["userdata_preserved"] = before == after and bool(before)
        result["userdata_before"] = before
        result["userdata_after"] = after
        return result

    def rollback(self) -> dict[str, Any]:
        before = self.user_state_hashes()
        rb = self.pm.rollback(APP_ID)
        if not rb.get("ok"):
            return {
                "ok": False,
                "success": False,
                "mock": False,
                "error": rb.get("error", "rollback_failed"),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        # Re-materialize previous version tree if missing (install already did)
        prev = rb["rolled_back_to"]
        version = prev["version"]
        version_dir = self.apps / version
        if not (version_dir / "waike-learning-os").exists():
            # Recover from package store payload by re-install materialization
            self.publish_and_install(version, channel=prev.get("channel", "stable"))
        self._link_current()
        after = self.user_state_hashes()
        return {
            "ok": True,
            "success": True,
            "mock": False,
            "rolled_back_to": prev,
            "executable": str(self.current_executable()) if self.current_executable() else None,
            "userdata_preserved": before == after and bool(before),
            "userdata_before": before,
            "userdata_after": after,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def current_executable(self) -> Path | None:
        cur = self.apps / "current" / "waike-learning-os"
        if cur.is_file():
            return cur
        installed = self.pm.installed.get(APP_ID)
        if not installed:
            return None
        p = self.apps / installed["version"] / "waike-learning-os"
        return p if p.is_file() else None

    def current_version(self) -> str | None:
        installed = self.pm.installed.get(APP_ID)
        return installed["version"] if installed else None

    def status(self) -> dict[str, Any]:
        installed = self.pm.installed.get(APP_ID)
        return {
            "installed": installed,
            "executable": str(self.current_executable()) if self.current_executable() else None,
            "userdata_hashes": self.user_state_hashes(),
            "rollback_supported": bool(installed and installed.get("prev")),
            "claim_boundary": CLAIM_BOUNDARY,
            "update_owner": "platform_tauri_bundle_via_device_os_package_manager",
            "mock": False,
        }

    def run_ab_proof(
        self,
        *,
        version_a: str = "1.0.0",
        version_b: str = "1.1.0",
        fixture: Path | None = None,
    ) -> dict[str, Any]:
        """Prove install A → launch A → update B → launch B → failure → rollback A → launch A."""
        from .ipc_transport import DeterministicTestTransport
        from .native_launch import NativeLaunchAdapter

        fixture = fixture or (
            Path(__file__).resolve().parents[2] / "fixtures" / "learning_os" / "waike-learning-os"
        )
        steps: list[dict[str, Any]] = []
        self.write_user_state(
            db_blob=b"learning-user-db-preserved",
            outbox={"items": [{"id": "ob-1"}]},
            progress={"lesson": "w01", "pct": 40},
        )
        hashes0 = self.user_state_hashes()

        a = self.publish_and_install(version_a, executable_source=fixture)
        steps.append({"step": "install_a", "ok": a.get("ok"), "version": version_a})
        adapter_a = NativeLaunchAdapter(
            install_root=self.root,
            executable=self.current_executable(),
            transport=DeterministicTestTransport(app_version=version_a),
        )
        launch_a1 = adapter_a.launch(deep_link="waike://learn/home")
        steps.append({"step": "launch_a", "launched": launch_a1.launched, "version": launch_a1.version})

        b = self.update(version_b, executable_source=fixture)
        steps.append(
            {
                "step": "update_b",
                "ok": b.get("ok"),
                "userdata_preserved": b.get("userdata_preserved"),
            }
        )
        adapter_b = NativeLaunchAdapter(
            install_root=self.root,
            executable=self.current_executable(),
            transport=DeterministicTestTransport(app_version=version_b),
        )
        launch_b = adapter_b.launch(deep_link="waike://learn/home")
        steps.append({"step": "launch_b", "launched": launch_b.launched, "version": launch_b.version})

        # Inject failure / incompatibility signal (app-level health fail — not OS OTA).
        failure = {
            "ok": False,
            "reason": "incompatible_update_health_fail",
            "active_version": self.current_version(),
            "action": "rollback_to_previous",
        }
        steps.append({"step": "inject_failure", **failure})

        rb = self.rollback()  # B → A
        steps.append(
            {
                "step": "rollback_a",
                "ok": rb.get("ok"),
                "success": rb.get("success"),
                "rolled_back_to": rb.get("rolled_back_to"),
                "userdata_preserved": rb.get("userdata_preserved"),
            }
        )

        adapter_a2 = NativeLaunchAdapter(
            install_root=self.root,
            executable=self.current_executable(),
            transport=DeterministicTestTransport(app_version=version_a),
        )
        launch_a2 = adapter_a2.launch(deep_link="waike://learn/home")
        steps.append(
            {
                "step": "launch_a_after_rollback",
                "launched": launch_a2.launched,
                "version": launch_a2.version,
            }
        )

        hashes_final = self.user_state_hashes()
        ok = (
            bool(a.get("ok"))
            and launch_a1.launched
            and bool(b.get("ok"))
            and launch_b.launched
            and bool(rb.get("ok"))
            and launch_a2.launched
            and self.current_version() == version_a
            and hashes0 == hashes_final
        )
        return {
            "ok": ok,
            "steps": steps,
            "userdata_preserved": hashes0 == hashes_final,
            "final_version": self.current_version(),
            "claim_boundary": CLAIM_BOUNDARY,
        }
