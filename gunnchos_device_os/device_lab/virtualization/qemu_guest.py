"""Real QEMU guest lifecycle for gunnchDevice Lab.

Prefers HVF (macOS) / KVM (Linux) / TCG fallback. Never claims silicon-exact SoC.
Headless mode for CI. Display transport: VNC (and SPICE when available) — not screenshot-only fakes.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient
from gunnchos_device_os.device_lab.image_builder import LabGuestImageBuilder


CLAIM = (
    "QEMU virt machine ≠ transistor-level SoC. SILICON_EXACT_EMULATION=false. "
    "VF4/VF5/VF6 PHYSICAL_PENDING. Measurement classes: HOST_OBSERVED for host "
    "process liveness; VIRTUAL_CONSTRAINED for guest RAM/disk caps."
)


def qemu_system_bin(*, prefer_arch: str | None = None) -> tuple[str, str]:
    """Return (binary_path, arch_label). Prefer host-native arch for acceleration."""
    machine = platform.machine().lower()
    host = platform.system()
    prefer = prefer_arch or os.environ.get("GUNNCHDEVICE_LAB_QEMU_ARCH")
    if not prefer:
        if machine in {"arm64", "aarch64"}:
            prefer = "aarch64"
        else:
            prefer = "x86_64"
    candidates = {
        "aarch64": ["qemu-system-aarch64", "/opt/homebrew/bin/qemu-system-aarch64"],
        "x86_64": ["qemu-system-x86_64", "/opt/homebrew/bin/qemu-system-x86_64"],
    }
    order = [prefer] + [a for a in ("aarch64", "x86_64") if a != prefer]
    for arch in order:
        for c in candidates[arch]:
            if "/" in c:
                if Path(c).exists():
                    return c, arch
            else:
                which = shutil.which(c)
                if which:
                    return which, arch
    raise FileNotFoundError("qemu-system-aarch64/x86_64 not found")


def select_accel(arch: str) -> dict[str, Any]:
    host = platform.system()
    machine = platform.machine().lower()
    if host == "Darwin":
        # HVF works for same-arch guests on Apple Silicon / Intel Macs.
        same = (arch == "aarch64" and machine in {"arm64", "aarch64"}) or (
            arch == "x86_64" and machine in {"x86_64", "amd64"}
        )
        if same:
            return {"accel": "hvf", "cpu": "host", "note": "macOS Hypervisor.framework"}
        return {"accel": "tcg", "cpu": "max", "note": "cross-arch TCG on macOS"}
    if host == "Linux" and Path("/dev/kvm").exists():
        same = (arch == "aarch64" and machine in {"aarch64", "arm64"}) or (
            arch == "x86_64" and machine in {"x86_64", "amd64"}
        )
        if same:
            return {"accel": "kvm", "cpu": "host", "note": "Linux KVM"}
    return {"accel": "tcg", "cpu": "max", "note": "TCG software emulation"}


@dataclass
class QemuGuestSession:
    work: Path
    profile: dict[str, Any]
    repo_root: Path
    headless: bool = True
    memory_mb: int = 1024
    smp: int = 2
    persist_disk_gb: int = 4
    proc: subprocess.Popen[str] | None = None
    qemu_bin: str = ""
    arch: str = ""
    accel: dict[str, Any] = field(default_factory=dict)
    boot_log: Path | None = None
    pid_file: Path | None = None
    agent: GuestAgentClient | None = None
    display_transport: dict[str, Any] = field(default_factory=dict)
    started_at: float = 0.0
    boot_complete: bool = False
    state: dict[str, Any] = field(default_factory=dict)

    def _resolve_images(self) -> tuple[Path, Path]:
        builder = LabGuestImageBuilder(self.repo_root)
        inspect = builder.inspect()
        if not inspect.get("ok"):
            # Attempt build without network if cache present
            try:
                builder.build(fetch=False)
            except Exception:
                builder.build(fetch=True)
        kernel = builder.artifacts / "vmlinuz-virt"
        initrd = builder.artifacts / "gunnchos-ref-initramfs.cpio.gz"
        if not kernel.exists() or not initrd.exists():
            # Fall back to bootable_reference artifacts
            ref = self.repo_root / "os_build" / "bootable_reference" / "artifacts"
            kernel = ref / "vmlinuz-virt"
            initrd = ref / "gunnchos-ref-initramfs.cpio.gz"
        if not kernel.exists() or not initrd.exists():
            raise FileNotFoundError(
                "Lab/bootable reference kernel+initramfs missing; run gunnchctl image build"
            )
        return kernel, initrd

    def _ensure_persist_disk(self) -> Path:
        disk = self.work / "persist.qcow2"
        if disk.exists():
            return disk
        qemu_img = shutil.which("qemu-img") or "/opt/homebrew/bin/qemu-img"
        if not Path(qemu_img).exists():
            # Raw fallback
            raw = self.work / "persist.raw"
            with raw.open("wb") as fh:
                fh.truncate(self.persist_disk_gb * 1024 * 1024 * 1024)
            return raw
        subprocess.run(
            [qemu_img, "create", "-f", "qcow2", str(disk), f"{self.persist_disk_gb}G"],
            check=True,
            capture_output=True,
            text=True,
        )
        return disk

    def start(self) -> dict[str, Any]:
        self.work.mkdir(parents=True, exist_ok=True)
        self.qemu_bin, self.arch = qemu_system_bin()
        self.accel = select_accel(self.arch)
        kernel, initrd = self._resolve_images()
        disk = self._ensure_persist_disk()
        self.boot_log = self.work / "qemu_boot.log"
        self.pid_file = self.work / "qemu.pid"
        agent_mailbox = self.work / "guest_agent.mailbox"
        vnc_port = int(os.environ.get("GUNNCHDEVICE_LAB_VNC_PORT", "0"))  # 0 => display :7 -> 5907

        machine = "virt" if self.arch == "aarch64" else "q35"
        cmd = [
            self.qemu_bin,
            "-machine",
            f"{machine},accel={self.accel['accel']}",
            "-cpu",
            self.accel["cpu"],
            "-smp",
            str(self.smp),
            "-m",
            str(self.memory_mb),
            "-kernel",
            str(kernel),
            "-initrd",
            str(initrd),
            "-append",
            (
                "console=ttyAMA0 earlyprintk=serial rdinit=/init panic=1 "
                "gunnchos.lab_persist=1 gunnchos.guest_agent=1"
                if self.arch == "aarch64"
                else "console=ttyS0 rdinit=/init panic=1 gunnchos.lab_persist=1 gunnchos.guest_agent=1"
            ),
            "-drive",
            f"file={disk},if=virtio,format={'qcow2' if disk.suffix == '.qcow2' else 'raw'}",
            "-serial",
            f"file:{self.boot_log}",
            "-pidfile",
            str(self.pid_file),
            "-daemonize",
            "-monitor",
            "none",
            # No user-net broad exposure by default — restrict to localhost usernet if enabled.
        ]
        # Optional usernet localhost-only (off by default)
        if os.environ.get("GUNNCHDEVICE_LAB_USERNET", "").lower() in {"1", "true", "yes"}:
            cmd += ["-netdev", "user,id=n0,restrict=on", "-device", "virtio-net-device,netdev=n0"]

        # Display transport scaffolding (real VNC path — not fake screenshots)
        # Note: QEMU forbids combining -nographic with -daemonize; use -display none instead.
        display_mode = os.environ.get("GUNNCHDEVICE_LAB_DISPLAY", "vnc" if not self.headless else "none")
        if self.headless or display_mode == "none":
            cmd += ["-display", "none"]
            self.display_transport = {
                "kind": "none_headless",
                "note": "Headless CI/default; set GUNNCHDEVICE_LAB_DISPLAY=vnc for VNC",
                "fake_screenshot_only": False,
            }
        elif display_mode == "spice":
            spice_addr = f"127.0.0.1:{5900 + (vnc_port or 8)}"
            cmd += ["-display", "none", "-spice", f"addr=127.0.0.1,port={5900 + (vnc_port or 8)},disable-ticketing=on"]
            self.display_transport = {
                "kind": "spice",
                "listen": spice_addr,
                "novnc_path": "scaffold",
                "fake_screenshot_only": False,
                "note": "SPICE localhost-only; noVNC UI polish later",
            }
        else:
            # VNC display :N => port 5900+N; bind localhost
            disp = vnc_port or 7
            cmd += ["-display", "none", "-vnc", f"127.0.0.1:{disp}"]
            self.display_transport = {
                "kind": "vnc",
                "listen": f"127.0.0.1:{5900 + disp}",
                "novnc_path": "scaffold",
                "fake_screenshot_only": False,
                "note": "VNC localhost-only; wire noVNC proxy in follow-up UI PR",
            }

        # Record command for evidence
        (self.work / "qemu_cmd.json").write_text(
            json.dumps({"cmd": cmd, "accel": self.accel, "arch": self.arch}, indent=2) + "\n",
            encoding="utf-8",
        )

        # daemonize: QEMU forks; parent exits 0 quickly
        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            return {
                "ok": False,
                "error": "qemu_exec_failed",
                "detail": str(exc),
                "SKIPPED_ENVIRONMENT": False,
                "SILICON_EXACT_EMULATION": False,
            }

        if completed.returncode != 0:
            return {
                "ok": False,
                "error": "qemu_start_failed",
                "stderr": completed.stderr,
                "stdout": completed.stdout,
                "cmd": cmd,
                "SILICON_EXACT_EMULATION": False,
            }

        # Wait for pidfile
        pid = None
        for _ in range(50):
            if self.pid_file.exists():
                try:
                    pid = int(self.pid_file.read_text(encoding="utf-8").strip())
                    break
                except ValueError:
                    pass
            time.sleep(0.1)
        if pid is None or not _pid_alive(pid):
            return {
                "ok": False,
                "error": "qemu_pid_missing",
                "stderr": completed.stderr,
                "SILICON_EXACT_EMULATION": False,
            }

        self.started_at = time.time()
        # Guest agent: prefer mailbox until virtio-serial wired in later PR; still real QEMU process.
        self.agent = GuestAgentClient(agent_mailbox, timeout_sec=5.0)
        # Disable host stub if we can observe boot markers (still HOST_OBSERVED readiness)
        agent_status = self._poll_boot_and_agent(timeout_sec=float(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "90")))

        self.state = {
            "backend": f"QEMU_{self.accel['accel'].upper()}",
            "qemu_bin": self.qemu_bin,
            "qemu_version": _qemu_version(self.qemu_bin),
            "arch": self.arch,
            "accel": self.accel,
            "pid": pid,
            "boot_log": str(self.boot_log),
            "persist_disk": str(disk),
            "display_transport": self.display_transport,
            "guest_agent": agent_status,
            "SILICON_EXACT_EMULATION": False,
            "claim_boundary": CLAIM,
            "measurement_class_process": "HOST_OBSERVED",
        }
        (self.work / "qemu_session.json").write_text(json.dumps(self.state, indent=2) + "\n", encoding="utf-8")
        return {
            "ok": True,
            "qemu_alive": _pid_alive(pid),
            "state": self.state,
            "boot_complete": self.boot_complete,
            "SILICON_EXACT_EMULATION": False,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        }

    def _poll_boot_and_agent(self, *, timeout_sec: float) -> dict[str, Any]:
        deadline = time.time() + timeout_sec
        markers: list[str] = []
        while time.time() < deadline:
            if self.boot_log and self.boot_log.exists():
                text = self.boot_log.read_text(encoding="utf-8", errors="replace")
                if "GUNNCHOS_BOOT_COMPLETE=true" in text or "GUNNCHOS_BOOT_MARKER=OK" in text:
                    self.boot_complete = True
                    markers.append("boot_complete_marker")
                    break
                if "GUNNCHOS_BOOT_STAGE=" in text:
                    markers.append("boot_progress")
            time.sleep(0.5)
        # Always exercise guest agent path (mailbox stub until in-guest agent answers)
        assert self.agent is not None
        ready = self.agent.wait_ready(timeout_sec=min(10.0, timeout_sec))
        return {
            "ready": bool(ready.get("ready")),
            "boot_complete_observed": self.boot_complete,
            "markers": markers,
            "agent_response": ready,
            "measurement_class": "HOST_OBSERVED",
            "note": (
                "Boot markers from QEMU serial file; agent may use host mailbox stub "
                "until virtio-serial guest daemon is linked in-guest"
            ),
        }

    def stop(self) -> dict[str, Any]:
        pid = None
        if self.pid_file and self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = None
        if pid and _pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
            for _ in range(30):
                if not _pid_alive(pid):
                    break
                time.sleep(0.1)
            if _pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        return {"ok": True, "stopped_pid": pid, "alive": bool(pid and _pid_alive(pid))}

    def status(self) -> dict[str, Any]:
        pid = None
        if self.pid_file and self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = None
        return {
            "qemu_alive": bool(pid and _pid_alive(pid)),
            "pid": pid,
            "boot_complete": self.boot_complete,
            "display_transport": self.display_transport,
            "accel": self.accel,
            "SILICON_EXACT_EMULATION": False,
            "uptime_s": (time.time() - self.started_at) if self.started_at else 0,
        }


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _qemu_version(bin_path: str) -> str:
    try:
        out = subprocess.run([bin_path, "--version"], capture_output=True, text=True, check=False)
        return (out.stdout or out.stderr or "").splitlines()[0] if (out.stdout or out.stderr) else "unknown"
    except OSError:
        return "unknown"


def environment_can_run_qemu() -> dict[str, Any]:
    try:
        bin_path, arch = qemu_system_bin()
        accel = select_accel(arch)
        return {
            "ok": True,
            "qemu_bin": bin_path,
            "arch": arch,
            "accel": accel,
            "version": _qemu_version(bin_path),
            "SKIPPED_ENVIRONMENT": False,
        }
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "SKIPPED_ENVIRONMENT": True,
            "note": "QEMU not installed — tests must not claim PASS",
        }


def start_qemu_guest(
    *,
    work: Path,
    profile: dict[str, Any],
    repo_root: Path,
    headless: bool = True,
) -> dict[str, Any]:
    env = environment_can_run_qemu()
    if not env.get("ok"):
        return {
            "ok": False,
            "SKIPPED_ENVIRONMENT": True,
            "environment": env,
            "SILICON_EXACT_EMULATION": False,
            # Explicitly not PASS
            "result": "SKIPPED_ENVIRONMENT",
        }
    # Cap guest RAM below physical profile to avoid host OOM in Lab (VIRTUAL_CONSTRAINED)
    profile_ram = ((profile.get("ram") or {}).get("gb")) or 2
    memory_mb = min(int(profile_ram) * 1024, int(os.environ.get("GUNNCHDEVICE_LAB_MEMORY_MB", "2048")))
    sess = QemuGuestSession(
        work=work,
        profile=profile,
        repo_root=repo_root,
        headless=headless,
        memory_mb=max(512, memory_mb),
    )
    result = sess.start()
    result["environment"] = env
    result["_session"] = sess
    return result
