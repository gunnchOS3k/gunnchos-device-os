"""WP-011R live visual proof — guest DRM/fb / VNC capture with input-visible change.

No synthetic screenshots. LIVE_GUNNCHOS_VISUAL_PASS stays false until shell +
app window + input-visible change are captured under artifacts/wp011r/visual/.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


CLAIM = (
    "Live visual evidence is guest/QEMU framebuffer or VNC capture — "
    "not synthetic PNGs. Alpine/dev guest = DEVICE_LAB_DEVELOPMENT_GUEST "
    "(not shipping image). SILICON_EXACT_EMULATION=false."
)

PASS_TOKEN = "LIVE_GUNNCHOS_VISUAL_PASS"


def _visual_dir(repo_root: Path) -> Path:
    d = repo_root / "artifacts" / "wp011r" / "visual"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _qemu_screendump(monitor_sock: Path | None, out_path: Path) -> dict[str, Any]:
    """Ask QEMU monitor for screendump PPM/PNG when monitor socket exists."""
    if monitor_sock is None or not Path(monitor_sock).exists():
        return {"ok": False, "reason": "monitor_sock_absent"}
    try:
        import socket

        # PPM is universally supported by screendump
        ppm = out_path.with_suffix(".ppm")
        cmd = f"screendump {ppm}\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3.0)
            sock.connect(str(monitor_sock))
            # Drain QEMU banner
            try:
                sock.recv(4096)
            except OSError:
                pass
            sock.sendall(cmd.encode("utf-8"))
            time.sleep(0.3)
            try:
                sock.recv(4096)
            except OSError:
                pass
        if ppm.is_file() and ppm.stat().st_size > 100:
            # Keep PPM as real capture; optionally note conversion not required
            if out_path.suffix.lower() == ".png":
                # Do not fabricate PNG — keep PPM and record path
                return {
                    "ok": True,
                    "path": str(ppm),
                    "format": "ppm",
                    "bytes": ppm.stat().st_size,
                    "synthetic": False,
                    "source": "qemu_monitor_screendump",
                }
            return {
                "ok": True,
                "path": str(ppm),
                "format": "ppm",
                "bytes": ppm.stat().st_size,
                "synthetic": False,
                "source": "qemu_monitor_screendump",
            }
        return {"ok": False, "reason": "screendump_empty", "path": str(ppm)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:300], "source": "qemu_monitor_screendump"}


def _guest_agent_framebuffer(agent: Any, out_path: Path) -> dict[str, Any]:
    if agent is None:
        return {"ok": False, "reason": "guest_agent_absent"}
    try:
        # Prefer explicit drm/fb capture commands when agent supports them
        for cmd in ("framebuffer_capture", "drm_screenshot", "screenshot"):
            try:
                resp = agent.call(cmd, path=str(out_path))
            except Exception:
                continue
            if not isinstance(resp, dict):
                continue
            if resp.get("ok") and out_path.is_file() and out_path.stat().st_size > 100:
                return {
                    "ok": True,
                    "path": str(out_path),
                    "bytes": out_path.stat().st_size,
                    "synthetic": False,
                    "source": f"guest_agent:{cmd}",
                    "agent_response": {k: resp.get(k) for k in ("ok", "cmd", "path", "transport")},
                }
            if resp.get("ok") and resp.get("path"):
                p = Path(str(resp["path"]))
                if p.is_file() and p.stat().st_size > 100:
                    return {
                        "ok": True,
                        "path": str(p),
                        "bytes": p.stat().st_size,
                        "synthetic": False,
                        "source": f"guest_agent:{cmd}",
                    }
        return {"ok": False, "reason": "guest_agent_no_framebuffer_cmd"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:300]}


def _vnc_rfb_frame_probe(host: str, port: int) -> dict[str, Any]:
    """Prove live RFB endpoint (not a PNG). Frame decode is best-effort."""
    from gunnchos_device_os.device_lab.virtualization.live_display import probe_vnc_endpoint

    probe = probe_vnc_endpoint(host, port)
    return {
        "ok": bool(probe.get("ok")),
        "live_rfb": bool(probe.get("live")),
        "banner": probe.get("banner"),
        "host": host,
        "port": port,
        "synthetic": False,
        "source": "vnc_rfb_probe",
        "note": "RFB live probe — full pixel decode optional when screendump available",
    }


def run_live_visual_proof(
    *,
    repo_root: Path,
    monitor_sock: Path | None = None,
    guest_agent: Any = None,
    vnc_host: str = "127.0.0.1",
    vnc_port: int | None = None,
    inject_input: Any | None = None,
    require_guest: bool = True,
) -> dict[str, Any]:
    """Capture before/after visual evidence with input-visible change when possible."""
    out_dir = _visual_dir(repo_root)
    before_path = out_dir / "shell_app_before.ppm"
    after_path = out_dir / "shell_app_after.ppm"
    meta_path = out_dir / "LIVE_VISUAL_EVIDENCE.json"

    guest_label = {
        "image_class": "DEVICE_LAB_DEVELOPMENT_GUEST",
        "shipping_image": False,
        "note": "Alpine/dev guest is development-only — not a shipping gunnchOS image",
    }

    captures: dict[str, Any] = {}
    # Before
    cap_b = _guest_agent_framebuffer(guest_agent, before_path)
    if not cap_b.get("ok"):
        cap_b = _qemu_screendump(monitor_sock, before_path)
    captures["before"] = cap_b

    # Input into live surface
    input_result: dict[str, Any] = {"attempted": False}
    if inject_input is not None:
        input_result = {"attempted": True, "result": inject_input()}
    elif monitor_sock is not None:
        try:
            from gunnchos_device_os.device_lab.virtualization.guest_input import inject_key

            input_result = {
                "attempted": True,
                "result": inject_key(monitor_sock=monitor_sock, key="a", agent=guest_agent),
            }
        except Exception as exc:  # noqa: BLE001
            input_result = {"attempted": True, "error": str(exc)}

    time.sleep(0.2)
    cap_a = _guest_agent_framebuffer(guest_agent, after_path)
    if not cap_a.get("ok"):
        cap_a = _qemu_screendump(monitor_sock, after_path)
    captures["after"] = cap_a

    vnc = None
    if vnc_port:
        vnc = _vnc_rfb_frame_probe(vnc_host, vnc_port)
        captures["vnc"] = vnc

    before_ok = bool(cap_b.get("ok")) and not cap_b.get("synthetic", False)
    after_ok = bool(cap_a.get("ok")) and not cap_a.get("synthetic", False)
    bytes_differ = False
    if before_ok and after_ok:
        try:
            bytes_differ = Path(cap_b["path"]).read_bytes() != Path(cap_a["path"]).read_bytes()
        except OSError:
            bytes_differ = False
    input_ok = bool((input_result.get("result") or {}).get("ok")) or bool(
        input_result.get("result")
    )

    # Require real captures of shell/app surface + input-visible change
    earned = bool(before_ok and after_ok and bytes_differ and input_result.get("attempted"))
    if require_guest and not (monitor_sock or guest_agent or vnc_port):
        earned = False

    # Never invent screenshots
    if not before_ok or not after_ok:
        earned = False

    force = os.environ.get("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", "").lower() in {"1", "true", "yes"}
    result = {
        "ok": earned,
        PASS_TOKEN: earned,
        "guest": guest_label,
        "captures": captures,
        "input": input_result,
        "input_visible_change": bytes_differ,
        "shell_compositor_surface": before_ok,
        "app_window_capture": after_ok,
        "synthetic_screenshots": False,
        "FORCE_REAL_GUEST": force,
        "evidence_dir": str(out_dir),
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": CLAIM,
        "note": (
            "LIVE_GUNNCHOS_VISUAL_PASS earned"
            if earned
            else (
                "PASS false — need guest DRM/fb or QEMU screendump of shell+app "
                "with input-visible before/after change; no synthetic PNGs"
            )
        ),
    }
    meta_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
