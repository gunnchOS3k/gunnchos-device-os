#!/usr/bin/env python3
"""Guest-native Interactive Development Guest provisioner (QEMU + PTY).

Cycle 3B WP-011R: boots Alpine virt ISO inside QEMU (HVF aarch64), installs
to qcow2 via setup-alpine, then apk-adds Wayland stack — all guest-native.

Uses a PTY so QEMU stdout cannot deadlock the host pipe buffer.
DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false.
Never asserts *_PASS tokens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import termios
import time
import tty
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALPINE_VERSION = "3.21.3"
ALPINE_MAJOR = "3.21"
ARCH = "aarch64"
ISO_NAME = f"alpine-virt-{ALPINE_VERSION}-{ARCH}.iso"
ISO_URL = (
    f"https://dl-cdn.alpinelinux.org/alpine/v{ALPINE_MAJOR}/releases/{ARCH}/{ISO_NAME}"
)

GUEST_PACKAGES = [
    "seatd",
    "weston",
    "mesa-dri-gallium",
    "foot",
    "nano",
    "pipewire",
    "pipewire-alsa",
    "libinput",
    "eudev",
    "font-dejavu",
    "python3",
    "openssh",
    "chromium",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _find_edk2() -> Path | None:
    for p in (
        Path("/opt/homebrew/share/qemu/edk2-aarch64-code.fd"),
        Path("/opt/homebrew/opt/qemu/share/qemu/edk2-aarch64-code.fd"),
        Path("/usr/share/qemu/edk2-aarch64-code.fd"),
        Path("/usr/share/AAVMF/AAVMF_CODE.fd"),
    ):
        if p.is_file():
            return p
    return None


def download_iso(cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    iso = cache / ISO_NAME
    if iso.is_file() and iso.stat().st_size > 1_000_000:
        return iso
    partial = cache / f"{ISO_NAME}.partial"
    print(f"[provision] downloading {ISO_URL}", flush=True)
    subprocess.check_call(["curl", "-L", "--fail", "-o", str(partial), ISO_URL])
    partial.rename(iso)
    return iso


def write_answerfile(path: Path) -> None:
    path.write_text(
        """KEYMAPOPTS="us us"
