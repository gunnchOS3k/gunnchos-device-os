"""Device Lab session lifecycle: start/stop with backends + fidelity."""
from __future__ import annotations

import json
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
            "SILICON_EXACT_EMULATION": SILICON_EXACT_EMULATION,
        }
        (self.work / "session.json").write_text(
            json.dumps({"instance_id": self.instance_id, "profile_id": self.profile_id, "state": self.state}, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "ok": True,
            "instance_id": self.instance_id,
            "profile_id": self.profile_id,
            "state": self.state,
            "fidelity": self.fidelity.to_dict(),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def stop(self) -> dict[str, Any]:
        self.network.cleanup()
        self.storage.reset()
        self.running = False
        _INSTANCES.pop(self.instance_id, None)
        return {"ok": True, "instance_id": self.instance_id, "stopped": True}

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
    work = work or (repo_root / "artifacts" / "device_lab" / "instances" / instance_id)
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


def get_session(instance_id: str) -> LabSession:
    if instance_id not in _INSTANCES:
        raise KeyError(instance_id)
    return _INSTANCES[instance_id]


def stop_session(instance_id: str) -> dict[str, Any]:
    return get_session(instance_id).stop()


def list_sessions() -> list[dict[str, Any]]:
    return [s.status() for s in _INSTANCES.values()]
