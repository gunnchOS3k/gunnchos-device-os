"""CX2E QEMU lifecycle — independent of Device Lab provisioner.

Lifecycle (steps 1–16 condensed):
  prepare overlay/base → SSH keys → cloud-init seed → first-boot provision+poweroff
  → second-boot graphical → SSH wait → provenance → Weston session → deploy shell
  → journeys → evidence → shutdown

One guest at a time. Prefer HVF. Fail closed on PASS inflation.
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import platform
import shutil
import socket
import socketserver
import subprocess
import textwrap
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gunnchos_device_os.cx2e.paths import (
    DEVICE_LAB_FORBIDDEN,
    cx2e_lab_root,
    ensure_lab_tree,
    evidence_root,
    repo_root_from_here,
)

PROVISION_OK = "CX2E_LINUX_LAB_PROVISION_OK"
PROVISION_FAIL = "CX2E_LINUX_LAB_PROVISION_FAILED"
DEFAULT_SSH_PORT = 2227
DEFAULT_MEMORY_MB = 4096
DEFAULT_SMP = 4
DEFAULT_DISK_GB = 16
PROVISION_TIMEOUT_S = 2700

REQUIRED_PACKAGES = (
    "linux-image-arm64",  # DRM/virtio-gpu (cloud kernel lacks DRM)
    "weston",
    "seatd",
    "libseat1",
    "kbd",
    "dbus-user-session",
    "dbus-x11",
    "libgl1-mesa-dri",
    "mesa-utils",
    "xwayland",
    "fonts-dejavu",
    "xdg-desktop-portal",
    "xdg-desktop-portal-gtk",
    "flatpak",
    "cups",
    "cups-bsd",
    "cups-client",
    "chromium",
    "libreoffice",
    "libreoffice-gtk3",
    "thunderbird",  # bookworm arm64 package name (not thunderbird)
    "ffmpeg",
    "at-spi2-core",
    "orca",
    "python3",
    "python3-gi",
    "gir1.2-atspi-2.0",
    "openssh-server",
    "curl",
    "ca-certificates",
    "pipewire",
    "wireplumber",
    "wayland-utils",
    "libinput-tools",
    "evtest",
    "python3-evdev",
)


def sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def find_edk2() -> Optional[Path]:
    for c in (
        "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
        "/opt/homebrew/opt/qemu/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/AAVMF/AAVMF_CODE.fd",
    ):
        p = Path(c)
        if p.is_file():
            return p
    return None


def select_accel() -> Dict[str, str]:
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        # Prefer HVF; do not pretend acceleration if unavailable.
        try:
            # Hypervisor.framework presence is a soft signal; QEMU will fail loudly if HVF broken.
            if Path("/System/Library/Frameworks/Hypervisor.framework").exists():
                return {"accel": "hvf", "cpu": "host", "accel_note": "HVF preferred on Apple Silicon"}
        except Exception:
            pass
        return {"accel": "tcg", "cpu": "max", "accel_note": "HVF unavailable; using TCG honestly"}
    if Path("/dev/kvm").exists():
        return {"accel": "kvm", "cpu": "host", "accel_note": "KVM"}
    return {"accel": "tcg", "cpu": "max", "accel_note": "TCG fallback"}


def host_prereqs() -> Dict[str, Any]:
    qemu = shutil.which("qemu-system-aarch64") or (
        "/opt/homebrew/bin/qemu-system-aarch64"
        if Path("/opt/homebrew/bin/qemu-system-aarch64").exists()
        else None
    )
    qimg = shutil.which("qemu-img") or (
        "/opt/homebrew/bin/qemu-img" if Path("/opt/homebrew/bin/qemu-img").exists() else None
    )
    edk2 = find_edk2()
    accel = select_accel()
    st = os.statvfs("/")
    free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
    return {
        "host_os": platform.system(),
        "host_machine": platform.machine(),
        "qemu_system_aarch64": qemu,
        "qemu_img": qimg,
        "edk2": str(edk2) if edk2 else None,
        "accel": accel,
        "free_disk_gb": round(free_gb, 2),
        "ok": bool(qemu and qimg and edk2 and free_gb >= 8),
    }


def any_qemu_running() -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-lf", "qemu-system"], text=True)
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False
    except Exception:
        # sandbox / permissions — try ps
        try:
            out = subprocess.check_output(["ps", "aux"], text=True)
            return "qemu-system" in out
        except Exception:
            return False


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


@dataclass
class SeedHttpServer:
    directory: Path
    port: int = 0
    _httpd: socketserver.TCPServer | None = field(default=None, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def start(self) -> int:
        handler = lambda *a, **kw: _QuietHandler(*a, directory=str(self.directory), **kw)  # noqa: E731
        self._httpd = socketserver.TCPServer(("127.0.0.1", self.port), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()


def ensure_ssh_keypair(lab: Path) -> Dict[str, str]:
    ssh_dir = lab / "ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)
    priv = ssh_dir / "id_ed25519"
    pub = ssh_dir / "id_ed25519.pub"
    if not priv.is_file():
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(priv), "-C", "cx2e-lab"],
            check=True,
            capture_output=True,
            text=True,
        )
    return {"private": str(priv), "public": str(pub), "public_key": pub.read_text().strip()}


def base_image_ro(repo: Path) -> Path:
    return (
        repo
        / "os_build"
        / "device_lab_interactive_guest"
        / "cache"
        / "debian-12-genericcloud-arm64.qcow2"
    )


def prepare_overlay(repo: Path, *, resize_gb: int = DEFAULT_DISK_GB) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    src = base_image_ro(repo)
    dest = lab / "images" / "debian-12-genericcloud-arm64.qcow2"
    overlay = lab / "overlays" / "cx2e-aarch64.qcow2"
    prereq = host_prereqs()
    result: Dict[str, Any] = {
        "ok": False,
        "base_source_ro": str(src),
        "base_copy": str(dest),
        "overlay": str(overlay),
        "blocker": None,
        "host": prereq,
    }
    if not src.is_file():
        result["blocker"] = "CX2E_BASE_IMAGE_MISSING"
        return result
    if not prereq["ok"]:
        result["blocker"] = f"CX2E_HOST_PREREQ_FAIL: {prereq}"
        return result
    if not dest.is_file():
        try:
            os.link(src, dest)
        except OSError:
            shutil.copy2(src, dest)
    if overlay.is_file():
        # Keep existing overlay (may already be provisioned)
        result["ok"] = True
        result["base_sha256"] = sha256_file(dest)
        result["overlay_sha256"] = sha256_file(overlay)
        result["reused_overlay"] = True
        return result
    cmd = [
        prereq["qemu_img"],
        "create",
        "-f",
        "qcow2",
        "-F",
        "qcow2",
        "-b",
        str(dest),
        str(overlay),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        subprocess.run(
            [prereq["qemu_img"], "resize", str(overlay), f"{resize_gb}G"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        result["blocker"] = f"CX2E_OVERLAY_CREATE_FAILED: {exc}"
        return result
    result["ok"] = True
    result["base_sha256"] = sha256_file(dest)
    result["overlay_sha256"] = sha256_file(overlay)
    result["reused_overlay"] = False
    return result


def _indent(text: str, spaces: int = 6) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else pad.rstrip() for line in text.splitlines())


def write_cloud_init(lab: Path, *, ssh_pubkey: str, weston_ini: str, weston_unit: str) -> Dict[str, str]:
    pkgs = "\n".join(f"  - {p}" for p in REQUIRED_PACKAGES)
    user_data = f"""#cloud-config
