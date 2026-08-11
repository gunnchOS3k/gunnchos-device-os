"""Device Lab session lifecycle: start/stop with backends + fidelity."""
from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY, SILICON_EXACT_EMULATION
from gunnchos_device_os.device_lab.fidelity import FidelityDashboard
from gunnchos_device_os.device_lab.hw_backends.audio import AudioBackend
from gunnchos_device_os.device_lab.hw_backends.camera import CameraBackend
from gunnchos_device_os.device_lab.hw_backends.display import DisplayBackend
from gunnchos_device_os.device_lab.hw_backends.input_backend import InputBackend
from gunnchos_device_os.device_lab.hw_backends.network import NetworkBackend
from gunnchos_device_os.device_lab.hw_backends.print_backend import PrintBackend
from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend
from gunnchos_device_os.device_lab.hw_backends.storage import StorageBackend
from gunnchos_device_os.device_lab.profiles import load_profile
from gunnchos_device_os.device_lab.virtualization.backend import select_backend


_INSTANCES: dict[str, "LabSession"] = {}
_QEMU_SESSIONS: dict[str, Any] = {}
# Explicit allowlist for approved lab work roots (e.g. pytest tmp_path).
# Host escape outside instances + registered roots remains denied (SEC-LAB-001).
_APPROVED_WORK_ROOTS: set[Path] = set()


