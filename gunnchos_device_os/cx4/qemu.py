"""CX4 QEMU helpers — campaign overlay on canonical CX2H4; never kill foreign guests."""

from __future__ import annotations

import json
import os
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
from gunnchos_device_os.cx4.canonical import prepare_campaign_overlay, validate_backing_chain
from gunnchos_device_os.cx4.paths import ensure_lab_tree, repo_root_from_here

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
    base = Path(f"/tmp/cx4-{kind}")
    return {
        "boot_log": base / "qemu_boot.log",
        "pidfile": base / "qemu.pid",
        "monitor": base / "monitor.sock",
        "captures": base / "captures",
        "base": base,
    }


def cx_owned_qemu_running() -> bool:
    for pf in (
        Path("/tmp/cx4-graphical/qemu.pid"),
        Path("/tmp/cx3-graphical/qemu.pid"),
        Path("/tmp/cx2h4-graphical/qemu.pid"),
        Path("/tmp/cx2h3-graphical/qemu.pid"),
        Path("/tmp/cx2h2-graphical/qemu.pid"),
        Path("/tmp/cx2h-graphical/qemu.pid"),
        Path("/tmp/cx2g-graphical/qemu.pid"),
    ):
        if pf.is_file():
            try:
                pid = int(pf.read_text().strip())
                if _pid_alive(pid):
                    return True
                pf.unlink(missing_ok=True)
            except Exception:
                try:
                    pf.unlink(missing_ok=True)
                except OSError:
                    pass
    return False


def prepare_overlay(repo: Optional[Path] = None, *, force: bool = False) -> Dict[str, Any]:
    """Fail-closed campaign overlay preflight with full backing-chain validation."""
    repo = repo or repo_root_from_here()
    info = prepare_campaign_overlay(repo, force=force)
    if not info.get("ok"):
        return info
    # Explicit fail-closed preflight
    chain = validate_backing_chain(Path(info["overlay"]))
    info["preflight_chain"] = chain
    if not chain.get("ok"):
        info["ok"] = False
        info["blocker"] = chain.get("blocker") or "CX4_BACKING_CHAIN_BROKEN"
    return info


def start_graphical_guest(repo: Optional[Path] = None, *, ssh_port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    result: Dict[str, Any] = {
        "schema": "gunnchos.cx4.graphical_boot.v1",
        "ok": False,
        "blocker": None,
        "ssh_port": ssh_port,
    }
    if cx_owned_qemu_running():
        deadline = time.time() + 60
        while cx_owned_qemu_running() and time.time() < deadline:
            time.sleep(5)
        if cx_owned_qemu_running():
            result["blocker"] = "CX4_QEMU_SLOT_BUSY"
            return result
    result["foreign_qemu_present"] = any_qemu_running()
    result["foreign_qemu_policy"] = "never_kill; CX lock governs CX slot only"
    overlay_info = prepare_overlay(repo)
    result["overlay"] = {k: overlay_info.get(k) for k in overlay_info if k not in ("create",)}
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
        branch="eng/cx4-human-physical-external-readiness",
        repo=str(repo),
        purpose="CX4_HUMAN_PHYSICAL_EXTERNAL_READINESS",
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
    _ = (DEFAULT_MEMORY_MB, DEFAULT_SMP)
    result["qemu_cmd"] = cmd
    result["graphics"] = {
        "display_backend": "vnc",
        "vnc_display": vnc_display,
        "vnc_tcp_port": vnc_port,
        "monitor_socket": str(rt["monitor"]),
    }
    result["accel"] = accel
    result["runtime"] = {k: str(v) for k, v in rt.items()}
    import subprocess

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        release_lock(only_if_pid=os.getpid())
        result["blocker"] = f"CX4_GRAPHICAL_BOOT_FAILED: {proc.stderr[-2000:]}"
        return result
    time.sleep(1)
    pid = int(rt["pidfile"].read_text().strip()) if rt["pidfile"].is_file() else None
    result["qemu_pid"] = pid
    lock_meta = lock.get("lock") or {}
    lock_meta["qemu_pid"] = pid
    lock_meta["wave"] = "CX4.0"
    Path("/tmp/gunnchos-cx-qemu.lock").write_text(json.dumps(lock_meta, indent=2) + "\n")
    tmp_ssh = rt["base"] / "ssh"
    tmp_ssh.mkdir(parents=True, exist_ok=True)
    for candidate in (
        Path("/tmp/cx3-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h4-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h3-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h2-graphical/ssh/id_ed25519"),
        repo / "os_build" / "cx3_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h4_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h3_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h2_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2g_linux_lab" / "ssh" / "id_ed25519",
    ):
        if candidate.is_file():
            dest = tmp_ssh / "id_ed25519"
            if not dest.is_file():
                try:
                    dest.write_bytes(candidate.read_bytes())
                    dest.chmod(0o600)
                    pub = candidate.with_suffix(candidate.suffix + ".pub")
                    if not pub.is_file():
                        pub = Path(str(candidate) + ".pub")
                    if pub.is_file():
                        (tmp_ssh / "id_ed25519.pub").write_bytes(pub.read_bytes())
                except OSError:
                    pass
            break
    key = tmp_ssh / "id_ed25519"
    if not key.is_file():
        ensure_ssh_keypair(lab)
        key = lab / "ssh" / "id_ed25519"
    ok_ssh = wait_ssh(port=ssh_port, key=key, timeout_s=480)
    result["ssh_ready"] = ok_ssh
    result["guest_booted"] = bool(ok_ssh and pid and _pid_alive(pid))
    result["ok"] = bool(ok_ssh and pid and _pid_alive(pid))
    if not result["ok"]:
        result["blocker"] = "CX4_SSH_TIMEOUT"
    return result


def stop_guest(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    rt = short_runtime_paths("graphical")
    pid = None
    if rt["pidfile"].is_file():
        try:
            pid = int(rt["pidfile"].read_text().strip())
        except Exception:
            pid = None
    owned = False
    if pid and _pid_alive(pid):
        lock_path = Path("/tmp/gunnchos-cx-qemu.lock")
        if lock_path.is_file():
            try:
                meta = json.loads(lock_path.read_text())
                if meta.get("qemu_pid") == pid or meta.get("wave") in ("CX4.0", "CX3.1", "CX2H.4", "CX2H.3"):
                    owned = True
            except Exception:
                owned = True
        else:
            owned = True
    if owned and pid:
        try:
            os.kill(pid, 15)
        except OSError:
            pass
        deadline = time.time() + 30
        while _pid_alive(pid) and time.time() < deadline:
            time.sleep(1)
        if _pid_alive(pid):
            try:
                os.kill(pid, 9)
            except OSError:
                pass
    try:
        release_lock(only_if_pid=os.getpid())
    except Exception:
        pass
    try:
        rt["pidfile"].unlink(missing_ok=True)
    except OSError:
        pass
    return {"ok": True, "stopped_pid": pid if owned else None, "foreign_untouched": not owned}
