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

# WP-011R: env flag(s) that select the Interactive Development Guest
# (persistent qcow2 root disk + virtio-gpu/keyboard/tablet) instead of (in
# addition to) the slim initramfs-only DEVICE_LAB_DEVELOPMENT_GUEST path.
# See os_build/device_lab_interactive_guest/README.md.
INTERACTIVE_GUEST_ENV_VARS = (
    "GUNNCH_LAB_INTERACTIVE_GUEST",
    "GUNNCHDEVICE_LAB_INTERACTIVE_GUEST",
)


def interactive_guest_enabled() -> bool:
    return any(
        (os.environ.get(name) or "").strip().lower() in {"1", "true", "yes"}
        for name in INTERACTIVE_GUEST_ENV_VARS
    )


def interactive_guest_disk_path(repo_root: Path, *, arch: str = "aarch64") -> Path:
    """Path QEMU recognizes as the Interactive Guest's persistent root disk.

    Recognition only — does not create or populate the disk. Use
    InteractiveGuestImageBuilder.create_disk_placeholder() (or the real
    rootfs build script) to materialize it first.
    """
    return (
        repo_root
        / "os_build"
        / "device_lab_interactive_guest"
        / "artifacts"
        / f"interactive-root-{arch}.qcow2"
    )


CLAIM = (
    "QEMU virt machine ≠ transistor-level SoC. SILICON_EXACT_EMULATION=false. "
    "VF4/VF5/VF6 PHYSICAL_PENDING. Measurement classes: HOST_OBSERVED for host "
    "process liveness; VIRTUAL_CONSTRAINED for guest RAM/disk caps."
)


def lab_guest_image_arch(repo_root: Path | None = None) -> str:
    """Lab/bootable reference guest is Alpine aarch64 — never boot it under x86_64 QEMU."""
    forced = (os.environ.get("GUNNCHDEVICE_LAB_QEMU_ARCH") or "").strip().lower()
    if forced in {"aarch64", "x86_64"}:
        return forced
    root = repo_root or Path(__file__).resolve().parents[3]
    for manifest in (
        root / "os_build" / "device_lab_guest" / "artifacts" / "LAB_GUEST_MANIFEST.json",
        root / "os_build" / "bootable_reference" / "artifacts" / "MANIFEST.json",
    ):
        if not manifest.exists():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            arch = ((data.get("target") or {}).get("arch")) or (
                (data.get("upstream_bootable_reference") or {}).get("arch")
            )
            if arch in {"aarch64", "x86_64"}:
                return str(arch)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    # SoT for Lab guest image builder is Alpine aarch64.
    return "aarch64"


def qemu_system_bin(*, prefer_arch: str | None = None, repo_root: Path | None = None) -> tuple[str, str]:
    """Return (binary_path, arch_label). Prefer guest-image arch (aarch64), not host-native.

    CI x86 runners previously selected qemu-system-x86_64 against an aarch64
    initramfs → 'linux kernel too old to load a ram disk'. Match the image.
    """
    prefer = prefer_arch or lab_guest_image_arch(repo_root)
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


def _kvm_usable() -> bool:
    """True only when /dev/kvm exists *and* is openable (CI often has KVM present but denied)."""
    kvm = Path("/dev/kvm")
    if not kvm.exists():
        return False
    try:
        fd = os.open(str(kvm), os.O_RDWR)
        os.close(fd)
        return True
    except OSError:
        return False


