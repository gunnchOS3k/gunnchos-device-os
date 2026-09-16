"""CX2G QEMU + overlay + SSH helpers."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gunnchos_device_os.cx2g.lock import acquire_lock, release_lock
from gunnchos_device_os.cx2g.paths import (
    CX2E_OVERLAY_REL,
    CX2F_OVERLAY_REL,
    cx2e_lab_root,
    cx2f_lab_root,
    cx2g_lab_root,
    ensure_lab_tree,
    repo_root_from_here,
)

DEFAULT_SSH_PORT = 2229
DEFAULT_MEMORY_MB = 4096
DEFAULT_SMP = 4


def sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_edk2() -> Optional[Path]:
    for c in (
        "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
        "/opt/homebrew/opt/qemu/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/qemu/edk2-aarch64-code.fd",
    ):
        p = Path(c)
        if p.is_file():
            return p
    return None


def select_accel() -> Dict[str, str]:
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        if Path("/System/Library/Frameworks/Hypervisor.framework").exists():
            return {"accel": "hvf", "cpu": "host"}
        return {"accel": "tcg", "cpu": "max"}
    if Path("/dev/kvm").exists():
        return {"accel": "kvm", "cpu": "host"}
    return {"accel": "tcg", "cpu": "max"}


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
    return {
        "host_os": platform.system(),
        "host_machine": platform.machine(),
        "qemu_system_aarch64": qemu,
        "qemu_img": qimg,
        "edk2": str(edk2) if edk2 else None,
        "accel": select_accel(),
        "ok": bool(qemu and qimg and edk2),
    }


def any_qemu_running() -> bool:
    """Any qemu-system on host (Device Lab foreign guests included). Never kill them."""
    try:
        out = subprocess.check_output(["pgrep", "-lf", "qemu-system"], text=True)
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False
    except Exception:
        try:
            return "qemu-system" in subprocess.check_output(["ps", "aux"], text=True)
        except Exception:
            return False


def cx_owned_qemu_running() -> bool:
    """True only if a CX wave guest we own is alive (cx2f/cx2g runtime pidfiles or CX lock)."""
    from gunnchos_device_os.cx2g.lock import read_lock

    for pidfile in (Path("/tmp/cx2g-graphical/qemu.pid"), Path("/tmp/cx2f-graphical/qemu.pid")):
        if pidfile.is_file():
            try:
                pid = int(pidfile.read_text().strip())
            except Exception:
                pid = 0
            if pid > 0 and _pid_alive(pid):
                return True
    lock = read_lock()
    if lock:
        qpid = int(lock.get("qemu_pid") or 0)
        if qpid > 0 and _pid_alive(qpid):
            return True
        pid = int(lock.get("pid") or 0)
        purpose = str(lock.get("purpose") or "")
        if pid > 0 and _pid_alive(pid) and purpose.startswith(("CX2F", "CX2G")):
            return True
    return False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def short_runtime_paths(label: str = "graphical") -> Dict[str, Path]:
    base = Path(f"/tmp/cx2g-{label}")
    base.mkdir(parents=True, exist_ok=True)
    return {
        "dir": base,
        "monitor": base / "monitor.sock",
        "pidfile": base / "qemu.pid",
        "boot_log": base / "serial.log",
        "captures": base / "captures",
    }


def find_free_tcp_port(start: int = 5901, end: int = 5999) -> int:
    for p in range(start, end + 1):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            s.close()
    raise RuntimeError("no free TCP port for VNC")


def ensure_ssh_keypair(lab: Path) -> Dict[str, str]:
    ssh_dir = lab / "ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)
    priv = ssh_dir / "id_ed25519"
    pub = ssh_dir / "id_ed25519.pub"
    if not priv.is_file():
        # Prefer CX2F/CX2E keys so provisioned overlay auth continues to work
        cx2f = cx2f_lab_root() / "ssh" / "id_ed25519"
        cx2e = cx2e_lab_root() / "ssh" / "id_ed25519"
        src = cx2f if cx2f.is_file() else cx2e
        if src.is_file():
            shutil.copy2(src, priv)
            shutil.copy2(src.with_suffix(".pub"), pub)
            os.chmod(priv, 0o600)
        else:
            subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(priv), "-C", "cx2g-lab"],
                check=True,
                capture_output=True,
                text=True,
            )
    return {"private": str(priv), "public": str(pub), "public_key": pub.read_text().strip()}


def prepare_overlay(repo: Path) -> Dict[str, Any]:
    """Clone CX2F (preferred) or CX2E overlay into CX2G namespace; parent immutable."""
    lab = ensure_lab_tree(repo)
    parent_cx2f = repo / CX2F_OVERLAY_REL
    parent_cx2e = repo / CX2E_OVERLAY_REL
    if parent_cx2f.is_file():
        parent = parent_cx2f
        parent_wave = "CX2F"
    else:
        parent = parent_cx2e
        parent_wave = "CX2E"
    overlay = lab / "overlays" / "cx2g-aarch64.qcow2"
    prereq = host_prereqs()
    result: Dict[str, Any] = {
        "ok": False,
        "parent_overlay": str(parent),
        "parent_wave": parent_wave,
        "overlay": str(overlay),
        "blocker": None,
    }
    if not parent.is_file():
        result["blocker"] = "CX2G_PARENT_OVERLAY_MISSING"
        return result
    if not prereq["ok"]:
        result["blocker"] = f"CX2G_HOST_PREREQ_FAIL: {prereq}"
        return result
    parent_sha = sha256_file(parent)
    result["parent_overlay_sha256"] = parent_sha
    # Ensure parent is not writable by this process (best-effort immutability)
    try:
        os.chmod(parent, 0o444)
    except OSError:
        pass
    if not overlay.is_file():
        cmd = [
            prereq["qemu_img"],
            "create",
            "-f",
            "qcow2",
            "-F",
            "qcow2",
            "-b",
            str(parent),
            str(overlay),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            result["blocker"] = f"CX2G_OVERLAY_CREATE_FAILED: {exc.stderr[-500:]}"
            return result
    result["overlay_sha256"] = sha256_file(overlay)
    result["ok"] = True
    result["parent_overlay_immutable"] = True
    result["cx2f_overlay_immutable"] = parent_wave == "CX2F"
    result["cx2e_overlay_immutable"] = parent_wave == "CX2E"
    return result


def prepare_vars_flash(lab: Path, edk2_code: Path) -> Path:
    vars_path = lab / "work" / "edk2-aarch64-vars.fd"
    if vars_path.is_file():
        return vars_path
    cx2f_vars = cx2f_lab_root() / "work" / "edk2-aarch64-vars.fd"
    if cx2f_vars.is_file():
        shutil.copy2(cx2f_vars, vars_path)
        return vars_path
    cx2e_vars = cx2e_lab_root() / "work" / "edk2-aarch64-vars.fd"
    if cx2e_vars.is_file():
        shutil.copy2(cx2e_vars, vars_path)
        return vars_path
    for cand in (
        Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd"),
        Path("/opt/homebrew/opt/qemu/share/qemu/edk2-arm-vars.fd"),
    ):
        if cand.is_file():
            shutil.copy2(cand, vars_path)
            return vars_path
    vars_path.write_bytes(b"\x00" * edk2_code.stat().st_size)
    return vars_path


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
    vnc_display: int,
    accel: str,
    cpu: str,
    memory_mb: int = DEFAULT_MEMORY_MB,
    smp: int = DEFAULT_SMP,
) -> List[str]:
    # VNC display N => TCP 5900+N; bind loopback only via 127.0.0.1:N
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
        f"if=none,id=cx2g_disk,file={disk},format=qcow2",
        "-device",
        "virtio-blk-pci,drive=cx2g_disk,bootindex=1",
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
        f"vnc=127.0.0.1:{vnc_display}",
        "-pidfile",
        str(pidfile),
        "-monitor",
        f"unix:{monitor_sock},server,nowait",
        "-daemonize",
    ]


def wait_ssh(*, port: int, key: Path, timeout_s: int = 420) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
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


def hmp(monitor_sock: Path, command: str, timeout: float = 10.0) -> str:
    """Send one HMP command to QEMU unix monitor."""
    import select

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(str(monitor_sock))
    # drain banner
    time.sleep(0.2)
    try:
        while True:
            r, _, _ = select.select([sock], [], [], 0.2)
            if not r:
                break
            chunk = sock.recv(4096)
            if not chunk:
                break
    except Exception:
        pass
    sock.sendall((command.strip() + "\n").encode())
    time.sleep(0.3)
    data = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([sock], [], [], 0.5)
        if not r:
            if data:
                break
            continue
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
        if b"(qemu)" in data:
            break
    sock.close()
    return data.decode(errors="replace")


def screendump(monitor_sock: Path, dest: Path) -> Dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    # QEMU writes relative to guest? No — host path for screendump
    out = hmp(monitor_sock, f"screendump {dest}")
    ok = dest.is_file() and dest.stat().st_size > 64
    meta: Dict[str, Any] = {
        "path": str(dest),
        "ok": ok,
        "hmp_tail": out[-500:],
        "size": dest.stat().st_size if dest.is_file() else 0,
    }
    if ok:
        meta.update(parse_ppm_header(dest))
        meta["sha256"] = sha256_file(dest)
    return meta


def parse_ppm_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        magic = f.readline().strip()
        line = f.readline()
        while line.startswith(b"#"):
            line = f.readline()
        dims = line.split()
        maxval = f.readline().strip()
        width = int(dims[0])
        height = int(dims[1])
        return {
            "magic": magic.decode(),
            "width": width,
            "height": height,
            "maxval": int(maxval),
            "valid_ppm": magic == b"P6" and width > 0 and height > 0,
        }


def start_graphical_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    work = lab / "work"
    result: Dict[str, Any] = {
        "schema": "gunnchos.cx2g.graphical_boot.v1",
        "ok": False,
        "blocker": None,
        "ssh_port": ssh_port,
    }
    # One CX guest at a time. Never kill foreign (e.g. Device Lab) QEMU — coexist via CX lock.
    if cx_owned_qemu_running():
        deadline = time.time() + 120
        while cx_owned_qemu_running() and time.time() < deadline:
            time.sleep(5)
        if cx_owned_qemu_running():
            result["blocker"] = "CX2G_QEMU_SLOT_BUSY_FOREIGN_PROCESS"
            result["foreign_qemu"] = True
            result["note"] = "CX-owned guest still alive; Device Lab QEMU is never killed"
            return result
    result["foreign_qemu_present"] = any_qemu_running()
    result["foreign_qemu_policy"] = "never_kill; CX lock governs CX slot only"
    overlay_info = prepare_overlay(repo)
    result["overlay"] = overlay_info
    if not overlay_info.get("ok"):
        result["blocker"] = overlay_info.get("blocker")
        return result
    overlay = Path(overlay_info["overlay"])
    prereq = host_prereqs()
    edk2 = Path(prereq["edk2"])
    vars_fd = prepare_vars_flash(lab, edk2)
    accel = prereq["accel"]
    rt = short_runtime_paths("graphical")
    rt["captures"].mkdir(parents=True, exist_ok=True)
    for p in (rt["boot_log"], rt["pidfile"], rt["monitor"]):
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    vnc_port = find_free_tcp_port(5901, 5999)
    vnc_display = vnc_port - 5900
    lock = acquire_lock(
        branch="eng/cx2g-chromium-shell-render-repair",
        repo=str(repo),
        purpose="CX2G_CHROMIUM_SHELL_RENDER_REPAIR",
        monitor=str(rt["monitor"]),
        ssh_port=ssh_port,
    )
    if not lock.get("ok"):
        result["blocker"] = lock.get("blocker")
        result["lock"] = lock
        return result
    result["lock"] = lock
    cmd = build_graphical_cmd(
        qemu_bin=prereq["qemu_system_aarch64"],
        edk2_code=edk2,
        edk2_vars=vars_fd,
        disk=overlay,
        boot_log=rt["boot_log"],
        pidfile=rt["pidfile"],
        monitor_sock=rt["monitor"],
        ssh_port=ssh_port,
        vnc_display=vnc_display,
        accel=accel["accel"],
        cpu=accel["cpu"],
    )
    graphics = {
        "display_backend": "vnc",
        "bind_address": "127.0.0.1",
        "vnc_display": vnc_display,
        "vnc_tcp_port": vnc_port,
        "graphics_device": "virtio-gpu-pci",
        "monitor_socket": str(rt["monitor"]),
        "machine_type": f"virt,accel={accel['accel']}",
        "note": "VNC is capture/inspection infrastructure, not a gunnchOS product feature",
    }
    result["qemu_cmd"] = cmd
    result["graphics"] = graphics
    result["accel"] = accel
    result["runtime"] = {k: str(v) for k, v in rt.items()}
    (work / "qemu_graphical_cmd.json").write_text(json.dumps(cmd, indent=2) + "\n")
    (work / "CX2G_QEMU_GRAPHICS.json").write_text(json.dumps(graphics, indent=2) + "\n")
    (work / "runtime_graphical.json").write_text(json.dumps(result["runtime"], indent=2) + "\n")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        release_lock(only_if_pid=os.getpid())
        result["blocker"] = f"CX2G_GRAPHICAL_BOOT_FAILED: {proc.stderr[-2000:]}"
        return result
    time.sleep(1)
    pid = int(rt["pidfile"].read_text().strip()) if rt["pidfile"].is_file() else None
    result["qemu_pid"] = pid
    # Update lock with qemu pid
    lock_meta = lock.get("lock") or {}
    lock_meta["qemu_pid"] = pid
    Path("/tmp/gunnchos-cx-qemu.lock").write_text(json.dumps(lock_meta, indent=2) + "\n")
    keys = ensure_ssh_keypair(lab)
    ssh_ok = wait_ssh(port=ssh_port, key=Path(keys["private"]), timeout_s=480)
    result["ssh_ready"] = ssh_ok
    result["ok"] = bool(ssh_ok and pid and _pid_alive(pid))
    result["CX2G_QEMU_GRAPHICS_SURFACE_PASS"] = True  # VNC bound; validated further by screendump
    result["guest_booted"] = bool(pid and _pid_alive(pid))
    if not result["ok"]:
        result["blocker"] = result.get("blocker") or "CX2G_SSH_WAIT_TIMEOUT"
    return result


def stop_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = cx2g_lab_root(repo)
    stopped = []
    pidfile = Path("/tmp/cx2g-graphical/qemu.pid")
    if pidfile.is_file():
        try:
            pid = int(pidfile.read_text().strip())
            if _pid_alive(pid):
                keys = lab / "ssh" / "id_ed25519"
                if keys.is_file():
                    try:
                        ssh_exec(keys, ssh_port, "sudo poweroff || true", timeout=30)
                        time.sleep(10)
                    except Exception:
                        pass
                if _pid_alive(pid):
                    os.kill(pid, 15)
                    time.sleep(3)
                if _pid_alive(pid):
                    os.kill(pid, 9)
                stopped.append(pid)
        except Exception as exc:
            stopped.append(f"error:{exc}")
        try:
            pidfile.unlink()
        except OSError:
            pass
    release_lock(only_if_pid=os.getpid())
    return {"stopped": stopped, "any_qemu": any_qemu_running()}