hostname: cx2e-linux-lab
manage_etc_hosts: true
ssh_pwauth: false
users:
  - name: gunnchos
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    groups: [sudo, video, render, audio, seat]
    ssh_authorized_keys:
      - {ssh_pubkey}
package_update: true
package_upgrade: false
packages:
{pkgs}
write_files:
  - path: /etc/xdg/weston/weston.ini
    permissions: '0644'
    content: |
{_indent(weston_ini)}
  - path: /etc/cx2e-weston/weston.ini
    permissions: '0644'
    content: |
{_indent(weston_ini)}
  - path: /etc/systemd/system/cx2e-weston.service
    permissions: '0644'
    content: |
{_indent(weston_unit)}
  - path: /usr/local/bin/cx2e-verify-provision.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      set -euo pipefail
      mkdir -p /var/lib/cx2e
      missing=""
      for p in weston seatd chromium libreoffice flatpak cups xdg-desktop-portal; do
        if ! dpkg -s "$p" >/dev/null 2>&1; then missing="$missing $p"; fi
      done
      if [ -n "$missing" ]; then
        echo CX2E_LINUX_LAB_PROVISION_FAILED missing:$missing
        exit 1
      fi
      echo CX2E_LINUX_LAB_PROVISION_OK > /var/lib/cx2e/PROVISIONED
      echo CX2E_LINUX_LAB_PROVISION_OK
  - path: /etc/ssh/sshd_config.d/99-cx2e.conf
    permissions: '0644'
    content: |
      PasswordAuthentication no
      PermitRootLogin prohibit-password