HOSTNAMEOPTS="-n gunnch-lab-interactive"
DEVDOPTS="mdev"
INTERFACESOPTS="auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
"
TIMEZONEOPTS="-z UTC"
PROXYOPTS="none"
APKREPOSOPTS="-1"
SSHDOPTS="-c openssh"
NTPOPTS="-c none"
DISKOPTS="-m sys /dev/vda"
LBUOPTS="none"
APKCACHEOPTS="none"
""",
        encoding="utf-8",
    )


class PtyQemu:
    def __init__(self, cmd: list[str], log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_fh = self.log_path.open("ab")
        self.master, slave = pty.openpty()
        # raw slave
        tty.setraw(slave)
        self.proc = subprocess.Popen(
            cmd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            start_new_session=True,
            close_fds=True,
        )
        os.close(slave)
        self.buf = ""
        # non-blocking master
        os.set_blocking(self.master, False)

    def alive(self) -> bool:
        return self.proc.poll() is None

    def _drain(self) -> str:
        chunks: list[str] = []
        while True:
            try:
                data = os.read(self.master, 8192)
            except BlockingIOError:
                break
            if not data:
                break
            self.log_fh.write(data)
            self.log_fh.flush()
            chunks.append(data.decode("utf-8", errors="replace"))
        text = "".join(chunks)
        self.buf += text
        # keep buf bounded
        if len(self.buf) > 200_000:
            self.buf = self.buf[-100_000:]
        return text

    def wait_for(self, patterns: list[str], timeout: float) -> str:
        deadline = time.time() + timeout
        rx = [re.compile(p, re.I | re.M) for p in patterns]
        while time.time() < deadline:
            self._drain()
            for r in rx:
                if r.search(self.buf):
                    return self.buf
            if not self.alive():
                break
            # wait for readability
            select.select([self.master], [], [], 0.25)
        raise TimeoutError(
            f"timeout waiting {patterns}; tail={self.buf[-1200:]!r}"
        )

    def send(self, data: str) -> None:
        self._drain()
        os.write(self.master, data.encode("utf-8"))

    def close(self) -> int:
        try:
            if self.alive():
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
        finally:
            try:
                os.close(self.master)
            except OSError:
                pass
            self.log_fh.close()
        return int(self.proc.returncode or 0)


def qemu_cmd(
    *,
    qemu_bin: str,
    edk2: Path,
    disk: Path,
    iso: Path | None,
    memory_mb: int,
    boot_cdrom: bool,
) -> list[str]:
    accel: list[str] = []
    cpu = "cortex-a72"
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        accel = ["-accel", "hvf"]
        cpu = "host"
    elif Path("/dev/kvm").exists():
        accel = ["-accel", "kvm"]
        cpu = "host"
    cmd = [
        qemu_bin,
        "-machine",
        "virt",
        "-cpu",
        cpu,
        *accel,
        "-m",
        str(memory_mb),
        "-smp",
        "2",
        "-nographic",
        "-drive",
        f"if=pflash,format=raw,readonly=on,file={edk2}",
        "-drive",
        f"file={disk},if=virtio,format=qcow2",
        "-netdev",
        "user,id=n0",
        "-device",
        "virtio-net-pci,netdev=n0",
        "-device",
        "virtio-rng-pci",
    ]
    if boot_cdrom and iso is not None:
        cmd += ["-cdrom", str(iso), "-boot", "order=d"]
    return cmd


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\].*?\x07", "", s)


def phase1(iso: Path, disk: Path, edk2: Path, qemu_bin: str, work: Path, evidence: dict) -> None:
    if disk.exists():
        disk.unlink()
    subprocess.check_call(["qemu-img", "create", "-f", "qcow2", str(disk), "12G"])
    cmd = qemu_cmd(
        qemu_bin=qemu_bin,
        edk2=edk2,
        disk=disk,
        iso=iso,
        memory_mb=2048,
        boot_cdrom=True,
    )
    print("[provision] phase1", " ".join(cmd), flush=True)
    q = PtyQemu(cmd, work / "phase1_serial.log")
    try:
        # Wait for login prompt (avoid matching '#' in progress bars by requiring login:)
        q.wait_for([r"login:\s*$", r"localhost login:"], timeout=300)
        q.send("root\n")
        q.wait_for([r"(~|#)\s*$", r"Welcome to Alpine"], timeout=60)
        # network + repos
        for line in [
            "export TERM=dumb\n",
            "setup-interfaces -a || true\n",
            "udhcpc -i eth0 || udhcpc -i enp0s1 || true\n",
            "printf '%s\\n' https://dl-cdn.alpinelinux.org/alpine/v3.21/main https://dl-cdn.alpinelinux.org/alpine/v3.21/community > /etc/apk/repositories\n",
            "apk update\n",
        ]:
            q.send(line)
            time.sleep(0.3)
            q._drain()
        q.wait_for([r"OK:", r"packages"], timeout=180)
        q.send("apk add openrc util-linux e2fsprogs sfdisk dosfstools lsblk\n")
        # drain while apk runs
        deadline = time.time() + 300
        while time.time() < deadline:
            q._drain()
            if re.search(r"(~|#)\s*$", strip_ansi(q.buf[-200:])):
                # heuristic: prompt returned
                if "e2fsprogs" in q.buf or "Executing" in q.buf or "OK:" in q.buf:
                    break
            if not q.alive():
                break
            select.select([q.master], [], [], 0.5)
        # answerfile
        af = (work / "answers").read_text(encoding="utf-8")
        q.send("cat > /root/answers <<'EOF'\n")
        for line in af.splitlines():
            q.send(line + "\n")
        q.send("EOF\n")
        q.send("export ERASE_DISKS=/dev/vda\n")
        q.send("yes | setup-alpine -f /root/answers\n")
        deadline = time.time() + 700
        ok = False
        while time.time() < deadline:
            q._drain()
            low = q.buf.lower()
            if "installation is complete" in low or "you may reboot" in low or "you can reboot" in low:
                ok = True
                break
            if not q.alive():
                break
            select.select([q.master], [], [], 0.5)
        evidence["phase1_ok"] = ok
        evidence["phase1_tail"] = strip_ansi(q.buf[-2500:])
        q.send("poweroff\n")
        deadline = time.time() + 90
        while time.time() < deadline and q.alive():
            q._drain()
            select.select([q.master], [], [], 0.5)
    finally:
        evidence["phase1_exit"] = q.close()


def phase2(disk: Path, edk2: Path, qemu_bin: str, work: Path, evidence: dict) -> None:
    cmd = qemu_cmd(
        qemu_bin=qemu_bin,
        edk2=edk2,
        disk=disk,
        iso=None,
        memory_mb=3072,
        boot_cdrom=False,
    )
    print("[provision] phase2", " ".join(cmd), flush=True)
    q = PtyQemu(cmd, work / "phase2_serial.log")
    try:
        q.wait_for([r"login:\s*$", r"localhost login:"], timeout=360)
        q.send("root\n")
        time.sleep(0.5)
        q._drain()
        # empty password
        if "password" in q.buf.lower()[-200:]:
            q.send("\n")
        q.wait_for([r"(~|#)\s*$"], timeout=90)
        pkgs = " ".join(GUEST_PACKAGES)
        script = f"""set -e