def select_accel(arch: str) -> dict[str, Any]:
    host = platform.system()
    machine = platform.machine().lower()
    force = (os.environ.get("GUNNCHDEVICE_LAB_ACCEL") or "").strip().lower()
    if force in {"tcg", "hvf", "kvm"}:
        cpu = "host" if force in {"hvf", "kvm"} else "max"
        return {"accel": force, "cpu": cpu, "note": f"forced via GUNNCHDEVICE_LAB_ACCEL={force}"}
    if host == "Darwin":
        # HVF works for same-arch guests on Apple Silicon / Intel Macs.
        same = (arch == "aarch64" and machine in {"arm64", "aarch64"}) or (
            arch == "x86_64" and machine in {"x86_64", "amd64"}
        )
        if same:
            return {"accel": "hvf", "cpu": "host", "note": "macOS Hypervisor.framework"}
        return {"accel": "tcg", "cpu": "max", "note": "cross-arch TCG on macOS"}
    if host == "Linux" and _kvm_usable():
        same = (arch == "aarch64" and machine in {"aarch64", "arm64"}) or (
            arch == "x86_64" and machine in {"x86_64", "amd64"}
        )
        if same:
            return {"accel": "kvm", "cpu": "host", "note": "Linux KVM"}
        return {"accel": "tcg", "cpu": "max", "note": "TCG (KVM present but cross-arch)"}
    if host == "Linux" and Path("/dev/kvm").exists() and not _kvm_usable():
        return {
            "accel": "tcg",
            "cpu": "max",
            "note": "TCG fallback — /dev/kvm present but permission denied",
        }
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
    monitor_sock: Path | None = None
    virtio_serial_sock: Path | None = None
    live_display: Any = None
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
        self.qemu_bin, self.arch = qemu_system_bin(repo_root=self.repo_root)
        self.accel = select_accel(self.arch)
        kernel, initrd = self._resolve_images()
        # Hard fail early if arch mismatch would produce cryptic QEMU errors.
        image_arch = lab_guest_image_arch(self.repo_root)
        if self.arch != image_arch and not os.environ.get("GUNNCHDEVICE_LAB_QEMU_ARCH"):
            # Re-resolve strictly for image arch.
            self.qemu_bin, self.arch = qemu_system_bin(prefer_arch=image_arch, repo_root=self.repo_root)
            self.accel = select_accel(self.arch)

        # WP-011R: Interactive Development Guest recognition. Adds
        # virtio-gpu + virtio-keyboard/tablet + a persistent root disk on
        # top of the slim guest's kernel/initramfs boot. Fails early and
        # honestly if the disk placeholder has not been created yet — never
        # silently falls back to pretending the flag was not set.
        interactive_guest = interactive_guest_enabled()
        interactive_disk: Path | None = None
        if interactive_guest:
            interactive_disk = interactive_guest_disk_path(self.repo_root, arch=self.arch)
            if not interactive_disk.exists():
                return {
                    "ok": False,
                    "error": "interactive_guest_disk_missing",
                    "path": str(interactive_disk),
                    "note": (
                        "GUNNCH_LAB_INTERACTIVE_GUEST=1 set but no provisioned root disk "
                        "found. Run "
                        "os_build/device_lab_interactive_guest/scripts/"
                        "provision_interactive_guest_debian_cloud.py first. See "
                        "os_build/device_lab_interactive_guest/README.md"
                    ),
                    "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
                    "SILICON_EXACT_EMULATION": False,
                }
            # The Interactive Guest is a full Debian disk with its OWN UEFI
            # bootloader/kernel (provisioned by debian_cloud_provisioner.py) —
            # it cannot be booted by attaching it as a secondary virtio-blk
            # disk under the slim guest's -kernel/-initrd Alpine reference
            # image (that combination only ever produces the slim guest
            # boot marker, never a Debian/weston boot). Take a dedicated
            # UEFI boot path instead and return early.
            return self._start_interactive_uefi(interactive_disk)

        disk = self._ensure_persist_disk()
        self.boot_log = self.work / "qemu_boot.log"
        self.pid_file = self.work / "qemu.pid"
        agent_mailbox = self.work / "guest_agent.mailbox"
        # macOS UNIX socket path limit is ~104 bytes; pytest tmp paths are often longer.
        # Keep QEMU sockets under a short /tmp prefix and symlink from work for discovery.
        sock_dir = Path(f"/tmp/gdl-{os.getpid()}-{abs(hash(str(self.work))) % 10_000_000:x}")
        sock_dir.mkdir(parents=True, exist_ok=True)
        self.monitor_sock = sock_dir / "mon.sock"
        self.virtio_serial_sock = sock_dir / "ga.sock"
        for name, target in (("qemu-monitor.sock", self.monitor_sock), ("guest-agent.sock", self.virtio_serial_sock)):
            link = self.work / name
            try:
                if link.exists() or link.is_symlink():
                    link.unlink()
                link.symlink_to(target)
            except OSError:
                pass
        self.state["sock_dir"] = str(sock_dir)
        vnc_display = int(os.environ.get("GUNNCHDEVICE_LAB_VNC_PORT", "0"))  # 0 => display :7 -> 5907
        ws_port = int(os.environ.get("GUNNCHDEVICE_LAB_WS_PORT", "5707"))
        dual_guest = bool(
            (self.profile.get("profile_id") == "dsxl_coder")
            or self.profile.get("dual_screen")
            or os.environ.get("GUNNCHDEVICE_LAB_DUAL_GPU", "").lower() in {"1", "true", "yes"}
        )

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
                (
                    "console=ttyAMA0 earlyprintk=serial rdinit=/init panic=1 "
                    "gunnchos.lab_persist=1 gunnchos.guest_agent=1"
                    if self.arch == "aarch64"
                    else "console=ttyS0 rdinit=/init panic=1 gunnchos.lab_persist=1 gunnchos.guest_agent=1"
                )
                + (" gunnchos.interactive_guest=1" if interactive_guest else "")
            ),
            "-drive",
            f"file={disk},if=virtio,format={'qcow2' if disk.suffix == '.qcow2' else 'raw'}",
            "-serial",
            f"file:{self.boot_log}",
            "-pidfile",
            str(self.pid_file),
            "-daemonize",
            # QEMU monitor unix socket for sendkey / mouse (localhost-only file)
            "-monitor",
            f"unix:{self.monitor_sock},server,nowait",
            # virtio-serial guest agent channel (unix socket on host)
            # aarch64 virt uses PCI: virtio-serial-pci (not bare virtio-serial-device)
            "-chardev",
            f"socket,path={self.virtio_serial_sock},server=on,wait=off,id=ga0",
            "-device",
            "virtio-serial-pci,id=virtio-serial0",
            "-device",
            "virtserialport,bus=virtio-serial0.0,chardev=ga0,name=org.gunnchos.guest_agent.0",
        ]

        # Optional usernet localhost-only (off by default)
        if os.environ.get("GUNNCHDEVICE_LAB_USERNET", "").lower() in {"1", "true", "yes"}:
            cmd += ["-netdev", "user,id=n0,restrict=on", "-device", "virtio-net-device,netdev=n0"]

        # WP-011R Interactive Guest: attach the persistent root disk +
        # real virtio keyboard/tablet input devices (in addition to the
        # existing QEMU-monitor sendkey path used by the slim guest).
        if interactive_guest and interactive_disk is not None:
            cmd += [
                "-drive",
                f"file={interactive_disk},if=virtio,format=qcow2",
                "-device",
                "virtio-keyboard-pci",
                "-device",
                "virtio-tablet-pci",
            ]

        # Optional dual virtio-gpu scanouts for DS-XL guest dual attempt,
        # or a single virtio-gpu scanout for the Interactive Guest compositor.
        guest_outputs: list[dict[str, Any]] = []
        enable_gpu = (dual_guest or interactive_guest) and os.environ.get(
            "GUNNCHDEVICE_LAB_ENABLE_VIRTIO_GPU", "1"
        ).lower() in {
            "1",
            "true",
            "yes",
        }
        if enable_gpu and dual_guest:
            # QEMU ≥11: set outputs[].xres/yres so scanouts start Connected in guest DRM.
            # max_outputs alone leaves Virtual-2 disconnected under headless/single-head.
            # Output names must be ≤12 chars (QEMU virtio-gpu EDID name limit).
            # WP-011R: dual_guest AND interactive_guest can both be true (DS-XL profile
            # booting the Interactive Guest) — same two-output device works for either;
            # the difference is whether a real compositor is running on top (DSXL
            # compositor UX proof needs the Interactive Guest's weston, not the slim guest).
            gpu_dev = (
                '{"driver":"virtio-gpu-pci","id":"gpu0","max_outputs":2,'
                '"outputs":['
                '{"name":"lab0","xres":1280,"yres":800},'
                '{"name":"lab1","xres":1280,"yres":800}'
                "]}"
            )
            cmd += ["-device", gpu_dev]
            # Device attached ≠ guest-proven dual. Keep GUEST_DUAL_OUTPUT_PASS false
            # until guest agent display_info proves two guest outputs.
            guest_outputs = [
                {
                    "id": "guest-gpu0-out0",
                    "role": "primary",
                    "connected": False,
                    "source": "qemu_virtio_gpu_device_attached",
                    "class": "host_device_intent",
                    "note": "virtio-gpu max_outputs=2 + outputs xres/yres; awaiting guest DRM proof",
                },
                {
                    "id": "guest-gpu0-out1",
                    "role": "secondary",
                    "connected": False,
                    "source": "qemu_virtio_gpu_device_attached",
                    "class": "host_device_intent",
                    "note": "virtio-gpu max_outputs=2 + outputs xres/yres; awaiting guest DRM proof",
                },
            ]
        elif enable_gpu and interactive_guest:
            # Single scanout is enough for a non-dual Interactive Guest compositor.
            cmd += ["-device", "virtio-gpu-pci,id=gpu0"]
            guest_outputs = [
                {
                    "id": "guest-gpu0-out0",
                    "role": "primary",
                    "connected": False,
                    "source": "qemu_virtio_gpu_device_attached",
                    "class": "host_device_intent",
                    "note": (
                        "virtio-gpu attached for Interactive Guest compositor; "
                        "awaiting real guest compositor_info proof"
                    ),
                }
            ]

        # Display transport: real VNC (+ websocket when supported) — not fake screenshots
        # Note: QEMU forbids combining -nographic with -daemonize; use -display none instead.
        display_mode = os.environ.get(
            "GUNNCHDEVICE_LAB_DISPLAY",
            "vnc" if (not self.headless or os.environ.get("GUNNCHDEVICE_LAB_FORCE_VNC") == "1") else "none",
        )
        use_vnc = not (
            self.headless and display_mode == "none" and os.environ.get("GUNNCHDEVICE_LAB_FORCE_VNC") != "1"
        )
        if not use_vnc and display_mode != "spice":
            cmd += ["-display", "none"]
            self.display_transport = {
                "kind": "none_headless",
                "note": "Headless CI/default; set GUNNCHDEVICE_LAB_DISPLAY=vnc or FORCE_VNC=1 for live path",
                "fake_screenshot_only": False,
                "guest_outputs": guest_outputs,
            }
        elif display_mode == "spice":
            spice_port = 5900 + (vnc_display or 8)
            cmd += [
                "-display",
                "none",
                "-spice",
                f"addr=127.0.0.1,port={spice_port},disable-ticketing=on",
            ]
            self.display_transport = {
                "kind": "spice",
                "listen": f"127.0.0.1:{spice_port}",
                "novnc_path": "/lab/novnc/",
                "fake_screenshot_only": False,
                "guest_outputs": guest_outputs,
                "note": "SPICE localhost-only",
            }
        else:
            disp = vnc_display or 7
            vnc_port = 5900 + disp
            # Prefer QEMU native websocket listener when available
            vnc_arg = f"127.0.0.1:{disp},websocket={ws_port}"
            cmd += ["-display", "none", "-vnc", vnc_arg]
            self.display_transport = {
                "kind": "vnc",
                "listen": f"127.0.0.1:{vnc_port}",
                "vnc_port": vnc_port,
                "websocket_port": ws_port,
                "novnc_path": "/lab/novnc/",
                "fake_screenshot_only": False,
                "guest_outputs": guest_outputs,
                "note": "VNC+WebSocket localhost-only for Lab UI live pixels",
            }

        # Record command for evidence
        (self.work / "qemu_cmd.json").write_text(
            json.dumps({"cmd": cmd, "accel": self.accel, "arch": self.arch}, indent=2) + "\n",
            encoding="utf-8",
        )

        # daemonize: QEMU forks; parent exits 0 quickly. Retry without optional devices on failure.
        def _failed(res: Any) -> bool:
            return isinstance(res, dict) or getattr(res, "returncode", 1) != 0

        completed = self._run_qemu(cmd)
        if isinstance(completed, dict):
            return completed
        if _failed(completed) and enable_gpu:
            cmd2: list[str] = []
            skip = False
            for i, tok in enumerate(cmd):
                if skip:
                    skip = False
                    continue
                if tok == "-device" and i + 1 < len(cmd):
                    nxt = cmd[i + 1]
                    if nxt.startswith("virtio-gpu") or (
                        nxt.lstrip().startswith("{") and "virtio-gpu" in nxt
                    ):
                        skip = True
                        continue
                cmd2.append(tok)
            cmd = cmd2
            guest_outputs = []
            if isinstance(self.display_transport, dict):
                self.display_transport["guest_outputs"] = []
                self.display_transport["virtio_gpu"] = "unavailable_retry"
            completed = self._run_qemu(cmd)
            if isinstance(completed, dict):
                return completed
        if _failed(completed) and use_vnc and display_mode != "spice":
            cmd2 = []
            skip = False
            for i, tok in enumerate(cmd):
                if skip:
                    skip = False
                    continue
                if tok == "-vnc" and i + 1 < len(cmd):
                    disp = vnc_display or 7
                    cmd2 += ["-vnc", f"127.0.0.1:{disp}"]
                    skip = True
                    continue
                cmd2.append(tok)
            cmd = cmd2
            if isinstance(self.display_transport, dict):
                self.display_transport["websocket_port"] = None
                self.display_transport["note"] = "VNC without native websocket (QEMU fallback)"
            completed = self._run_qemu(cmd)
            if isinstance(completed, dict):
                return completed
        # Always try dropping virtio-serial on hard fail — aarch64 virt PCI variance
        if _failed(completed):
            err = (getattr(completed, "stderr", "") or "") + (getattr(completed, "stdout", "") or "")
            cmd2 = []
            skip = False
            drop_tokens = {"virtio-serial-device", "virtio-serial-pci", "virtserialport"}
            for i, tok in enumerate(cmd):
                if skip:
                    skip = False
                    continue
                if tok == "-chardev" and i + 1 < len(cmd) and "id=ga0" in cmd[i + 1]:
                    skip = True
                    continue
                if tok == "-device" and i + 1 < len(cmd) and any(x in cmd[i + 1] for x in drop_tokens):
                    skip = True
                    continue
                cmd2.append(tok)
            if cmd2 != cmd:
                cmd = cmd2
                completed = self._run_qemu(cmd)
                if isinstance(completed, dict):
                    return completed
                if isinstance(self.display_transport, dict):
                    self.display_transport["virtio_serial"] = "unavailable_retry"
                    self.display_transport["virtio_serial_error"] = err[:400]

        if _failed(completed):
            return {
                "ok": False,
                "error": "qemu_start_failed",
                "stderr": getattr(completed, "stderr", ""),
                "stdout": getattr(completed, "stdout", ""),
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
                "stderr": getattr(completed, "stderr", ""),
                "SILICON_EXACT_EMULATION": False,
            }

        self.started_at = time.time()
        # Guest agent: prefer virtio-serial unix socket; mailbox stub only as last resort.
        os.environ.setdefault("GUNNCH_GUEST_AGENT_HOST_STUB", "0")
        channel = self.virtio_serial_sock if self.virtio_serial_sock and self.virtio_serial_sock.exists() else agent_mailbox
        if channel == agent_mailbox:
            os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "1"
            os.environ["GUNNCH_GUEST_AGENT_MAILBOX"] = "1"
        self.agent = GuestAgentClient(
            channel,
            timeout_sec=5.0,
            extras={"transport_preference": "virtio_serial"},
        )
        agent_status = self._poll_boot_and_agent(
            timeout_sec=float(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "90"))
        )
        # Attempt guest-proven dual outputs via agent (never claim from host device attach alone).
        if enable_gpu and self.agent is not None and agent_status.get("transport") == "virtio_serial":
            try:
                disp = self.agent.call("display_info")
                displays = disp.get("displays") or []
                guest_connected = [
                    d
                    for d in displays
                    if d.get("connected")
                    and (
                        str(d.get("class") or "").startswith("guest")
                        or str(d.get("source") or "")
                        in {"guest_agent", "qemu_virtio_gpu", "virtio-gpu", "guest_drm"}
                    )
                ]
                agent_status["display_info"] = {
                    "connected_count": disp.get("connected_count"),
                    "connector_count": disp.get("connector_count"),
                    "note": disp.get("note"),
                    "guest_proven": disp.get("guest_proven"),
                    "transport": disp.get("transport"),
                    "stub": disp.get("stub"),
                }
                if (
                    len(guest_connected) >= 2
                    and disp.get("transport") == "virtio_serial"
                    and not disp.get("stub")
                    and disp.get("guest_proven") is not False
                ):
                    guest_outputs = [
                        {
                            "id": str(d.get("id") or f"guest{i}"),
                            "role": "primary" if i == 0 else "secondary",
                            "connected": True,
                            "source": "guest_agent",
                            "class": "guest_drm",
                            "status": d.get("status") or "connected",
                        }
                        for i, d in enumerate(guest_connected[:2])
                    ]
                    if isinstance(self.display_transport, dict):
                        self.display_transport["guest_outputs"] = guest_outputs
                    agent_status["guest_dual_proven"] = True
                else:
                    agent_status["guest_dual_proven"] = False
                    agent_status["guest_dual_blocker"] = (
                        disp.get("note")
                        or "Guest display_info did not prove two guest DRM outputs over virtio-serial"
                    )
            except Exception as exc:  # noqa: BLE001
                agent_status["guest_dual_proven"] = False
                agent_status["guest_dual_blocker"] = f"display_info_failed: {exc}"
        elif enable_gpu:
            agent_status["guest_dual_proven"] = False
            agent_status["guest_dual_blocker"] = (
                "virtio-gpu attached but agent transport is not virtio-serial; "
                "GUEST_DUAL_OUTPUT_PASS remains false"
            )

        # Live display probe when VNC enabled
        live_info = None
        if self.display_transport.get("kind") == "vnc":
            from gunnchos_device_os.device_lab.virtualization.live_display import (
                LiveDisplayBridge,
                prove_live_display_path,
                write_display_evidence,
            )

            vnc_port = int(self.display_transport.get("vnc_port") or 5907)
            bridge = LiveDisplayBridge(
                vnc_host="127.0.0.1",
                vnc_port=vnc_port,
                ws_port=int(self.display_transport.get("websocket_port") or ws_port),
                work=self.work,
            )
            # If QEMU websocket not listening, try websockify
            ws_port_eff = int(self.display_transport.get("websocket_port") or 0)
            if ws_port_eff:
                import socket as _sock

                try:
                    with _sock.create_connection(("127.0.0.1", ws_port_eff), timeout=0.3):
                        pass
                except OSError:
                    bridge.start_websockify_if_available()
            live_info = prove_live_display_path(vnc_port=vnc_port)
            write_display_evidence(self.work, live_info)
            self.live_display = bridge
            self.display_transport["live"] = live_info
            self.display_transport["ui"] = bridge.describe()

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
            "monitor_sock": str(self.monitor_sock) if self.monitor_sock else None,
            "virtio_serial_sock": str(self.virtio_serial_sock) if self.virtio_serial_sock else None,
            "guest_outputs": guest_outputs,
            "interactive_guest": {
                "enabled": interactive_guest,
                "disk_path": str(interactive_disk) if interactive_disk is not None else None,
                "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": interactive_guest,
                "note": (
                    "virtio-gpu/keyboard/tablet + persistent disk recognized by QEMU launcher; "
                    "does not by itself prove a booted compositor — see guest_agent compositor_info"
                    if interactive_guest
                    else "Interactive Guest not requested (slim DEVICE_LAB_DEVELOPMENT_GUEST path)"
                ),
            },
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

    def _start_interactive_uefi(self, disk: Path) -> dict[str, Any]:
        """Boot the provisioned Interactive Development Guest as a real UEFI guest.

        Distinct from the slim guest's direct -kernel/-initrd boot: the disk
        here has its own bootloader (grub-efi) and kernel installed by
        cloud-init on real Debian aarch64, so QEMU must boot it via UEFI
        pflash with the disk as the *primary* boot device — virtio-gpu,
        virtio-keyboard, virtio-tablet, and the virtio-serial guest agent
        channel are attached the same way the slim guest attaches them.
        """
        from gunnchos_device_os.device_lab.debian_cloud_provisioner import find_edk2_firmware

        edk2_code = find_edk2_firmware()
        if edk2_code is None:
            return {
                "ok": False,
                "error": "edk2_firmware_missing",
                "note": "aarch64 UEFI firmware (edk2-aarch64-code.fd) not found on this host",
                "SILICON_EXACT_EMULATION": False,
            }
        self.boot_log = self.work / "qemu_boot.log"
        self.pid_file = self.work / "qemu.pid"
        for p in (self.boot_log, self.pid_file):
            if p.exists():
                p.unlink()
        sock_dir = Path(f"/tmp/gdli-{os.getpid()}-{abs(hash(str(self.work))) % 10_000_000:x}")
        sock_dir.mkdir(parents=True, exist_ok=True)
        self.monitor_sock = sock_dir / "mon.sock"
        self.virtio_serial_sock = sock_dir / "ga.sock"
        for name, target in (("qemu-monitor.sock", self.monitor_sock), ("guest-agent.sock", self.virtio_serial_sock)):
            link = self.work / name
            try:
                if link.exists() or link.is_symlink():
                    link.unlink()
                link.symlink_to(target)
            except OSError:
                pass
        self.state["sock_dir"] = str(sock_dir)

        vars_flash = self.work / "edk2-aarch64-vars.fd"
        # Prefer Homebrew's nvram template (edk2-arm-vars.fd) over a zeroed
        # flash — blank vars can land in the UEFI shell after PCI topology changes.
        if not vars_flash.exists() or vars_flash.stat().st_size == 0:
            template_candidates = [
                Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd"),
                Path("/opt/homebrew/opt/qemu/share/qemu/edk2-arm-vars.fd"),
                Path("/usr/share/qemu/edk2-arm-vars.fd"),
            ]
            copied = False
            for tmpl in template_candidates:
                if tmpl.is_file():
                    shutil.copyfile(tmpl, vars_flash)
                    copied = True
                    break
            if not copied:
                with vars_flash.open("wb") as fh:
                    fh.truncate(edk2_code.stat().st_size)

        dual_guest = bool(
            (self.profile.get("profile_id") == "dsxl_coder")
            or self.profile.get("dual_screen")
            or os.environ.get("GUNNCHDEVICE_LAB_DUAL_GPU", "").lower() in {"1", "true", "yes"}
        )
        if dual_guest:
            gpu_dev = (
                '{"driver":"virtio-gpu-pci","id":"gpu0","max_outputs":2,'
                '"outputs":['
                '{"name":"ilab0","xres":1280,"yres":800},'
                '{"name":"ilab1","xres":1280,"yres":800}'
                "]}"
            )
        else:
            gpu_dev = "virtio-gpu-pci,id=gpu0"

        cmd = [
            self.qemu_bin,
            "-machine",
            f"virt,accel={self.accel['accel']}",
            "-cpu",
            self.accel["cpu"],
            "-smp",
            str(self.smp),
            "-m",
            str(self.memory_mb),
            "-drive",
            f"if=pflash,format=raw,readonly=on,file={edk2_code}",
            "-drive",
            f"if=pflash,format=raw,file={vars_flash}",
            # Explicit bootindex keeps UEFI on the Linux root disk when PCI
            # slot order changes (GPU/keyboard inserted ahead of the disk).
            "-drive",
            f"file={disk},if=none,format=qcow2,id=hd0",
            "-device",
            "virtio-blk-pci,drive=hd0,bootindex=1",
            "-device",
            gpu_dev,
            "-device",
            "virtio-keyboard-pci",
            "-device",
            "virtio-tablet-pci",
            "-serial",
            f"file:{self.boot_log}",
            "-display",
            "none",
            "-pidfile",
            str(self.pid_file),
            "-monitor",
            f"unix:{self.monitor_sock},server,nowait",
            "-chardev",
            f"socket,path={self.virtio_serial_sock},server=on,wait=off,id=ga0",
            "-device",
            "virtio-serial-pci,id=virtio-serial0",
            "-device",
            "virtserialport,bus=virtio-serial0.0,chardev=ga0,name=org.gunnchos.guest_agent.0",
            "-daemonize",
        ]
        if os.environ.get("GUNNCHDEVICE_LAB_INTERACTIVE_NET", "1").lower() in {"1", "true", "yes"}:
            cmd += [
                "-netdev",
                "user,id=n0,restrict=on",
                "-device",
                "virtio-net-pci,netdev=n0",
            ]
        (self.work / "qemu_cmd.json").write_text(
            json.dumps({"cmd": cmd, "accel": self.accel, "arch": self.arch, "interactive_uefi": True}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        completed = self._run_qemu(cmd)
        if isinstance(completed, dict):
            return completed
        if getattr(completed, "returncode", 1) != 0:
            return {
                "ok": False,
                "error": "qemu_start_failed",
                "stderr": getattr(completed, "stderr", ""),
                "stdout": getattr(completed, "stdout", ""),
                "cmd": cmd,
                "SILICON_EXACT_EMULATION": False,
            }
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
                "stderr": getattr(completed, "stderr", ""),
                "SILICON_EXACT_EMULATION": False,
            }
        self.started_at = time.time()
        self.agent = GuestAgentClient(
            self.virtio_serial_sock,
            timeout_sec=5.0,
            extras={"transport_preference": "virtio_serial"},
        )
        boot_timeout = float(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "180"))
        ready = self.agent.wait_ready(timeout_sec=boot_timeout)
        self.boot_complete = bool(ready.get("ready"))
        self.display_transport = {
            "kind": "none_headless",
            "note": "Interactive Guest headless by default; VNC not wired for this boot path yet",
            "fake_screenshot_only": False,
            "guest_outputs": [],
        }
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
            "guest_agent": {
                "ready": self.boot_complete,
                "transport": (ready.get("response") or {}).get("transport"),
                "agent_path_label": (ready.get("response") or {}).get("agent_path_label"),
                "measurement_class": "HOST_OBSERVED",
                "response": ready,
            },
            "monitor_sock": str(self.monitor_sock),
            "virtio_serial_sock": str(self.virtio_serial_sock),
            "guest_outputs": [],
            "interactive_guest": {
                "enabled": True,
                "boot_path": "uefi_primary_disk",
                "disk_path": str(disk),
                "dual_gpu_requested": dual_guest,
                "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
                "SHIPPING_IMAGE": False,
            },
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

    def _run_qemu(self, cmd: list[str]) -> Any:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            return {
                "ok": False,
                "error": "qemu_exec_failed",
                "detail": str(exc),
                "SKIPPED_ENVIRONMENT": False,
                "SILICON_EXACT_EMULATION": False,
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
                if "GUNNCHOS_GUEST_AGENT=started" in text or "GUNNCHOS_GUEST_AGENT_HEARTBEAT=" in text:
                    markers.append("guest_agent_serial")
            time.sleep(0.5)
        assert self.agent is not None
        # Prefer virtio-serial; if not ready, fall back to mailbox stub without lying.
        ready = self.agent.wait_ready(timeout_sec=min(12.0, timeout_sec))
        transport = "virtio_serial"
        agent_path_label = "virtio-serial"
        rsp = ready.get("response") or {}
        if ready.get("ready") and str(rsp.get("transport") or "") in {"virtio_serial", "virtio-serial"}:
            transport = "virtio_serial"
            agent_path_label = "virtio-serial"
        elif ready.get("ready") and str(rsp.get("transport") or "") == "host_mailbox_stub":
            transport = "host_mailbox_stub"
            agent_path_label = "host_mailbox_stub"
        if not ready.get("ready"):
            mailbox = self.work / "guest_agent.mailbox"
            os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "1"
            os.environ["GUNNCH_GUEST_AGENT_MAILBOX"] = "1"
            stub_client = GuestAgentClient(mailbox, timeout_sec=2.0)
            stub_ready = stub_client.wait_ready(timeout_sec=2.0)
            if stub_ready.get("ready"):
                self.agent = stub_client
                ready = stub_ready
                transport = "host_mailbox_stub_fallback"
                agent_path_label = "host_mailbox_stub_fallback"
                markers.append("agent_mailbox_fallback")
            else:
                transport = "FAIL_NO_AGENT"
                agent_path_label = "FAIL_NO_AGENT"
                markers.append("agent_unavailable")
        return {
            "ready": bool(ready.get("ready")) or self.boot_complete,
            "boot_complete_observed": self.boot_complete,
            "markers": markers,
            "agent_response": ready,
            "transport": transport,
            "agent_path_label": agent_path_label,
            "measurement_class": "HOST_OBSERVED",
            "note": (
                "Boot markers from QEMU serial file; agent prefers virtio-serial "
                f"({agent_path_label}). Mailbox stub is labeled when used."
            ),
        }

    def stop(self) -> dict[str, Any]:
        if self.live_display is not None:
            try:
                self.live_display.stop()
            except Exception:
                pass
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
        # Best-effort cleanup of short socket dir
        for sock in (self.monitor_sock, self.virtio_serial_sock):
            if sock is None:
                continue
            try:
                if sock.exists():
                    sock.unlink()
                parent = sock.parent
                if parent.name.startswith("gdl-") and parent.exists():
                    try:
                        parent.rmdir()
                    except OSError:
                        pass
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


def environment_can_run_qemu(repo_root: Path | None = None) -> dict[str, Any]:
    try:
        bin_path, arch = qemu_system_bin(repo_root=repo_root)
        accel = select_accel(arch)
        return {
            "ok": True,
            "qemu_bin": bin_path,
            "arch": arch,
            "accel": accel,
            "version": _qemu_version(bin_path),
            "image_arch": lab_guest_image_arch(repo_root),
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
    env = environment_can_run_qemu(repo_root=repo_root)
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
    # Honesty: qemu_start_failed is FAIL, never PASS/SKIPPED unless environment truly missing.
    if not result.get("ok") and not result.get("SKIPPED_ENVIRONMENT"):
        result["result"] = "FAIL"
        result.setdefault("ok", False)
    return result
