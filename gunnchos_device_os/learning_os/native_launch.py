"""Native Learning OS launch adapter — real process + IPC ack."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.app_registry import (
    LEARNING_OS_BUNDLE_ID,
    LEARNING_OS_REGISTRY_ID,
    LEARNING_OS_RUNTIME_ID,
    LEARNING_OS_SDK_APP_ID,
)

from .deep_link import parse_deep_link
from .ipc_protocol import build_launch_request
from .ipc_transport import FileIpcTransport, IpcTransport
from .provenance import build_provenance


@dataclass
class NativeLaunchResult:
    registered: bool = False
    available: bool = False
    handoff_created: bool = False
    launch_attempted: bool = False
    process_started: bool = False
    deep_link_delivered: bool = False
    acknowledged: bool = False
    launched: bool = False
    reason: str | None = None
    pid: int | None = None
    executable: str | None = None
    version: str | None = None
    artifact_hash: str | None = None
    ipc: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    mock: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NativeLaunchAdapter:
    """Discover + launch installed Learning OS native artifact via subprocess + IPC."""

    ENV_EXECUTABLE = "LEARNING_OS_EXECUTABLE"
    ENV_INSTALL_ROOT = "LEARNING_OS_INSTALL_ROOT"
    ENV_PLATFORM_SHA = "LEARNING_OS_PLATFORM_SHA"
    ENV_APP_VERSION = "LEARNING_OS_APP_VERSION"

    def __init__(
        self,
        *,
        install_root: Path | None = None,
        executable: Path | None = None,
        transport: IpcTransport | None = None,
        ipc_dir: Path | None = None,
        timeout_s: float = 5.0,
    ):
        self.install_root = Path(install_root) if install_root else self._default_install_root()
        self._explicit_executable = Path(executable) if executable else None
        self.timeout_s = timeout_s
        self.ipc_dir = Path(ipc_dir) if ipc_dir else Path(tempfile.mkdtemp(prefix="waike-los-ipc-"))
        self.transport = transport

    @staticmethod
    def _default_install_root() -> Path:
        env = os.environ.get(NativeLaunchAdapter.ENV_INSTALL_ROOT)
        if env:
            return Path(env)
        return Path(tempfile.gettempdir()) / "gunnchos-learning-os-install"

    def discover(self) -> dict[str, Any]:
        exe = self.resolve_executable()
        if exe is None:
            return {
                "available": False,
                "executable": None,
                "version": None,
                "artifact_hash": None,
                "reason": "learning_os_not_installed",
            }
        version = self._read_version(exe)
        digest = hashlib.sha256(exe.read_bytes()).hexdigest() if exe.is_file() else None
        return {
            "available": True,
            "executable": str(exe),
            "version": version,
            "artifact_hash": digest,
            "reason": None,
        }

    def resolve_executable(self) -> Path | None:
        if self._explicit_executable and self._explicit_executable.is_file():
            return self._explicit_executable
        env = os.environ.get(self.ENV_EXECUTABLE)
        if env:
            p = Path(env)
            if p.is_file() and os.access(p, os.X_OK):
                return p
        candidates = [
            self.install_root / "bin" / "waike-learning-os",
            self.install_root / "apps" / LEARNING_OS_BUNDLE_ID / "current" / "waike-learning-os",
            self.install_root / LEARNING_OS_BUNDLE_ID / "waike-learning-os",
        ]
        for c in candidates:
            if c.is_file() and os.access(c, os.X_OK):
                return c
        # Symlink "current" under package lifecycle layout
        current = self.install_root / "apps" / LEARNING_OS_BUNDLE_ID / "current"
        if current.is_symlink() or current.is_dir():
            for name in ("waike-learning-os", "learning-os", "app"):
                p = current / name
                if p.is_file() and os.access(p, os.X_OK):
                    return p
        return None

    def _read_version(self, exe: Path) -> str | None:
        env_ver = os.environ.get(self.ENV_APP_VERSION)
        if env_ver:
            return env_ver
        meta = exe.parent / "VERSION"
        if meta.is_file():
            return meta.read_text(encoding="utf-8").strip() or None
        marker = exe.parent / "INSTALLED.json"
        if marker.is_file():
            try:
                return json.loads(marker.read_text(encoding="utf-8")).get("version")
            except json.JSONDecodeError:
                return None
        return None

    def launch(
        self,
        *,
        deep_link: str | None = None,
        context: dict[str, Any] | None = None,
        profile: str = "student",
        mode: str = "School",
    ) -> NativeLaunchResult:
        result = NativeLaunchResult(registered=True)
        discovery = self.discover()
        result.available = bool(discovery["available"])
        result.executable = discovery.get("executable")
        result.version = discovery.get("version")
        result.artifact_hash = discovery.get("artifact_hash")
        result.provenance = build_provenance(
            app_version=result.version,
            artifact_hash=result.artifact_hash,
            platform_sha=os.environ.get(self.ENV_PLATFORM_SHA),
        )

        link = parse_deep_link(deep_link)
        if deep_link and not link.get("valid"):
            result.reason = "deep_link_rejected"
            result.ipc = {"deep_link": link}
            return result

        handoff = {
            "bundle_id": LEARNING_OS_BUNDLE_ID,
            "registry_id": LEARNING_OS_REGISTRY_ID,
            "sdk_app_id": LEARNING_OS_SDK_APP_ID,
            "runtime_id": LEARNING_OS_RUNTIME_ID,
            "deep_link": link if deep_link else parse_deep_link("waike://learn/home"),
            "context": context or {},
        }
        result.handoff_created = True

        if not result.available:
            result.reason = "learning_os_not_installed"
            return result

        assert result.executable is not None
        request_id = str(uuid.uuid4())
        ctx = {
            "profile": profile,
            "mode": mode,
            "registry_id": LEARNING_OS_REGISTRY_ID,
            "bundle_id": LEARNING_OS_BUNDLE_ID,
            "sdk_app_id": LEARNING_OS_SDK_APP_ID,
            "runtime_id": LEARNING_OS_RUNTIME_ID,
            **(context or {}),
        }
        request = build_launch_request(
            request_id=request_id,
            deep_link=handoff["deep_link"],
            context=ctx,
            bundle_id=LEARNING_OS_BUNDLE_ID,
        )

        result.launch_attempted = True
        env = os.environ.copy()
        env["LEARNING_OS_IPC_DIR"] = str(self.ipc_dir)
        env["LEARNING_OS_REQUEST_ID"] = request_id
        # Prefer headless ACK path in CI when the real Tauri binary supports it.
        # Does not replace validation/ACK code — skips webview only.
        if os.environ.get("WAIKE_CI_HEADLESS_UI") or os.environ.get("CI_HEADLESS_UI"):
            env["WAIKE_CI_HEADLESS_UI"] = os.environ.get("WAIKE_CI_HEADLESS_UI") or os.environ.get(
                "CI_HEADLESS_UI", "1"
            )
        deep_uri = (handoff["deep_link"] or {}).get("canonical") or deep_link or "waike://learn/home"

        log_dir = self.ipc_dir / "proc-logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout_f = open(log_dir / f"stdout-{request_id}.log", "w", encoding="utf-8")
            stderr_f = open(log_dir / f"stderr-{request_id}.log", "w", encoding="utf-8")
        except OSError:
            stdout_f = subprocess.DEVNULL
            stderr_f = subprocess.DEVNULL

        try:
            proc = subprocess.Popen(
                [
                    result.executable,
                    "--bundle-id",
                    LEARNING_OS_BUNDLE_ID,
                    "--deep-link",
                    deep_uri,
                    "--ipc-dir",
                    str(self.ipc_dir),
                    "--request-id",
                    request_id,
                ],
                env=env,
                stdout=stdout_f,
                stderr=stderr_f,
                text=True,
            )
        except OSError as exc:
            for fh in (stdout_f, stderr_f):
                if fh not in (subprocess.DEVNULL, None):
                    try:
                        fh.close()
                    except Exception:
                        pass
            result.reason = f"process_launch_error:{exc}"
            return result

        result.process_started = True
        result.pid = proc.pid

        # Always materialize the request for the native process/fixture, even when a
        # test transport is injected for ack semantics (keeps fixture from hanging).
        self.ipc_dir.mkdir(parents=True, exist_ok=True)
        (self.ipc_dir / f"request-{request_id}.json").write_text(
            json.dumps(request, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        transport = self.transport
        if transport is None:
            transport = FileIpcTransport(self.ipc_dir, receiver_present=True)

        time.sleep(0.05)

        ipc_result = transport.send_and_await_ack(
            request,
            timeout_s=self.timeout_s,
            expected_bundle_id=LEARNING_OS_BUNDLE_ID,
            expected_app_version=result.version,
        )
        result.ipc = {
            "protocol": request["protocol"],
            "request": {k: v for k, v in request.items() if k != "context"}
            | {"context_keys": sorted((request.get("context") or {}).keys())},
            "transport": type(transport).__name__,
            "result": {
                "ok": ipc_result.get("ok"),
                "reason": ipc_result.get("reason"),
                "replay": ipc_result.get("replay", False),
                "ack": ipc_result.get("ack"),
            },
        }

        exit_code = proc.poll()
        ack = ipc_result.get("ack") or {}
        if ipc_result.get("ok"):
            result.deep_link_delivered = True
            result.acknowledged = True
            result.launched = True
            result.reason = None
            if ack.get("app_version"):
                result.version = ack["app_version"]
            # Production: leave GUI running after ACK. CI must clean up explicitly.
            if os.environ.get("LEARNING_OS_CLEANUP_AFTER_ACK") == "1":
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
        else:
            result.deep_link_delivered = False
            result.acknowledged = False
            result.launched = False
            if exit_code is not None and exit_code != 0 and ipc_result.get("reason") == "timeout":
                result.reason = f"process_exited_before_ack:{exit_code}"
            else:
                result.reason = ipc_result.get("reason") or "ipc_ack_failed"
            # Best-effort terminate hung/failed process
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proc.kill()

        for fh in (stdout_f, stderr_f):
            if fh not in (subprocess.DEVNULL, None):
                try:
                    fh.close()
                except Exception:
                    pass

        return result