export TERM=dumb
udhcpc -i eth0 || udhcpc -i enp0s1 || true
printf '%s\\n' https://dl-cdn.alpinelinux.org/alpine/v3.21/main https://dl-cdn.alpinelinux.org/alpine/v3.21/community > /etc/apk/repositories
apk update
apk add {pkgs} || apk add seatd weston mesa-dri-gallium foot nano pipewire libinput eudev font-dejavu python3 openssh
rc-update add seatd default || true
mkdir -p /etc/xdg/weston /opt/gunnchos/bin /var/lib/gunnchos
cat > /etc/xdg/weston/weston.ini <<'WEOF'
[core]
backend=drm-backend.so
shell=desktop-shell.so
[shell]
locking=false
WEOF
cat > /opt/gunnchos/bin/lab-compositor-start <<'WEOF'
#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/0
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
exec weston --backend=drm-backend.so
WEOF
chmod +x /opt/gunnchos/bin/lab-compositor-start
echo INTERACTIVE_GUEST_PACKAGES_OK > /var/lib/gunnchos/interactive_guest_ready
sync
poweroff
"""
        q.send("cat > /root/phase2.sh <<'EOF'\n")
        for line in script.splitlines():
            q.send(line + "\n")
        q.send("EOF\n")
        q.send("sh /root/phase2.sh\n")
        deadline = time.time() + 1200
        marker = False
        while time.time() < deadline:
            q._drain()
            if "INTERACTIVE_GUEST_PACKAGES_OK" in q.buf:
                marker = True
            if not q.alive():
                break
            select.select([q.master], [], [], 0.5)
        evidence["phase2_ok"] = marker
        evidence["phase2_tail"] = strip_ansi(q.buf[-2500:])
    finally:
        evidence["phase2_exit"] = q.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--phase", choices=["all", "1", "2"], default="all")
    args = ap.parse_args()
    root = args.repo_root or _repo_root()
    interactive = root / "os_build" / "device_lab_interactive_guest"
    cache = interactive / "cache"
    work = interactive / "work" / "qemu_native"
    artifacts = interactive / "artifacts"
    work.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    disk = artifacts / f"interactive-root-{ARCH}.qcow2"
    evidence_path = artifacts / "INTERACTIVE_GUEST_QEMU_NATIVE_PROVISION.json"
    evidence: dict[str, Any] = {
        "schema": "gunnchos.device_lab.interactive_guest_qemu_native_provision.v1",
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SHIPPING_IMAGE": False,
        "SILICON_EXACT_EMULATION": False,
        "method": "qemu_pty_alpine_iso_setup",
        "host": {"system": platform.system(), "machine": platform.machine()},
        "ok": False,
        "LIVE_GUNNCHOS_VISUAL_PASS": False,
        "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "ECO010_SOAK_PASS": False,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
    }
    qemu_bin = shutil.which("qemu-system-aarch64")
    edk2 = _find_edk2()
    if not qemu_bin or not edk2:
        evidence["error"] = "missing_qemu_or_edk2"
        _write_json(evidence_path, evidence)
        return 1
    write_answerfile(work / "answers")
    try:
        iso = download_iso(cache)
        evidence["iso"] = {"path": str(iso), "sha256": _sha256(iso), "url": ISO_URL}
        if args.phase in ("all", "1"):
            phase1(iso, disk, edk2, qemu_bin, work, evidence)
        if args.phase in ("all", "2"):
            if not evidence.get("phase1_ok") and args.phase == "all":
                print("[provision] phase1 incomplete — attempting phase2 anyway", flush=True)
            phase2(disk, edk2, qemu_bin, work, evidence)
        evidence["disk"] = {
            "path": str(disk),
            "sha256": _sha256(disk) if disk.is_file() else None,
            "size_bytes": disk.stat().st_size if disk.is_file() else None,
        }
        evidence["ok"] = bool(evidence.get("phase2_ok"))
        evidence["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest = {
            "schema": "gunnchos.device_lab.interactive_guest_image.manifest.v1",
            "version": "0.2.0-qemu-native-pty",
            "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
            "SHIPPING_IMAGE": False,
            "SILICON_EXACT_EMULATION": False,
            "provision_method": "qemu_pty_alpine_iso_setup",
            "arch": ARCH,
            "disk": evidence.get("disk"),
            "packages_requested": GUEST_PACKAGES,
            "provision_ok": evidence["ok"],
            "claim_boundary": (
                "Interactive development guest via QEMU-native Alpine ISO install. "
                "Not shipping. PASS tokens require separate visual/app proofs."
            ),
        }
        _write_json(artifacts / "INTERACTIVE_GUEST_MANIFEST.json", manifest)
        _write_json(evidence_path, evidence)
        print(json.dumps({"ok": evidence["ok"], "evidence": str(evidence_path)}, indent=2))
        return 0 if evidence["ok"] else 1
    except Exception as e:
        evidence["error"] = str(e)
        evidence["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_json(evidence_path, evidence)
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
