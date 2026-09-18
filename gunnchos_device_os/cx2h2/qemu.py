"""CX2H.2 QEMU helpers — child overlay of CX2H; never kill foreign guests."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2g.lock import acquire_lock, release_lock
from gunnchos_device_os.cx2g.qemu import (
    DEFAULT_MEMORY_MB,
    DEFAULT_SMP,
    DEFAULT_SSH_PORT,
    any_qemu_running,
    build_graphical_cmd,
    ensure_ssh_keypair,
    find_free_tcp_port,
    host_prereqs,
    hmp,
    prepare_vars_flash,
    screendump,
    scp_to_guest,
    sha256_file,
    ssh_exec,
    wait_ssh,
    _pid_alive,
)
from gunnchos_device_os.cx2h2.paths import (
    CX2H_OVERLAY_REL,
    ensure_lab_tree,
    cx2h2_lab_root,
    repo_root_from_here,
)

__all__ = [
    "DEFAULT_SSH_PORT",
    "prepare_overlay",
    "start_graphical_guest",
    "stop_guest",
    "ssh_exec",
    "scp_to_guest",
    "hmp",
    "screendump",
    "ensure_ssh_keypair",
    "sha256_file",
]


def short_runtime_paths(kind: str = "graphical") -> Dict[str, Path]:
    base = Path(f"/tmp/cx2h2-{kind}")
    return {
        "boot_log": base / "qemu_boot.log",
        "pidfile": base / "qemu.pid",
        "monitor": base / "monitor.sock",
        "captures": base / "captures",
        "base": base,
    }


def cx_owned_qemu_running() -> bool:
    for pf in (
        Path("/tmp/cx2h2-graphical/qemu.pid"),
        Path("/tmp/cx2h-graphical/qemu.pid"),
        Path("/tmp/cx2g-graphical/qemu.pid"),
    ):
        if pf.is_file():
            try:
                if _pid_alive(int(pf.read_text().strip())):
                    return True
            except Exception:
                pass
    return False


def prepare_overlay(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    overlay = lab / "overlays" / "cx2h2-aarch64.qcow2"
    parent = repo / CX2H_OVERLAY_REL
    result: Dict[str, Any] = {"ok": False, "overlay": str(overlay), "parent": str(parent)}
    qimg = host_prereqs().get("qemu_img")
    if not qimg:
        result["blocker"] = "CX2H2_QEMU_IMG_MISSING"
        return result
    if not parent.is_file():
        result["blocker"] = "CX2H2_CX2H_OVERLAY_MISSING"
        return result
    if overlay.is_file():
        result["ok"] = True
        result["reused"] = True
        return result
    overlay.parent.mkdir(parents=True, exist_ok=True)
    # Make parent immutable for this child
    try:
        os.chmod(parent, 0o444)
    except OSError:
        pass
    import subprocess

    cmd = [qimg, "create", "-f", "qcow2", "-b", str(parent), "-F", "qcow2", str(overlay)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    result["qemu_img"] = {"cmd": cmd, "returncode": p.returncode, "stderr": (p.stderr or "")[-500:]}
    result["ok"] = p.returncode == 0
    if not result["ok"]:
        result["blocker"] = "CX2H2_OVERLAY_CREATE_FAILED"
    return result


def start_graphical_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    work = lab / "work"
    result: Dict[str, Any] = {
        "schema": "gunnchos.cx2h2.graphical_boot.v1",
        "ok": False,
        "blocker": None,
        "ssh_port": ssh_port,
    }
    if cx_owned_qemu_running():
        # Stale pidfiles from crashed runs can block the slot; wait briefly then
        # clear only our cx2h2 pidfile if the process is dead.
        deadline = time.time() + 60
        while cx_owned_qemu_running() and time.time() < deadline:
            time.sleep(5)
        for pf in (Path("/tmp/cx2h2-graphical/qemu.pid"),):
            if pf.is_file():
                try:
                    pid = int(pf.read_text().strip())
                    if not _pid_alive(pid):
                        pf.unlink(missing_ok=True)
                except Exception:
                    try:
                        pf.unlink()
                    except OSError:
                        pass
        if cx_owned_qemu_running():
            result["blocker"] = "CX2H2_QEMU_SLOT_BUSY"
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
    rt["base"].mkdir(parents=True, exist_ok=True)
    for p in (rt["boot_log"], rt["pidfile"], rt["monitor"]):
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    vnc_port = find_free_tcp_port(5901, 5999)
    vnc_display = vnc_port - 5900
    lock = acquire_lock(
        branch="eng/cx2h2-document-print-recovery-j1-j7",
        repo=str(repo),
        purpose="CX2H2_DOCUMENT_PRINT_RECOVERY",
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
    # Silence unused imports for static checkers that flag DEFAULT_* when cmd builder uses defaults
    _ = (DEFAULT_MEMORY_MB, DEFAULT_SMP)
    graphics = {
        "display_backend": "vnc",
        "bind_address": "127.0.0.1",
        "vnc_display": vnc_display,
        "vnc_tcp_port": vnc_port,
        "graphics_device": "virtio-gpu-pci",
        "monitor_socket": str(rt["monitor"]),
        "machine_type": f"virt,accel={accel['accel']}",
    }
    result["qemu_cmd"] = cmd
    result["graphics"] = graphics
    result["accel"] = accel
    result["runtime"] = {k: str(v) for k, v in rt.items()}
    meta_dir = rt["base"] / "work"
    meta_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in (
        ("qemu_graphical_cmd.json", cmd),
        ("runtime_graphical.json", result["runtime"]),
    ):
        for dest in (meta_dir / name, work / name):
            try:
                dest.write_text(json.dumps(payload, indent=2) + "\n")
                break
            except OSError:
                continue
    import subprocess

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        release_lock(only_if_pid=os.getpid())
        result["blocker"] = f"CX2H2_GRAPHICAL_BOOT_FAILED: {proc.stderr[-2000:]}"
        return result
    time.sleep(1)
    pid = int(rt["pidfile"].read_text().strip()) if rt["pidfile"].is_file() else None
    result["qemu_pid"] = pid
    lock_meta = lock.get("lock") or {}
    lock_meta["qemu_pid"] = pid
    lock_meta["wave"] = "CX2H.2"
    Path("/tmp/gunnchos-cx-qemu.lock").write_text(json.dumps(lock_meta, indent=2) + "\n")
    # Prefer existing CX2H/CX2G lab keys via ensure_ssh_keypair + runtime copy (no private key in tree)
    g_lab = repo / "os_build" / "cx2g_linux_lab" / "ssh"
    h_lab_src = repo / "os_build" / "cx2h_linux_lab" / "ssh"
    h_lab = lab / "ssh"
    tmp_ssh = rt["base"] / "ssh"
    tmp_ssh.mkdir(parents=True, exist_ok=True)
    for src_dir in (h_lab_src, g_lab):
        if not src_dir.is_dir():
            continue
        for name in ("id_ed25519", "id_ed25519.pub"):
            src = src_dir / name
            if not src.is_file():
                continue
            for dst_dir in (h_lab, tmp_ssh):
                dst = dst_dir / name
                if dst.is_file():
                    continue
                try:
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    if name == "id_ed25519":
                        os.chmod(dst, 0o600)
                    break
                except OSError:
                    continue
    try:
        keys = ensure_ssh_keypair(lab)
    except OSError:
        keys = ensure_ssh_keypair(rt["base"])
    key_path = Path(keys["private"])
    if not key_path.is_file() and (tmp_ssh / "id_ed25519").is_file():
        key_path = tmp_ssh / "id_ed25519"
    ssh_ok = wait_ssh(port=ssh_port, key=key_path, timeout_s=480)
    result["ssh_ready"] = ssh_ok
    result["ok"] = bool(ssh_ok and pid and _pid_alive(pid))
    result["guest_booted"] = bool(pid and _pid_alive(pid))
    if not result["ok"]:
        result["blocker"] = result.get("blocker") or "CX2H2_SSH_WAIT_TIMEOUT"
    return result


def stop_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = cx2h2_lab_root(repo)
    stopped = []
    pidfile = Path("/tmp/cx2h2-graphical/qemu.pid")
    if pidfile.is_file():
        try:
            pid = int(pidfile.read_text().strip())
            if _pid_alive(pid):
                keys = lab / "ssh" / "id_ed25519"
                if not keys.is_file():
                    keys = Path("/tmp/cx2h2-graphical/ssh/id_ed25519")
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
    try:
        Path("/tmp/gunnchos-cx-qemu.lock").unlink(missing_ok=True)
    except TypeError:
        # py<3.8 compat
        try:
            Path("/tmp/gunnchos-cx-qemu.lock").unlink()
        except OSError:
            pass
    except OSError:
        pass
    return {"stopped": stopped, "ok": True}
