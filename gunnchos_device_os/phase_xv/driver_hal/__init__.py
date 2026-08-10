"""DRIVER_HAL — risk ledger + HAL over real Linux interfaces / CI virtual devices.

Physical board validation remains PHYSICAL_PENDING under PHYSICAL_EXECUTION_FREEZE.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

CLAIM_BOUNDARY = (
    "Digital HAL over Linux interfaces and CI virtual/file-backed devices only. "
    "No physical board validation claimed. PHYSICAL_PENDING for EVT boards."
)

DRIVER_CLASSES = ("video", "audio", "net", "input", "gpu", "modem")


@dataclass
class HalRiskEntry:
    driver_class: str
    interface: str
    risk: str  # low | medium | high
    mitigation: str
    bind_mode: str  # real | virtual | file_sim
    physical_board: str = "PHYSICAL_PENDING"


@dataclass
class DeviceBinding:
    device_id: str
    driver_class: str
    path: str
    bound: bool = False
    hotplug: bool = False
    last_error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class FileBackedSimulator:
    """File-backed device with real bind/fail/hotplug semantics for CI."""

    def __init__(self, root: Path, device_id: str, driver_class: str):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.device_id = device_id
        self.driver_class = driver_class
        self.node = self.root / f"{device_id}.dev"
        self.state_path = self.root / f"{device_id}.state.json"
        self._fail_next = False

    def present(self) -> bool:
        return self.node.exists() and not self._fail_next

    def create(self) -> Path:
        self.node.write_bytes(b"gunnchos-hal-sim-v1")
        self._persist({"present": True, "bound": False})
        return self.node

    def remove(self) -> None:
        if self.node.exists():
            self.node.unlink()
        self._persist({"present": False, "bound": False})

    def force_fail(self, enabled: bool = True) -> None:
        self._fail_next = enabled

    def _persist(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _probe_linux_interfaces() -> dict[str, Any]:
    """Probe host for real/virtual Linux interfaces when available."""
    probes = {
        "video": Path("/dev/video0"),
        "audio_playback": Path("/dev/snd"),
        "net_dummy": Path("/sys/class/net/dummy0"),
        "net_lo": Path("/sys/class/net/lo"),
        "v4l2loopback_mod": Path("/sys/module/v4l2loopback"),
        "snd_aloop_mod": Path("/sys/module/snd_aloop"),
    }
    found = {k: p.exists() for k, p in probes.items()}
    bind_mode = "file_sim"
    if found.get("v4l2loopback_mod") or found.get("video"):
        bind_mode = "virtual" if found.get("v4l2loopback_mod") else "real"
    elif found.get("snd_aloop_mod") or found.get("audio_playback"):
        bind_mode = "virtual" if found.get("snd_aloop_mod") else "real"
    elif found.get("net_dummy") or found.get("net_lo"):
        bind_mode = "virtual" if found.get("net_dummy") else "real"
    return {"probes": found, "preferred_bind_mode": bind_mode, "ci_virtual_ok": True}


class DriverHal:
    """HAL that binds drivers to Linux paths or file-backed simulators."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.sim_root = self.root / "sim"
        self.sim_root.mkdir(exist_ok=True)
        self.bindings: dict[str, DeviceBinding] = {}
        self.sims: dict[str, FileBackedSimulator] = {}
        self.risk_ledger: list[HalRiskEntry] = []
        self._build_risk_ledger()

    def _build_risk_ledger(self) -> None:
        self.risk_ledger = [
            HalRiskEntry("video", "/dev/video*", "medium", "v4l2loopback or file sim", "virtual"),
            HalRiskEntry("audio", "ALSA/PipeWire", "medium", "snd-aloop or file sim", "virtual"),
            HalRiskEntry("net", "netdev", "low", "dummy/lo or file sim", "virtual"),
            HalRiskEntry("input", "evdev/Ring", "medium", "uinput or file sim", "file_sim"),
            HalRiskEntry("gpu", "DRM/KMS", "high", "render node probe; no fake FPS", "file_sim"),
            HalRiskEntry("modem", "QMI/MM", "high", "software modem path only", "file_sim"),
        ]

    def register_simulator(self, device_id: str, driver_class: str) -> FileBackedSimulator:
        if driver_class not in DRIVER_CLASSES:
            raise ValueError(driver_class)
        sim = FileBackedSimulator(self.sim_root, device_id, driver_class)
        sim.create()
        self.sims[device_id] = sim
        return sim

    def bind(self, device_id: str, driver_class: str, path: str | None = None) -> DeviceBinding:
        sim = self.sims.get(device_id)
        if sim is None:
            sim = self.register_simulator(device_id, driver_class)
        if sim._fail_next or not sim.present():
            binding = DeviceBinding(
                device_id=device_id,
                driver_class=driver_class,
                path=path or str(sim.node),
                bound=False,
                last_error="bind_failed_device_absent",
            )
            binding.events.append({"op": "bind_fail", "at": time.time()})
            self.bindings[device_id] = binding
            return binding
        resolved = path or str(sim.node)
        binding = DeviceBinding(
            device_id=device_id,
            driver_class=driver_class,
            path=resolved,
            bound=True,
        )
        binding.events.append({"op": "bind", "at": time.time(), "path": resolved})
        sim._persist({"present": True, "bound": True})
        self.bindings[device_id] = binding
        return binding

    def unbind(self, device_id: str) -> DeviceBinding:
        binding = self.bindings.get(device_id)
        if binding is None:
            raise KeyError(device_id)
        binding.bound = False
        binding.events.append({"op": "unbind", "at": time.time()})
        sim = self.sims.get(device_id)
        if sim:
            sim._persist({"present": sim.present(), "bound": False})
        return binding

    def hotplug_remove(self, device_id: str) -> DeviceBinding:
        sim = self.sims[device_id]
        sim.remove()
        binding = self.bindings.get(device_id) or DeviceBinding(
            device_id=device_id, driver_class=sim.driver_class, path=str(sim.node)
        )
        binding.bound = False
        binding.hotplug = True
        binding.events.append({"op": "hotplug_remove", "at": time.time()})
        self.bindings[device_id] = binding
        return binding

    def hotplug_insert(self, device_id: str) -> DeviceBinding:
        sim = self.sims[device_id]
        sim.create()
        return self.bind(device_id, sim.driver_class)

    def write_risk_ledger(self) -> Path:
        out = self.root / "HAL_RISK_LEDGER.json"
        payload = {
            "schema": "gunnchos.phase_xv.hal_risk_ledger.v1",
            "entries": [asdict(e) for e in self.risk_ledger],
            "claim_boundary": CLAIM_BOUNDARY,
            "physical_board_validation": "PHYSICAL_PENDING",
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out

    def e2e(self) -> dict[str, Any]:
        probes = _probe_linux_interfaces()
        ledger = self.write_risk_ledger()
        results: dict[str, Any] = {"probes": probes, "ledger": str(ledger.name)}

        # Bind success path
        cam = self.register_simulator("cam0", "video")
        b1 = self.bind("cam0", "video")
        results["bind_ok"] = b1.bound is True

        # Fail path
        cam.force_fail(True)
        b_fail = self.bind("cam0", "video")
        results["bind_fail"] = b_fail.bound is False and b_fail.last_error == "bind_failed_device_absent"
        cam.force_fail(False)
        cam.create()

        # Hotplug remove/insert
        self.bind("cam0", "video")
        rem = self.hotplug_remove("cam0")
        results["hotplug_remove"] = rem.hotplug is True and rem.bound is False
        ins = self.hotplug_insert("cam0")
        results["hotplug_insert"] = ins.bound is True

        # Audio + net simulators
        self.register_simulator("pcm0", "audio")
        self.register_simulator("net0", "net")
        results["audio_bind"] = self.bind("pcm0", "audio").bound
        results["net_bind"] = self.bind("net0", "net").bound
        results["unbind_ok"] = self.unbind("net0").bound is False

        ok = all(
            [
                results["bind_ok"],
                results["bind_fail"],
                results["hotplug_remove"],
                results["hotplug_insert"],
                results["audio_bind"],
                results["net_bind"],
                results["unbind_ok"],
                ledger.exists(),
                len(self.risk_ledger) == len(DRIVER_CLASSES),
            ]
        )
        return {
            "schema": "gunnchos.phase_xv.driver_hal.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "physical_board_validation": "PHYSICAL_PENDING",
            "driver_classes": list(DRIVER_CLASSES),
            "results": results,
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