runcmd:
  - [ bash, -c, "mkdir -p /run/cx2e-wayland /var/lib/cx2e /opt/cx2e /var/log && chmod 700 /run/cx2e-wayland" ]
  - [ bash, -c, "groupadd -f seat || true; usermod -aG seat,video,render gunnchos || true" ]
  - [ bash, -c, "dpkg -l > /var/lib/cx2e/dpkg-versions.txt 2>&1 || true" ]
  - [ bash, -c, "dpkg-query -W -f='${{Package}}\\t${{Version}}\\n' weston seatd chromium libreoffice flatpak cups xdg-desktop-portal xdg-desktop-portal-gtk at-spi2-core orca thunderbird ffmpeg > /var/lib/cx2e/key-packages.txt 2>&1 || true" ]
  - [ systemctl, enable, cx2e-weston.service ]
  - [ systemctl, enable, ssh ]
  - [ /usr/local/bin/cx2e-verify-provision.sh ]
  - [ bash, -c, "touch /etc/cloud/cloud-init.disabled" ]
power_state:
  mode: poweroff
  timeout: 60
  condition: true
"""
    meta = "instance-id: cx2e-linux-lab-1\nlocal-hostname: cx2e-linux-lab\n"
    seed = lab / "seed"
    seed.mkdir(parents=True, exist_ok=True)
    (seed / "user-data").write_text(user_data)
    (seed / "meta-data").write_text(meta)
    (lab / "cloud-init" / "user-data").write_text(user_data)
    (lab / "cloud-init" / "meta-data").write_text(meta)
    return {
        "seed_dir": str(seed),
        "user_data_sha256": sha256_text(user_data),
        "meta_data_sha256": sha256_text(meta),
    }



def short_runtime_paths(label: str) -> Dict[str, Path]:
    """QEMU UNIX monitor sockets must be <104 bytes on Darwin — use /tmp."""
    base = Path(f"/tmp/cx2e-{label}")
    base.mkdir(parents=True, exist_ok=True)
    return {
        "dir": base,
        "monitor": base / "monitor.sock",
        "pidfile": base / "qemu.pid",
        "boot_log": base / "serial.log",
    }



def rebuild_cidata_vfat(lab: Path) -> Path:
    """Rewrite VFAT cidata image from seed/ (macOS newfs_msdos + mount)."""
    import shutil
    seed = lab / "seed"
    img = lab / "work" / "cx2e-cidata.img"
    if img.exists():
        img.unlink()
    img.write_bytes(b"\x00" * (64 * 1024 * 1024))
    r = subprocess.run(["hdiutil", "attach", "-nomount", str(img)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"attach failed: {r.stderr}")
    dev = r.stdout.strip().split()[0]
    fr = subprocess.run(["newfs_msdos", "-F", "32", "-v", "cidata", dev], capture_output=True, text=True)
    if fr.returncode != 0:
        subprocess.run(["hdiutil", "detach", dev], check=False)
        raise RuntimeError(f"format failed: {fr.stderr}")
    mp = Path("/tmp/cx2e-cidata-mnt")
    mp.mkdir(exist_ok=True)
    mr = subprocess.run(["mount", "-t", "msdos", dev, str(mp)], capture_output=True, text=True)
    if mr.returncode != 0:
        subprocess.run(["hdiutil", "detach", dev], check=False)
        raise RuntimeError(f"mount failed: {mr.stderr}")
    shutil.copy2(seed / "user-data", mp / "user-data")
    shutil.copy2(seed / "meta-data", mp / "meta-data")
    subprocess.run(["umount", str(mp)], check=False)
    subprocess.run(["hdiutil", "detach", dev], check=False)
    return img


def build_cidata_iso(lab: Path) -> Path:
    """Build NoCloud CIDATA ISO via macOS hdiutil (no genisoimage required)."""
    seed = lab / "seed"
    iso = lab / "work" / "cx2e-cidata.iso"
    if iso.exists():
        iso.unlink()
    # Volume name MUST be cidata for NoCloud datasource
    cmd = [
        "hdiutil",
        "makehybrid",
        "-iso",
        "-joliet",
        "-default-volume-name",
        "cidata",
        "-o",
        str(iso),
        str(seed),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return iso


def prepare_vars_flash(lab: Path, edk2_code: Path) -> Path:
    vars_path = lab / "work" / "edk2-aarch64-vars.fd"
    if vars_path.is_file():
        return vars_path
    for cand in (
        Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd"),
        Path("/opt/homebrew/opt/qemu/share/qemu/edk2-arm-vars.fd"),
    ):
        if cand.is_file():
            shutil.copy2(cand, vars_path)
            return vars_path
    # blank vars same size as code
    vars_path.write_bytes(b"\x00" * edk2_code.stat().st_size)
    return vars_path


def build_provision_cmd(
    *,
    qemu_bin: str,
    edk2_code: Path,
    edk2_vars: Path,
    disk: Path,
    boot_log: Path,
    pidfile: Path,
    monitor_sock: Path,
    smbios_url: str,
    accel: str,
    cpu: str,
    memory_mb: int = DEFAULT_MEMORY_MB,
    smp: int = DEFAULT_SMP,
    cidata_iso: Optional[Path] = None,
) -> List[str]:
    """Match Device Lab NoCloud-net path; optional VFAT/ISO cidata disk as backup seed."""
    cmd = [
        qemu_bin,
        "-machine",
        f"virt,accel={accel}",
        "-cpu",
        cpu,
        "-smp",
        str(smp),
        "-m",
        str(memory_mb),
        "-drive",
        f"if=pflash,format=raw,readonly=on,file={edk2_code}",
        "-drive",
        f"if=pflash,format=raw,file={edk2_vars}",
        "-drive",
        f"file={disk},if=virtio,format=qcow2",
        "-netdev",
        "user,id=n0",
        "-device",
        "virtio-net-pci,netdev=n0",
        "-device",
        "virtio-rng-pci",
        "-smbios",
        f"type=1,serial=ds=nocloud-net;s={smbios_url}",
        "-serial",
        f"file:{boot_log}",
        "-display",
        "none",
        "-pidfile",
        str(pidfile),
        "-monitor",
        f"unix:{monitor_sock},server,nowait",
        "-daemonize",
        "-no-reboot",
    ]
    # Prefer VFAT img if present alongside iso path naming
    if cidata_iso is not None:
        img = Path(str(cidata_iso).replace(".iso", ".img"))
        seed_path = img if img.is_file() else cidata_iso
        cmd += ["-drive", f"file={seed_path},format=raw,if=virtio,readonly=on"]
    return cmd



def build_graphical_cmd(
    *,
    qemu_bin: str,
    edk2_code: Path,
    edk2_vars: Path,
    disk: Path,
    boot_log: Path,
    pidfile: Path,
    monitor_sock: Path,
    ssh_port: int,
    accel: str,
    cpu: str,
    memory_mb: int = DEFAULT_MEMORY_MB,
    smp: int = DEFAULT_SMP,
) -> List[str]:
    return [
        qemu_bin,
        "-machine",
        f"virt,accel={accel}",
        "-cpu",
        cpu,
        "-smp",
        str(smp),
        "-m",
        str(memory_mb),
        "-drive",
        f"if=pflash,format=raw,readonly=on,file={edk2_code}",
        "-drive",
        f"if=pflash,format=raw,file={edk2_vars}",
        "-drive",
        f"if=none,id=cx2e_disk,file={disk},format=qcow2",
        "-device",
        "virtio-blk-pci,drive=cx2e_disk,bootindex=1",
        "-netdev",
        f"user,id=n0,hostfwd=tcp:127.0.0.1:{ssh_port}-:22",
        "-device",
        "virtio-net-pci,netdev=n0",
        "-device",
        "virtio-rng-pci",
        "-device",
        "virtio-gpu-pci,id=gpu0,max_outputs=1",
        "-device",
        "virtio-keyboard-pci",
        "-device",
        "virtio-tablet-pci",
        "-serial",
        f"file:{boot_log}",
        "-display",
        "none",
        "-pidfile",
        str(pidfile),
        "-monitor",
        f"unix:{monitor_sock},server,nowait",
        "-daemonize",
    ]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _wait_log_sentinel(log: Path, ok: str, fail: str, timeout_s: int) -> Tuple[bool, bool, str]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if log.is_file():
            text = log.read_text(errors="replace")
            if fail in text:
                return False, True, text[-4000:]
            if ok in text:
                return True, False, text[-4000:]
        time.sleep(5)
    tail = log.read_text(errors="replace")[-4000:] if log.is_file() else ""
    return False, False, tail


def run_first_boot_provision(repo: Optional[Path] = None, *, force: bool = False) -> Dict[str, Any]:
    """First boot: cloud-init package install + poweroff."""
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    work = lab / "work"
    work.mkdir(parents=True, exist_ok=True)
    evidence: Dict[str, Any] = {
        "schema": "gunnchos.cx2e.first_boot_provision.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": False,
        "blocker": None,
    }
    marker = work / "PROVISION_COMPLETE.json"
    if marker.is_file() and not force:
        prior = json.loads(marker.read_text())
        if prior.get("ok"):
            evidence.update(prior)
            evidence["reused"] = True
            return evidence

    if force:
        ov_path = lab / "overlays" / "cx2e-aarch64.qcow2"
        if ov_path.is_file():
            ov_path.unlink()
        vars_reset = lab / "work" / "edk2-aarch64-vars.fd"
        if vars_reset.is_file():
            vars_reset.unlink()

    if any_qemu_running():
        evidence["blocker"] = "CX2E_QEMU_ALREADY_RUNNING: only one guest at a time"
        return evidence

    overlay = prepare_overlay(repo)
    if not overlay.get("ok"):
        evidence["blocker"] = overlay.get("blocker")
        evidence["overlay"] = overlay
        return evidence

    keys = ensure_ssh_keypair(lab)
    weston_ini = (lab / "config" / "weston.ini").read_text()
    weston_unit = (lab / "config" / "cx2e-weston.service").read_text()
    cloud = write_cloud_init(lab, ssh_pubkey=keys["public_key"], weston_ini=weston_ini, weston_unit=weston_unit)
    try:
        cidata_iso = rebuild_cidata_vfat(lab)
    except Exception as exc:
        try:
            cidata_iso = build_cidata_iso(lab)
        except Exception as exc2:
            evidence["blocker"] = f"CX2E_CIDATA_SEED_FAILED: vfat={exc}; iso={exc2}"
            return evidence
    cloud["cidata_iso"] = str(cidata_iso)
    prereq = host_prereqs()
    edk2 = Path(prereq["edk2"])
    vars_fd = prepare_vars_flash(lab, edk2)
    accel = prereq["accel"]

    seed_server = SeedHttpServer(directory=Path(cloud["seed_dir"]))
    port = seed_server.start()
    smbios_url = f"http://10.0.2.2:{port}/"
    # Verify seed HTTP locally before guest boot
    try:
        import urllib.request
        ud = urllib.request.urlopen(f"http://127.0.0.1:{port}/user-data", timeout=5).read()
        md = urllib.request.urlopen(f"http://127.0.0.1:{port}/meta-data", timeout=5).read()
        evidence["seed_http_ok"] = bool(ud.startswith(b"#cloud-config") and b"instance-id" in md)
        evidence["seed_http_port"] = port
        if not evidence["seed_http_ok"]:
            seed_server.stop()
            evidence["blocker"] = "CX2E_SEED_HTTP_CONTENT_INVALID"
            return evidence
    except Exception as exc:
        seed_server.stop()
        evidence["blocker"] = f"CX2E_SEED_HTTP_VERIFY_FAILED: {exc}"
        return evidence
    rt = short_runtime_paths("provision")
    boot_log = rt["boot_log"]
    if boot_log.exists():
        boot_log.unlink()
    pidfile = rt["pidfile"]
    mon = rt["monitor"]
    if mon.exists():
        mon.unlink()
    # Mirror paths into lab work for operators
    (work / "runtime_provision.json").write_text(
        __import__("json").dumps({k: str(v) for k, v in rt.items()}, indent=2) + "\n"
    )
    disk = Path(overlay["overlay"])
    cmd = build_provision_cmd(
        qemu_bin=prereq["qemu_system_aarch64"],
        edk2_code=edk2,
        edk2_vars=vars_fd,
        disk=disk,
        boot_log=boot_log,
        pidfile=pidfile,
        monitor_sock=mon,
        smbios_url=smbios_url,
        accel=accel["accel"],
        cpu=accel["cpu"],
        cidata_iso=cidata_iso,
    )
    evidence["qemu_cmd"] = cmd
    evidence["accel"] = accel
    evidence["cloud_init"] = cloud
    evidence["overlay"] = {k: overlay[k] for k in ("ok", "base_sha256", "overlay_sha256", "overlay")}
    (work / "qemu_provision_cmd.json").write_text(json.dumps(cmd, indent=2) + "\n")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        seed_server.stop()
        evidence["blocker"] = f"CX2E_QEMU_START_FAILED: {proc.stderr[-2000:]}"
        evidence["stdout"] = proc.stdout[-2000:]
        return evidence

    # wait for pidfile
    time.sleep(1)
    pid = int(pidfile.read_text().strip()) if pidfile.is_file() else None
    evidence["qemu_pid"] = pid
    ok_seen, fail_seen, tail = _wait_log_sentinel(boot_log, PROVISION_OK, PROVISION_FAIL, PROVISION_TIMEOUT_S)
    evidence["serial_tail"] = tail
    evidence["sentinel_ok"] = ok_seen
    evidence["sentinel_fail"] = fail_seen

    # wait for clean exit after poweroff
    deadline = time.time() + 180
    exited = False
    while time.time() < deadline:
        if pid is None or not _pid_alive(pid):
            exited = True
            break
        time.sleep(2)
    if not exited and pid is not None:
        try:
            os.kill(pid, 15)
            time.sleep(5)
            if _pid_alive(pid):
                os.kill(pid, 9)
        except OSError:
            pass
        evidence["forced_kill"] = True
    seed_server.stop()
    evidence["qemu_exited"] = exited or (pid is not None and not _pid_alive(pid))
    evidence["ok"] = bool(ok_seen and evidence["qemu_exited"] and not fail_seen)
    if not evidence["ok"] and not evidence.get("blocker"):
        if fail_seen:
            evidence["blocker"] = "CX2E_PROVISION_FAIL_SENTINEL"
        elif not ok_seen:
            evidence["blocker"] = "CX2E_PROVISION_TIMEOUT_NO_SENTINEL"
        else:
            evidence["blocker"] = "CX2E_PROVISION_QEMU_EXIT_UNCLEAN"
    marker.write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def wait_ssh(*, port: int, key: Path, timeout_s: int = 300) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        # TCP first
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                pass
        except OSError:
            time.sleep(3)
            continue
        cmd = [
            "ssh",
            "-i",
            str(key),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "BatchMode=yes",
            "-p",
            str(port),
            "gunnchos@127.0.0.1",
            "uname -a",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and "Linux" in r.stdout:
            return True
        time.sleep(3)
    return False


def ssh_exec(key: Path, port: int, remote_cmd: str, *, timeout: int = 120) -> subprocess.CompletedProcess:
    cmd = [
        "ssh",
        "-i",
        str(key),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "BatchMode=yes",
        "-p",
        str(port),
        "gunnchos@127.0.0.1",
        remote_cmd,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def scp_to_guest(key: Path, port: int, local: Path, remote: str) -> subprocess.CompletedProcess:
    cmd = [
        "scp",
        "-i",
        str(key),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-P",
        str(port),
        "-r",
        str(local),
        f"gunnchos@127.0.0.1:{remote}",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600)


def start_graphical_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    work = lab / "work"
    result: Dict[str, Any] = {
        "schema": "gunnchos.cx2e.graphical_boot.v1",
        "ok": False,
        "blocker": None,
        "ssh_port": ssh_port,
    }
    if any_qemu_running():
        result["blocker"] = "CX2E_QEMU_ALREADY_RUNNING"
        return result
    overlay = lab / "overlays" / "cx2e-aarch64.qcow2"
    if not overlay.is_file():
        result["blocker"] = "CX2E_OVERLAY_MISSING"
        return result
    prov = work / "PROVISION_COMPLETE.json"
    if not prov.is_file() or not json.loads(prov.read_text()).get("ok"):
        result["blocker"] = "CX2E_PROVISION_NOT_COMPLETE"
        return result
    prereq = host_prereqs()
    edk2 = Path(prereq["edk2"])
    vars_fd = prepare_vars_flash(lab, edk2)
    accel = prereq["accel"]
    rt = short_runtime_paths("graphical")
    boot_log = rt["boot_log"]
    if boot_log.exists():
        boot_log.unlink()
    pidfile = rt["pidfile"]
    mon = rt["monitor"]
    if mon.exists():
        mon.unlink()
    (work / "runtime_graphical.json").write_text(
        __import__("json").dumps({k: str(v) for k, v in rt.items()}, indent=2) + "\n"
    )
    cmd = build_graphical_cmd(
        qemu_bin=prereq["qemu_system_aarch64"],
        edk2_code=edk2,
        edk2_vars=vars_fd,
        disk=overlay,
        boot_log=boot_log,
        pidfile=pidfile,
        monitor_sock=mon,
        ssh_port=ssh_port,
        accel=accel["accel"],
        cpu=accel["cpu"],
    )
    result["qemu_cmd"] = cmd
    result["accel"] = accel
    (work / "qemu_graphical_cmd.json").write_text(json.dumps(cmd, indent=2) + "\n")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        result["blocker"] = f"CX2E_GRAPHICAL_BOOT_FAILED: {proc.stderr[-2000:]}"
        return result
    time.sleep(1)
    pid = int(pidfile.read_text().strip()) if pidfile.is_file() else None
    result["qemu_pid"] = pid
    keys = ensure_ssh_keypair(lab)
    ssh_ok = wait_ssh(port=ssh_port, key=Path(keys["private"]), timeout_s=420)
    result["ssh_ready"] = ssh_ok
    result["ok"] = bool(ssh_ok and pid and _pid_alive(pid))
    if not result["ok"]:
        result["blocker"] = result.get("blocker") or "CX2E_SSH_WAIT_TIMEOUT"
    result["guest_booted"] = bool(pid and _pid_alive(pid))
    return result


def stop_guest(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = cx2e_lab_root(repo)
    work = lab / "work"
    stopped = []
    pid_candidates = [
        Path("/tmp/cx2e-graphical/qemu.pid"),
        Path("/tmp/cx2e-provision/qemu.pid"),
        work / "qemu-graphical.pid",
        work / "qemu-provision.pid",
    ]
    for pf in pid_candidates:
        if pf.is_file():
            try:
                pid = int(pf.read_text().strip())
                if _pid_alive(pid):
                    keys = lab / "ssh" / "id_ed25519"
                    if "graphical" in str(pf) and keys.is_file():
                        ssh_exec(keys, DEFAULT_SSH_PORT, "sudo poweroff || true", timeout=30)
                        time.sleep(8)
                    if _pid_alive(pid):
                        os.kill(pid, 15)
                        time.sleep(3)
                    if _pid_alive(pid):
                        os.kill(pid, 9)
                    stopped.append(pid)
            except Exception as exc:
                stopped.append(f"error:{exc}")
            try:
                pf.unlink()
            except OSError:
                pass
    return {"stopped": stopped, "any_qemu": any_qemu_running()}


__all__ = [
    "DEVICE_LAB_FORBIDDEN",
    "PROVISION_OK",
    "DEFAULT_SSH_PORT",
    "host_prereqs",
    "prepare_overlay",
    "run_first_boot_provision",
    "start_graphical_guest",
    "stop_guest",
    "ssh_exec",
    "scp_to_guest",
    "ensure_ssh_keypair",
    "any_qemu_running",
    "wait_ssh",
]
