"""CX2H QEMU helpers — CX2H overlay + runtime; never kill foreign guests."""

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
from gunnchos_device_os.cx2h.paths import (
    CX2G_OVERLAY_REL,
    ensure_lab_tree,
    cx2h_lab_root,
    repo_root_from_here,
)

# Re-export for callers
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
    base = Path(f"/tmp/cx2h-{kind}")
    return {
        "boot_log": base / "qemu_boot.log",
        "pidfile": base / "qemu.pid",
        "monitor": base / "monitor.sock",
        "captures": base / "captures",
        "base": base,
    }


def cx_owned_qemu_running() -> bool:
    for pf in (Path("/tmp/cx2h-graphical/qemu.pid"), Path("/tmp/cx2g-graphical/qemu.pid")):
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
    overlay = lab / "overlays" / "cx2h-aarch64.qcow2"
    parent = repo / CX2G_OVERLAY_REL
    result: Dict[str, Any] = {"ok": False, "overlay": str(overlay), "parent": str(parent)}
    qimg = host_prereqs().get("qemu_img")
    if not qimg:
        result["blocker"] = "CX2H_QEMU_IMG_MISSING"
        return result
    if not parent.is_file():
        result["blocker"] = "CX2H_CX2G_OVERLAY_MISSING"
        return result
    if overlay.is_file():
        # refresh backing pointer if empty/stale
        result["ok"] = True
        result["reused"] = True
        return result
    overlay.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess_run_qemu_img(qimg, overlay, parent)
    result["qemu_img"] = proc
    result["ok"] = proc.get("returncode") == 0
    if not result["ok"]:
        result["blocker"] = "CX2H_OVERLAY_CREATE_FAILED"
    return result


def subprocess_run_qemu_img(qimg: str, overlay: Path, parent: Path) -> Dict[str, Any]:
    import subprocess

    cmd = [qimg, "create", "-f", "qcow2", "-b", str(parent), "-F", "qcow2", str(overlay)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"cmd": cmd, "returncode": p.returncode, "stderr": (p.stderr or "")[-500:]}


def start_graphical_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    work = lab / "work"
    result: Dict[str, Any] = {
        "schema": "gunnchos.cx2h.graphical_boot.v1",
        "ok": False,
        "blocker": None,
        "ssh_port": ssh_port,
    }
    if cx_owned_qemu_running():
        deadline = time.time() + 120
        while cx_owned_qemu_running() and time.time() < deadline:
            time.sleep(5)
        if cx_owned_qemu_running():
            result["blocker"] = "CX2H_QEMU_SLOT_BUSY"
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
        branch="eng/cx2h-journey-digital-pass-closure",
        repo=str(repo),
        purpose="CX2H_PORTAL_J3_APP_CENTER",
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
    }
    result["qemu_cmd"] = cmd
    result["graphics"] = graphics
    result["accel"] = accel
    result["runtime"] = {k: str(v) for k, v in rt.items()}
    (work / "qemu_graphical_cmd.json").write_text(json.dumps(cmd, indent=2) + "\n")
    (work / "runtime_graphical.json").write_text(json.dumps(result["runtime"], indent=2) + "\n")
    import subprocess

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        release_lock(only_if_pid=os.getpid())
        result["blocker"] = f"CX2H_GRAPHICAL_BOOT_FAILED: {proc.stderr[-2000:]}"
        return result
    time.sleep(1)
    pid = int(rt["pidfile"].read_text().strip()) if rt["pidfile"].is_file() else None
    result["qemu_pid"] = pid
    lock_meta = lock.get("lock") or {}
    lock_meta["qemu_pid"] = pid
    lock_meta["wave"] = "CX2H"
    Path("/tmp/gunnchos-cx-qemu.lock").write_text(json.dumps(lock_meta, indent=2) + "\n")
    # Ensure SSH key available (copy from CX2G lab if needed)
    g_lab = repo / "os_build" / "cx2g_linux_lab" / "ssh"
    h_lab = lab / "ssh"
    if g_lab.is_dir():
        for name in ("id_ed25519", "id_ed25519.pub"):
            src, dst = g_lab / name, h_lab / name
            if src.is_file() and not dst.is_file():
                shutil.copy2(src, dst)
                os.chmod(dst, 0o600)
    keys = ensure_ssh_keypair(lab)
    ssh_ok = wait_ssh(port=ssh_port, key=Path(keys["private"]), timeout_s=480)
    result["ssh_ready"] = ssh_ok
    result["ok"] = bool(ssh_ok and pid and _pid_alive(pid))
    result["guest_booted"] = bool(pid and _pid_alive(pid))
    if not result["ok"]:
        result["blocker"] = result.get("blocker") or "CX2H_SSH_WAIT_TIMEOUT"
    return result


def stop_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = cx2h_lab_root(repo)
    stopped = []
    pidfile = Path("/tmp/cx2h-graphical/qemu.pid")
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
    return {"stopped": stopped}
