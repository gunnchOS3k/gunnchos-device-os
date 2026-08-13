#!/usr/bin/env python3
"""Boot Interactive Development Guest with virtio-gpu and attempt LIVE visual proof.

Honest: only sets LIVE_GUNNCHOS_VISUAL_PASS when screendumps are non-blank and
differ after input. Never uses RFB handshake alone.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISK = ROOT / "os_build/device_lab_interactive_guest/artifacts/interactive-root-aarch64.qcow2"
VARS = ROOT / "os_build/device_lab_interactive_guest/work/debian_cloud_provision/edk2-aarch64-vars.fd"
EDK2 = Path("/opt/homebrew/share/qemu/edk2-aarch64-code.fd")
OUT = ROOT / "artifacts/wp011r/visual"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def ppm_stats(path: Path) -> dict:
    data = path.read_bytes()
    # PPM P6 header
    if not data.startswith(b"P6"):
        return {"ok": False, "reason": "not_ppm", "size": len(data)}
    # find header end
    try:
        header, body = data.split(b"\n255\n", 1)
    except ValueError:
        return {"ok": False, "reason": "bad_ppm_header", "size": len(data)}
    nonzero = sum(1 for b in body if b != 0)
    unique = len(set(body[::max(1, len(body)//5000)])) if body else 0
    return {
        "ok": True,
        "bytes": len(data),
        "body_bytes": len(body),
        "nonzero_bytes": nonzero,
        "nonzero_ratio": (nonzero / len(body)) if body else 0.0,
        "sample_unique": unique,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    evidence = {
        "schema": "gunnchos.wp011r.interactive_guest_live_visual.v1",
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SHIPPING_IMAGE": False,
        "LIVE_GUNNCHOS_VISUAL_PASS": False,
        "RFB_HANDSHAKE_ALONE_ACCEPTED": False,
    }
    if not DISK.is_file():
        evidence["error"] = "interactive_disk_missing"
        (OUT / "LIVE_VISUAL_INTERACTIVE_GUEST.json").write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))
        return 1
    if not EDK2.is_file() or not VARS.is_file():
        evidence["error"] = "edk2_missing"
        (OUT / "LIVE_VISUAL_INTERACTIVE_GUEST.json").write_text(json.dumps(evidence, indent=2) + "\n")
        return 1

    mon = f"/tmp/gdl-live-vis-{os.getpid()}.sock"
    serial = OUT / "interactive_live_serial.log"
    if Path(mon).exists():
        Path(mon).unlink()
    qemu = shutil.which("qemu-system-aarch64")
    cmd = [
        qemu,
        "-machine", "virt,accel=hvf" if platform.system() == "Darwin" else "virt",
        "-cpu", "host",
        "-smp", "4",
        "-m", "4096",
        "-drive", f"if=pflash,format=raw,readonly=on,file={EDK2}",
        "-drive", f"if=pflash,format=raw,file={VARS}",
        "-drive", f"file={DISK},if=virtio,format=qcow2",
        "-netdev", "user,id=n0",
        "-device", "virtio-net-pci,netdev=n0",
        "-device", "virtio-gpu-pci,max_outputs=2",
        "-device", "virtio-keyboard-pci",
        "-device", "virtio-tablet-pci",
        "-display", "none",
        "-vnc", "127.0.0.1:17",
        "-serial", f"file:{serial}",
        "-monitor", f"unix:{mon},server,nowait",
        "-daemonize",
        "-pidfile", str(OUT / "interactive_live.pid"),
    ]
    evidence["qemu_cmd"] = cmd
    subprocess.check_call(cmd)
    time.sleep(25)  # boot

    def monitor(cmd_line: str) -> str:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect(mon)
        s.recv(4096)
        s.sendall((cmd_line + "\n").encode())
        time.sleep(0.5)
        data = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"(qemu)" in chunk and len(data) > 20:
                    break
        except socket.timeout:
            pass
        s.close()
        return data.decode("utf-8", errors="replace")

    # Start weston via serial is hard when daemonized; use guest SSH if cloud-init set password.
    # Fallback: QEMU sendkey + assume autostart — try screendump anyway after weston user service.
    before = OUT / "interactive_fb_before.ppm"
    after = OUT / "interactive_fb_after.ppm"
    monitor(f"screendump {before}")
    time.sleep(1)
    # inject keys: try to get to a TTY and start weston briefly via sendkey is weak;
    # use guest agent if present — else sendkey sequence for root login is unreliable over VNC-only.
    # Prefer SSH: debian cloud often has gunnchos/gunnchos or debian/debian — check seed.
    ssh_ok = False
    for user, pw in (("lab", "lab"), ("debian", "debian"), ("root", "")):
        try:
            r = subprocess.run(
                [
                    "sshpass", "-p", pw, "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=5",
                    "-p", "2222",
                    f"{user}@127.0.0.1",
                    "true",
                ],
                capture_output=True,
                timeout=15,
            )
            if r.returncode == 0:
                ssh_ok = True
                evidence["ssh_user"] = user
                break
        except Exception:
            continue

    # If no forwarded SSH, add note — reboot with hostfwd next time.
    evidence["ssh_ok"] = ssh_ok

    # Input via monitor sendkey regardless
    for key in ["ret", "ret", "t", "e", "s", "t"]:
        monitor(f"sendkey {key}")
        time.sleep(0.05)
    time.sleep(2)
    monitor(f"screendump {after}")
    time.sleep(1)

    st_b = ppm_stats(before) if before.exists() else {"ok": False}
    st_a = ppm_stats(after) if after.exists() else {"ok": False}
    evidence["before"] = st_b
    evidence["after"] = st_a
    nonblank = (
        st_b.get("ok")
        and st_a.get("ok")
        and st_b.get("nonzero_ratio", 0) > 0.01
        and st_a.get("nonzero_ratio", 0) > 0.01
    )
    changed = st_b.get("sha256") != st_a.get("sha256")
    evidence["nonblank_framebuffer"] = bool(nonblank)
    evidence["input_visible_delta"] = bool(changed and nonblank)
    # Without confirmed compositor+app, do not PASS even if nonblank boot splash
    evidence["compositor_confirmed"] = False
    evidence["app_window_confirmed"] = False
    evidence["LIVE_GUNNCHOS_VISUAL_PASS"] = False
    evidence["note"] = (
        "Provisioned interactive disk booted with virtio-gpu. PASS requires confirmed "
        "Weston+app and input-visible delta; boot splash alone is insufficient."
    )

    # shutdown
    try:
        monitor("system_powerdown")
        time.sleep(5)
    except Exception as e:
        evidence["shutdown_error"] = str(e)
    pid_path = OUT / "interactive_live.pid"
    if pid_path.exists():
        try:
            os.kill(int(pid_path.read_text().strip()), 9)
        except Exception:
            pass
    evidence["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT / "LIVE_VISUAL_INTERACTIVE_GUEST.json").write_text(json.dumps(evidence, indent=2) + "\n")
    # also refresh blocker
    (OUT / "LIVE_VISUAL_EVIDENCE.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "LIVE_GUNNCHOS_VISUAL_PASS": evidence["LIVE_GUNNCHOS_VISUAL_PASS"],
        "nonblank": evidence["nonblank_framebuffer"],
        "delta": evidence["input_visible_delta"],
        "before_ratio": st_b.get("nonzero_ratio"),
        "after_ratio": st_a.get("nonzero_ratio"),
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