def lab_artifact_root(repo_root: Path) -> Path:
    """Device Lab artifact root — override via GUNNCHDEVICE_LAB_ARTIFACT_ROOT for tests/CI."""
    override = os.environ.get("GUNNCHDEVICE_LAB_ARTIFACT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(repo_root) / "artifacts" / "device_lab").resolve()


def instances_root(repo_root: Path) -> Path:
    return lab_artifact_root(repo_root) / "instances"


def _is_under(path: Path, root: Path) -> bool:
    try:
        return path == root or path.is_relative_to(root)
    except (OSError, ValueError):
        return False


def lab_work_root_policy_ok(root: Path, *, repo_root: Path | None = None) -> bool:
    """Approve only controlled temp / Device Lab artifact trees — not host escape roots."""
    resolved = Path(root).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if _is_under(resolved, temp_root):
        return True
    if repo_root is not None and _is_under(resolved, lab_artifact_root(repo_root)):
        return True
    # Explicit override root (may live outside repo for sandboxed CI/tests).
    override = os.environ.get("GUNNCHDEVICE_LAB_ARTIFACT_ROOT", "").strip()
    if override and _is_under(resolved, Path(override).expanduser().resolve()):
        return True
    return False


def register_lab_work_root(root: Path, *, repo_root: Path | None = None) -> Path:
    """Register an approved session work root (unit tests / controlled lab temps)."""
    resolved = Path(root).resolve()
    if not lab_work_root_policy_ok(resolved, repo_root=repo_root):
        raise PermissionError("device_lab_work_root_not_approvable")
    _APPROVED_WORK_ROOTS.add(resolved)
    return resolved


def unregister_lab_work_root(root: Path) -> None:
    _APPROVED_WORK_ROOTS.discard(Path(root).resolve())


def clear_lab_work_roots() -> None:
    _APPROVED_WORK_ROOTS.clear()


def work_path_allowed(work: Path, *, repo_root: Path) -> bool:
    """True iff work is under default instances root or an explicitly registered root."""
    resolved = Path(work).resolve()
    if _is_under(resolved, instances_root(repo_root)):
        return True
    for approved in _APPROVED_WORK_ROOTS:
        if _is_under(resolved, approved):
            return True
    return False


@dataclass
class LabSession:
    instance_id: str
    profile_id: str
    profile: dict[str, Any]
    work: Path
    virt: dict[str, Any]
    repo_root: Path | None = None
    display: DisplayBackend = field(default_factory=DisplayBackend)
    storage: StorageBackend = field(default_factory=lambda: StorageBackend(Path(".")))
    network: NetworkBackend = field(default_factory=NetworkBackend)
    audio: AudioBackend = field(default_factory=AudioBackend)
    input: InputBackend = field(default_factory=InputBackend)
    camera: CameraBackend = field(default_factory=CameraBackend)
    printer: PrintBackend = field(default_factory=PrintBackend)
    rings: RingsBackend = field(default_factory=RingsBackend)
    fidelity: FidelityDashboard = field(default_factory=FidelityDashboard)
    started_at: float = 0.0
    running: bool = False
    state: dict[str, Any] = field(default_factory=dict)

    def start(self) -> dict[str, Any]:
        self.work.mkdir(parents=True, exist_ok=True)
        disp = self.display.start(self.profile)
        stor = self.storage.start(self.profile, self.work)
        net = self.network.start()
        aud = self.audio.start()
        cam = self.camera.start()
        # Rings only when profile or companion asks
        rings_info = None
        if self.profile_id in {"edge_io_rings", "full_ecosystem"} or self.profile.get("ring_capabilities", {}).get("supported"):
            rings_ev = self.work / "rings"
            rings_info = self.rings.start(evidence_dir=rings_ev, repo_root=self.repo_root)
        qemu_info = None
        selected = (self.virt.get("selected") or {})
        backend_name = selected.get("name") or ""
        prefer_qemu = backend_name.startswith("QEMU_") or bool(self.virt.get("prefer_real_guest"))
        if prefer_qemu and self.repo_root is not None:
            from gunnchos_device_os.device_lab.virtualization.qemu_guest import start_qemu_guest

            q = start_qemu_guest(
                work=self.work / "qemu",
                profile=self.profile,
                repo_root=self.repo_root,
                headless=True,
            )
            sess_obj = q.pop("_session", None)
            if sess_obj is not None:
                _QEMU_SESSIONS[self.instance_id] = sess_obj
            qemu_info = q
            # Merge real guest dual outputs into display honesty plane when present
            gout = ((q.get("state") or {}).get("guest_outputs")) or (
                (q.get("state") or {}).get("display_transport") or {}
            ).get("guest_outputs")
            if gout and len(gout) >= 2:
                self.display.outputs = list(gout)
                self.display.backend_name = "qemu_virtio_gpu"
            # If QEMU was required and skipped/failed, surface honestly (do not fake PASS).
            if not q.get("ok") and q.get("SKIPPED_ENVIRONMENT"):
                self.state = {
                    "display": disp,
                    "storage": stor,
                    "network": net,
                    "audio": aud,
                    "camera": cam,
                    "rings": rings_info,
                    "virtualization": self.virt,
                    "qemu": qemu_info,
                    "SILICON_EXACT_EMULATION": SILICON_EXACT_EMULATION,
                    "result": "SKIPPED_ENVIRONMENT",
                }
                (self.work / "session.json").write_text(
                    json.dumps(
                        {
                            "instance_id": self.instance_id,
                            "profile_id": self.profile_id,
                            "state": self.state,
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return {
                    "ok": False,
                    "instance_id": self.instance_id,
                    "profile_id": self.profile_id,
                    "state": self.state,
                    "result": "SKIPPED_ENVIRONMENT",
                    "SKIPPED_ENVIRONMENT": True,
                    "fidelity": self.fidelity.to_dict(),
                    "claim_boundary": CLAIM_BOUNDARY,
                    "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
                }
        self.started_at = time.time()
        self.running = True
        self.state = {
            "display": disp,
            "storage": stor,
            "network": net,
            "audio": aud,
            "camera": cam,
            "rings": rings_info,
            "virtualization": self.virt,
            "qemu": qemu_info,
            "SILICON_EXACT_EMULATION": SILICON_EXACT_EMULATION,
        }
        (self.work / "session.json").write_text(
            json.dumps({"instance_id": self.instance_id, "profile_id": self.profile_id, "state": self.state}, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "ok": True if (qemu_info is None or qemu_info.get("ok")) else False,
            "instance_id": self.instance_id,
            "profile_id": self.profile_id,
            "state": self.state,
            "fidelity": self.fidelity.to_dict(),
            "claim_boundary": CLAIM_BOUNDARY,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        }

    def stop(self) -> dict[str, Any]:
        q = _QEMU_SESSIONS.pop(self.instance_id, None)
        qemu_stop = None
        if q is not None:
            qemu_stop = q.stop()
        self.network.cleanup()
        self.storage.reset()
        self.running = False
        _INSTANCES.pop(self.instance_id, None)
        return {
            "ok": True,
            "instance_id": self.instance_id,
            "stopped": True,
            "qemu": qemu_stop,
        }

    def status(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "profile_id": self.profile_id,
            "running": self.running,
            "uptime_s": (time.time() - self.started_at) if self.running else 0,
            "display_outputs": self.display.outputs,
            "network": {"state": self.network.state, "ethernet_via_dock": self.network.ethernet_via_dock},
            "audio_route": self.audio.route,
            "fidelity": self.fidelity.to_dict(),
            "claim_boundary": CLAIM_BOUNDARY,
        }


def start_session(profile_id: str, *, repo_root: Path, work: Path | None = None) -> dict[str, Any]:
    profile = load_profile(profile_id)
    virt = select_backend()
    instance_id = f"dev-{uuid.uuid4().hex[:8]}"
    base = instances_root(repo_root)
    work = work or (base / instance_id)
    work = work.resolve()
    # SEC-LAB: refuse path escape outside instances root or registered lab work roots.
    if not work_path_allowed(work, repo_root=repo_root):
        raise PermissionError("device_lab_work_path_escape")
    sess = LabSession(
        instance_id=instance_id,
        profile_id=profile_id,
        profile=profile,
        work=work,
        virt=virt,
        repo_root=repo_root,
    )
    _INSTANCES[instance_id] = sess
    return sess.start()


def get_qemu_session(instance_id: str) -> Any | None:
    return _QEMU_SESSIONS.get(instance_id)


def get_session(instance_id: str) -> LabSession:
    if instance_id not in _INSTANCES:
        raise KeyError(instance_id)
    return _INSTANCES[instance_id]


def stop_session(instance_id: str) -> dict[str, Any]:
    return get_session(instance_id).stop()


def list_sessions() -> list[dict[str, Any]]:
    return [s.status() for s in _INSTANCES.values()]
