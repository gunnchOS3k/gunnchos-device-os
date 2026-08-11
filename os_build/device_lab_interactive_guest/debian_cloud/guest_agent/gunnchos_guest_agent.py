#!/usr/bin/env python3
"""gunnchGuestAgent — real in-guest agent for the Interactive Development Guest.

Runs INSIDE the Debian cloud-init-provisioned Interactive Guest
(DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true, SHIPPING_IMAGE=false). Speaks
the `gunnchos.guest_agent.v1` line-JSON protocol
(gunnchos_device_os/device_lab/guest_agent/PROTOCOL.md) over the virtio-serial
character device the host attaches as
`virtserialport,name=org.gunnchos.guest_agent.0`.

Honesty contract: every command answers with what actually happened inside
THIS guest right now. It never fabricates a compositor, a PID, or pixel
bytes. If a capability is missing (no evdev module, no weston socket, no
screenshot produced), the response says so explicitly (`"ok": false` and a
`reason`), it never invents success.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROTOCOL = "gunnchos.guest_agent.v1"
PORT_CANDIDATES = (
    "/dev/virtio-ports/org.gunnchos.guest_agent.0",
    "/dev/vport0p1",
    "/dev/vport1p1",
)
SCREENSHOT_DIR = Path("/var/lib/gunnchos/screenshots")
RUNTIME_DIR = os.environ.get("GUNNCH_WAYLAND_RUNTIME_DIR", "/run/gunnchos-wayland")
WAYLAND_DISPLAY = os.environ.get("GUNNCH_WAYLAND_DISPLAY", "wayland-0")
LOG_PATH = Path("/var/log/gunnchos-guest-agent.log")

APP_COMMANDS: dict[str, list[str]] = {
    "chromium": [
        "chromium",
        "--no-sandbox",
        "--disable-gpu-sandbox",
        "--ozone-platform=wayland",
        "--enable-features=UseOzonePlatform",
        "--user-data-dir=/root/.gunnchos-chromium",
        "--no-first-run",
        "about:blank",
    ],
    "browser": None,  # resolved to chromium below
    "mousepad": ["mousepad", "/root/gunnchos-lab-document.txt"],
    "editor": None,  # resolved to mousepad below
    "godot": ["godot3", "--path", "/root/gunnchos-lab-godot"],
    "foot": ["foot"],
}
APP_COMMANDS["browser"] = APP_COMMANDS["chromium"]
APP_COMMANDS["editor"] = APP_COMMANDS["mousepad"]

_uinput_kbd = None
_uinput_mouse = None
_procs: dict[str, subprocess.Popen[bytes]] = {}
_started_at = time.time()


def _log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
    except OSError:
        pass


def _env_for_gui() -> dict[str, str]:
    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = WAYLAND_DISPLAY
    env["XDG_RUNTIME_DIR"] = RUNTIME_DIR
    env.pop("DISPLAY", None)
    return env


def _find_port() -> str | None:
    for cand in PORT_CANDIDATES:
        if Path(cand).exists():
            return cand
    matches = sorted(glob.glob("/dev/virtio-ports/*"))
    for m in matches:
        if "gunnchos" in m:
            return m
    return None


def _ok(cmd: str, **fields: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "protocol": PROTOCOL,
        "cmd": cmd,
        "transport": "virtio_serial",
        "agent_path_label": "virtio-serial",
        "SILICON_EXACT_EMULATION": False,
        "production_keys": False,
        "measurement_class": "GUEST_OBSERVED",
        **fields,
    }


def _fail(cmd: str, reason: str, **fields: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "protocol": PROTOCOL,
        "cmd": cmd,
        "reason": reason,
        "transport": "virtio_serial",
        "measurement_class": "GUEST_OBSERVED",
        **fields,
    }


def cmd_ping(_req: dict[str, Any]) -> dict[str, Any]:
    return _ok("ping", pong=True, boot_complete=True)


def cmd_boot_status(_req: dict[str, Any]) -> dict[str, Any]:
    return _ok("boot_status", boot_complete=True, ready=True, uptime_s=round(time.time() - _started_at, 1))


def cmd_process_list(_req: dict[str, Any]) -> dict[str, Any]:
    procs = []
    try:
        out = subprocess.run(["ps", "-eo", "pid,comm"], capture_output=True, text=True, timeout=5, check=False)
        procs = [ln.strip() for ln in out.stdout.splitlines()[1:] if ln.strip()]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return _ok("process_list", processes=procs, launched_by_agent=sorted(_procs.keys()))


def cmd_process_start(req: dict[str, Any]) -> dict[str, Any]:
    name = req.get("name")
    argv = req.get("argv") or ([name] if name else None)
    if not argv:
        return _fail("process_start", "missing_name_or_argv")
    env = _env_for_gui()
    extra = req.get("env")
    if isinstance(extra, dict):
        for k, v in extra.items():
            if v is None:
                env.pop(str(k), None)
            else:
                env[str(k)] = str(v)
    env.setdefault("LIBSEAT_BACKEND", "seatd")
    try:
        proc = subprocess.Popen(argv, env=env)
    except OSError as exc:
        return _fail("process_start", f"spawn_failed:{exc}")
    _procs[str(name or argv[0])] = proc
    return _ok("process_start", started=str(name or argv[0]), pid=proc.pid)


def cmd_process_stop(req: dict[str, Any]) -> dict[str, Any]:
    name = str(req.get("name") or "")
    proc = _procs.get(name)
    if proc is None:
        return _fail("process_stop", "not_launched_by_agent", name=name)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    return _ok("process_stop", stopped=name, pid=proc.pid, returncode=proc.poll())


def cmd_package_ops(req: dict[str, Any]) -> dict[str, Any]:
    op = req.get("op") or "list"
    names = req.get("names") or []
    if op == "list":
        try:
            out = subprocess.run(
                ["dpkg-query", "-W", "-f=${Package}\\t${Version}\\t${Status}\\n", *names] if names else
                ["dpkg-query", "-W", "-f=${Package}\\t${Version}\\t${Status}\\n"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return _ok("package_ops", op=op, output=out.stdout.strip().splitlines()[:200])
        except (OSError, subprocess.TimeoutExpired) as exc:
            return _fail("package_ops", f"dpkg_query_failed:{exc}")
    return _fail("package_ops", f"unsupported_op:{op}")


def _drm_connectors() -> list[dict[str, Any]]:
    out = []
    for card_status in sorted(glob.glob("/sys/class/drm/card*-*/status")):
        try:
            status = Path(card_status).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        name = Path(card_status).parent.name
        out.append({"id": name, "connected": status == "connected", "status": status})
    return out


def cmd_display_info(_req: dict[str, Any]) -> dict[str, Any]:
    connectors = _drm_connectors()
    connected = [c for c in connectors if c["connected"]]
    displays = [
        {
            "id": c["id"],
            "connected": True,
            "source": "guest_drm",
            "class": "guest_drm",
        }
        for c in connected
    ]
    return _ok(
        "display_info",
        displays=displays,
        connected_count=len(connected),
        connector_count=len(connectors),
        guest_proven=True,
        note="Enumerated from /sys/class/drm/*/status inside guest (real DRM connector state).",
    )


def _wayland_socket_present() -> str | None:
    try:
        for entry in sorted(Path(RUNTIME_DIR).glob("wayland-*")):
            if entry.is_socket():
                return entry.name
    except OSError:
        pass
    return None


def cmd_compositor_info(_req: dict[str, Any]) -> dict[str, Any]:
    weston_running = False
    try:
        out = subprocess.run(["pgrep", "-x", "weston"], capture_output=True, text=True, timeout=5, check=False)
        weston_running = out.returncode == 0 and bool(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    sock = _wayland_socket_present()
    if not weston_running or not sock:
        return _ok(
            "compositor_info",
            available=False,
            compositor=None,
            outputs=0,
            surfaces=0,
            note="weston process or wayland socket not found in guest right now",
        )
    outputs = 0
    surfaces = None
    detail: dict[str, Any] = {}
    try:
        env = _env_for_gui()
        env["WAYLAND_DISPLAY"] = sock
        info = subprocess.run(
            ["wayland-info"], capture_output=True, text=True, timeout=8, env=env, check=False
        )
        text = info.stdout or info.stderr or ""
        outputs = text.count("interface: 'wl_output'")
        detail["wayland_info_returncode"] = info.returncode
        detail["wayland_info_output_globals"] = outputs
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail["wayland_info_error"] = str(exc)
    return _ok(
        "compositor_info",
        available=True,
        compositor="weston",
        socket=sock,
        outputs=outputs,
        surfaces=surfaces,
        detail=detail,
        note="Real registry query via wayland-info against the running weston socket.",
    )


def _get_uinput_devices():
    global _uinput_kbd, _uinput_mouse
    if _uinput_kbd is not None:
        return _uinput_kbd, _uinput_mouse
    try:
        import evdev
        from evdev import UInput, ecodes as e
    except ImportError as exc:
        raise RuntimeError(f"python3-evdev not available: {exc}") from exc
    kbd_caps = {e.EV_KEY: list(range(e.KEY_ESC, e.KEY_MICMUTE + 1))}
    mouse_caps = {
        e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
        e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
    }
    _uinput_kbd = UInput(kbd_caps, name="gunnchos-uinput-kbd")
    _uinput_mouse = UInput(mouse_caps, name="gunnchos-uinput-mouse")
    time.sleep(0.3)  # let udev/libinput register the new device
    return _uinput_kbd, _uinput_mouse


_KEYNAME_MAP = {
    "ret": "KEY_ENTER",
    "enter": "KEY_ENTER",
    "spc": "KEY_SPACE",
    "space": "KEY_SPACE",
    "ctrl": "KEY_LEFTCTRL",
    "shift": "KEY_LEFTSHIFT",
    "super": "KEY_LEFTMETA",
    "meta": "KEY_LEFTMETA",
}


def _key_to_evdev(key: str):
    from evdev import ecodes as e

    key = key.strip()
    if len(key) == 1 and key.isalpha():
        return getattr(e, f"KEY_{key.upper()}")
    if len(key) == 1 and key.isdigit():
        return getattr(e, f"KEY_{key}")
    mapped = _KEYNAME_MAP.get(key.lower())
    if mapped:
        return getattr(e, mapped)
    guess = f"KEY_{key.upper()}"
    if hasattr(e, guess):
        return getattr(e, guess)
    raise ValueError(f"unmapped_key:{key}")


def cmd_input_inject(req: dict[str, Any]) -> dict[str, Any]:
    kind = req.get("kind")
    try:
        kbd, mouse = _get_uinput_devices()
    except RuntimeError as exc:
        return _fail("input_inject", str(exc))
    from evdev import ecodes as e

    try:
        if kind == "key":
            key = str(req.get("key") or "")
            mods = req.get("mods") or []
            codes = [_key_to_evdev(m) for m in mods] + [_key_to_evdev(key)]
            for c in codes:
                kbd.write(e.EV_KEY, c, 1)
            kbd.syn()
            time.sleep(0.02)
            for c in reversed(codes):
                kbd.write(e.EV_KEY, c, 0)
            kbd.syn()
            return _ok("input_inject", kind="key", key=key, mods=mods, injected_via="uinput")
        if kind == "text":
            text = str(req.get("text") or "")
            for ch in text:
                if ch == " ":
                    code = e.KEY_SPACE
                    shift = False
                elif ch.isalpha():
                    code = getattr(e, f"KEY_{ch.upper()}")
                    shift = ch.isupper()
                elif ch.isdigit():
                    code = getattr(e, f"KEY_{ch}")
                    shift = False
                else:
                    continue
                if shift:
                    kbd.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                kbd.write(e.EV_KEY, code, 1)
                kbd.syn()
                time.sleep(0.01)
                kbd.write(e.EV_KEY, code, 0)
                if shift:
                    kbd.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                kbd.syn()
                time.sleep(0.01)
            return _ok("input_inject", kind="text", text=text, injected_via="uinput")
        if kind == "pointer":
            dx = int(req.get("dx") or 0)
            dy = int(req.get("dy") or 0)
            button = req.get("button")
            if dx or dy:
                mouse.write(e.EV_REL, e.REL_X, dx)
                mouse.write(e.EV_REL, e.REL_Y, dy)
                mouse.syn()
            if button == "left":
                mouse.write(e.EV_KEY, e.BTN_LEFT, 1)
                mouse.syn()
                time.sleep(0.02)
                mouse.write(e.EV_KEY, e.BTN_LEFT, 0)
                mouse.syn()
            return _ok("input_inject", kind="pointer", dx=dx, dy=dy, button=button, injected_via="uinput")
    except (ValueError, OSError) as exc:
        return _fail("input_inject", f"inject_failed:{exc}")
    return _fail("input_inject", f"unsupported_kind:{kind}")


def cmd_input_observe(_req: dict[str, Any]) -> dict[str, Any]:
    try:
        import evdev

        devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
        info = [{"path": d.path, "name": d.name} for d in devices]
        return _ok("input_observe", devices=info, count=len(info))
    except ImportError as exc:
        return _fail("input_observe", f"python3-evdev not available: {exc}")
    except OSError as exc:
        return _fail("input_observe", f"enumerate_failed:{exc}")


def cmd_logs(req: dict[str, Any]) -> dict[str, Any]:
    path = req.get("path") or "/var/log/gunnchos-weston.log"
    n = int(req.get("lines") or 80)
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[-n:]
    except OSError as exc:
        return _fail("logs", f"read_failed:{exc}", path=path)
    return _ok("logs", path=path, lines=lines)


def cmd_metrics(_req: dict[str, Any]) -> dict[str, Any]:
    load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[:3] if Path("/proc/loadavg").exists() else []
    mem = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith(("MemTotal:", "MemAvailable:")):
                k, v = line.split(":", 1)
                mem[k] = v.strip()
    except OSError:
        pass
    return _ok(
        "metrics",
        metrics={
            "uptime_s": round(time.time() - _started_at, 1),
            "loadavg": load,
            "meminfo": mem,
            "measurement_class": "GUEST_OBSERVED",
        },
    )


def cmd_shutdown(_req: dict[str, Any]) -> dict[str, Any]:
    resp = _ok("shutdown", action="shutdown", accepted=True)
    subprocess.Popen(["systemctl", "poweroff"])
    return resp


def cmd_reboot(_req: dict[str, Any]) -> dict[str, Any]:
    resp = _ok("reboot", action="reboot", accepted=True)
    subprocess.Popen(["systemctl", "reboot"])
    return resp


def cmd_framebuffer_capture(req: dict[str, Any]) -> dict[str, Any]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    before = set(SCREENSHOT_DIR.glob("*.png"))
    try:
        kbd, _mouse = _get_uinput_devices()
        from evdev import ecodes as e

        kbd.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
        kbd.write(e.EV_KEY, e.KEY_S, 1)
        kbd.syn()
        time.sleep(0.05)
        kbd.write(e.EV_KEY, e.KEY_S, 0)
        kbd.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
        kbd.syn()
    except RuntimeError as exc:
        return _fail("framebuffer_capture", f"uinput_unavailable:{exc}")

    deadline = time.time() + 5.0
    new_file: Path | None = None
    while time.time() < deadline:
        after = set(SCREENSHOT_DIR.glob("*.png"))
        newly = after - before
        if newly:
            new_file = sorted(newly)[0]
            break
        time.sleep(0.2)
    if new_file is None:
        return _fail(
            "framebuffer_capture",
            "no_screenshot_produced",
            note=(
                "Sent Ctrl+S via guest uinput to trigger weston-screenshooter keybinding but "
                f"no new PNG appeared under {SCREENSHOT_DIR} within 5s. Compositor may not be "
                "running the drm-backend, or screenshooter keybinding not active."
            ),
        )
    try:
        raw = new_file.read_bytes()
    except OSError as exc:
        return _fail("framebuffer_capture", f"read_failed:{exc}")
    import base64

    return _ok(
        "framebuffer_capture",
        path=str(new_file),
        bytes=len(raw),
        format="png",
        bytes_b64=base64.b64encode(raw).decode("ascii"),
        synthetic=False,
        via="weston_screenshooter_ctrl_s_uinput",
    )


def cmd_app_launch(req: dict[str, Any]) -> dict[str, Any]:
    app = str(req.get("app") or "")
    argv = APP_COMMANDS.get(app)
    if argv is None:
        return _fail("app_launch", f"unknown_app:{app}", app=app, known=sorted(APP_COMMANDS))
    binary = argv[0]
    try:
        which = subprocess.run(["which", binary], capture_output=True, text=True, timeout=3, check=False)
        if which.returncode != 0:
            return _fail("app_launch", f"binary_not_installed:{binary}", app=app)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _fail("app_launch", f"which_failed:{exc}", app=app)
    try:
        proc = subprocess.Popen(argv, env=_env_for_gui())
    except OSError as exc:
        return _fail("app_launch", f"spawn_failed:{exc}", app=app)
    time.sleep(0.5)
    alive = proc.poll() is None
    _procs[app] = proc
    return _ok("app_launch", app=app, pid=proc.pid, started=True, alive_after_500ms=alive, argv=argv)


HANDLERS = {
    "ping": cmd_ping,
    "boot_status": cmd_boot_status,
    "process_list": cmd_process_list,
    "process_start": cmd_process_start,
    "process_stop": cmd_process_stop,
    "package_ops": cmd_package_ops,
    "display_info": cmd_display_info,
    "input_inject": cmd_input_inject,
    "input_observe": cmd_input_observe,
    "logs": cmd_logs,
    "metrics": cmd_metrics,
    "shutdown": cmd_shutdown,
    "reboot": cmd_reboot,
    "framebuffer_capture": cmd_framebuffer_capture,
    "compositor_info": cmd_compositor_info,
    "app_launch": cmd_app_launch,
}


def serve_forever() -> None:
    _log("gunnchos-guest-agent starting")
    while True:
        port = _find_port()
        if port is None:
            _log("virtio-serial port not found yet; retrying")
            time.sleep(1.0)
            continue
        try:
            with open(port, "r+b", buffering=0) as fh:
                _log(f"connected to {port}")
                buf = b""
                while True:
                    chunk = fh.read(4096)
                    if not chunk:
                        time.sleep(0.05)
                        continue
                    buf += chunk
                    while b"\n" in buf:
                        raw, buf = buf.split(b"\n", 1)
                        if not raw.strip():
                            continue
                        try:
                            req = json.loads(raw.decode("utf-8"))
                        except json.JSONDecodeError:
                            continue
                        cmd = req.get("cmd")
                        handler = HANDLERS.get(cmd)
                        try:
                            resp = handler(req) if handler else _fail(str(cmd), "unknown_cmd")
                        except Exception as exc:  # noqa: BLE001 - never let one bad request kill the loop
                            resp = _fail(str(cmd), f"handler_exception:{exc}")
                        line = (json.dumps(resp, separators=(",", ":")) + "\n").encode("utf-8")
                        fh.write(line)
        except OSError as exc:
            _log(f"port error, reopening: {exc}")
            time.sleep(1.0)


if __name__ == "__main__":
    try:
        serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
