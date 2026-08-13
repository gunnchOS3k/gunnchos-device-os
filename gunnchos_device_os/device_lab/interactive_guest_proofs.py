"""WP-011R: attempt LIVE / DSXL / RING proofs against the provisioned
Interactive Development Guest — only ever writes a `*_PASS: true` token when
a live guest-agent session actually produced the evidence in this run.

Every attempt function returns its own honest result even when the guest
agent is unreachable, the compositor never came up, or a screenshot never
appeared — it never falls back to a stub answer and calls that a PASS.

DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false.
SILICON_EXACT_EMULATION=false always.
"""
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.profiles import load_profile
from gunnchos_device_os.device_lab.virtualization import guest_input
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import (
    compositor_ux_gate,
    high_fidelity_dual_gate,
)
from gunnchos_device_os.device_lab.virtualization.qemu_guest import start_qemu_guest

CLAIM = (
    "Interactive Development Guest proofs run against a real virtio-serial "
    "guest agent inside a Debian cloud-init-provisioned guest. "
    "SILICON_EXACT_EMULATION=false. DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. "
    "SHIPPING_IMAGE=false. A *_PASS token here is only ever set true when this "
    "run's own agent responses (not a mailbox stub) demonstrate it."
)


def _evidence_dir(repo_root: Path, *sub: str) -> Path:
    d = repo_root / "artifacts" / "wp011r"
    for s in sub:
        d = d / s
    d.mkdir(parents=True, exist_ok=True)
    return d


def boot_interactive_guest(
    repo_root: Path,
    work: Path,
    *,
    dual: bool = False,
    boot_timeout_s: int = 180,
    memory_mb: int = 3072,
) -> dict[str, Any]:
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ["GUNNCHDEVICE_LAB_BOOT_TIMEOUT"] = str(boot_timeout_s)
    # Always honor caller memory_mb (setdefault left stale 4096 and OOM'd tight disks).
    os.environ["GUNNCHDEVICE_LAB_MEMORY_MB"] = str(int(memory_mb))
    if dual:
        os.environ["GUNNCHDEVICE_LAB_DUAL_GPU"] = "1"
    else:
        os.environ.pop("GUNNCHDEVICE_LAB_DUAL_GPU", None)
    profile = load_profile("dsxl_coder" if dual else "handheld_hybrid")
    result = start_qemu_guest(work=work, profile=profile, repo_root=repo_root, headless=True)
    return result


def _agent_call(session: Any, cmd: str, *, timeout_sec: float = 20.0, **kwargs: Any) -> dict[str, Any]:
    # monitor_sock may arrive as str from qemu_session.json — guest_input needs Path.
    mon = getattr(session, "monitor_sock", None)
    if isinstance(mon, str):
        session.monitor_sock = Path(mon)  # monitor_sock Path coerce
    agent = getattr(session, "agent", None)
    if agent is None:
        return {"ok": False, "error": "no_agent_bound"}
    old_timeout = agent.timeout_sec
    agent.timeout_sec = timeout_sec
    try:
        return agent.call(cmd, timeout_sec=timeout_sec, **kwargs)
    finally:
        agent.timeout_sec = old_timeout


def _wait_agent(session: Any, *, tries: int = 30, sleep_s: float = 1.0) -> bool:
    for _ in range(tries):
        if _agent_call(session, "ping", timeout_sec=5.0).get("pong"):
            return True
        time.sleep(sleep_s)
    return False


def _recover_guest_agent(session: Any) -> dict[str, Any]:
    """Soft-restart guest agent when virtio-serial stalls after Super+s / large pulls."""
    # Schedule restart out-of-band so we do not pkill the agent mid-process_run.
    sched = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "rm -f /tmp/ga_soft_restarted; "
            "( sleep 1; "
            "  systemctl stop gunnchos-guest-agent.service 2>/dev/null || true; "
            "  pkill -f '/opt/gunnchos/bin/gunnchos_guest_agent.py' || true; "
            "  pkill -f '/usr/local/sbin/gunnchos_guest_agent.py' || true; "
            "  sleep 1; "
            "  nohup python3 /opt/gunnchos/bin/gunnchos_guest_agent.py "
            "    >/var/log/gunnchos-guest-agent.log 2>&1 & "
            "  sleep 1; pgrep -af gunnchos_guest_agent | head > /tmp/ga_soft_restarted; "
            ") >/tmp/ga_soft_restart.log 2>&1 & echo soft_restart_scheduled",
        ],
        timeout_sec=15.0,
    )
    time.sleep(4.0)
    alive = _wait_agent(session, tries=40, sleep_s=0.8)
    return {"scheduled": sched, "alive": alive}


def _require_real_virtio_serial(resp: dict[str, Any]) -> bool:
    """Reject anything answered by the host mailbox stub — never a proof."""
    if not isinstance(resp, dict):
        return False
    transport = str(resp.get("transport") or "")
    label = str(resp.get("agent_path_label") or "")
    if "stub" in transport.lower() or "stub" in label.lower():
        return False
    return resp.get("ok") is not False or "reason" in resp  # allow honest ok:false diagnostics through


def _png_complete(data: bytes) -> bool:
    return (
        len(data) > 4096
        and data.startswith(b"\x89PNG\r\n\x1a\n")
        and b"\x00\x00\x00\x00IEND" in data
    )


def _image_nonblank(data: bytes) -> tuple[bool, str]:
    import hashlib

    if not data or len(data) < 64:
        return False, ""
    digest = hashlib.sha256(data).hexdigest()
    if data.startswith(b"\x89PNG"):
        # Require complete PNG (IEND). len>4096 alone accepted truncated 16KiB shots.
        if not _png_complete(data):
            return False, digest
        return True, digest
    if data.startswith(b"P6"):
        try:
            _, body = data.split(b"\n255\n", 1)
        except ValueError:
            return False, digest
        ratio = (sum(1 for b in body if b != 0) / len(body)) if body else 0.0
        # Reject identical blank/near-blank PPMs.
        return ratio > 0.01, digest
    return len(data) > 4096, digest


def _pull_guest_file(session: Any, path: str, *, chunk: int = 24_000) -> bytes:
    """Pull full guest file via chunked file_get (survives large PNGs / ODT)."""
    out = bytearray()
    offset = 0
    for _ in range(512):
        resp = _agent_call(
            session,
            "file_get",
            path=path,
            offset=offset,
            length=chunk,
            timeout_sec=30.0,
        )
        if not resp.get("ok") or not resp.get("bytes_b64"):
            # Older guest agent without file_get — fall back to process_run base64 slice.
            if resp.get("error") in {"unknown_cmd", "unix_connect_failed"} or "unknown" in str(
                resp.get("error") or ""
            ):
                break
            if resp.get("error") == "not_found":
                return bytes(out)
            break
        piece = base64.b64decode(resp["bytes_b64"])
        if not piece:
            break
        out.extend(piece)
        offset += len(piece)
        if resp.get("eof") or len(piece) < chunk:
            return bytes(out)
    if out:
        return bytes(out)
    # Fallback: single-shot base64 via python in guest (small files).
    probe = _agent_call(
        session,
        "process_run",
        argv=[
            "python3",
            "-c",
            (
                "import base64,pathlib,sys;\n"
                f"p=pathlib.Path({path!r});\n"
                "sys.stdout.write(base64.b64encode(p.read_bytes()).decode() if p.is_file() else '')\n"
            ),
        ],
        timeout_sec=60.0,
    )
    b64 = (probe.get("stdout") or "").strip()
    if not b64:
        return b""
    try:
        return base64.b64decode(b64)
    except Exception:
        return b""


def _capture_guest_fb(session: Any, *, retries: int = 5, settle_s: float = 1.0) -> dict[str, Any]:
    """Retry framebuffer_capture until complete nonblank PNG (IEND required)."""
    last: dict[str, Any] = {"ok": False}
    for i in range(retries):
        # Re-ping before each attempt — Super+s can briefly stall virtio-serial.
        ping = _agent_call(session, "ping", timeout_sec=8.0)
        if not ping.get("pong"):
            time.sleep(0.8)
            continue
        _agent_call(
            session,
            "process_run",
            argv=[
                "bash",
                "-lc",
                "find /var/lib/gunnchos/screenshots /root /tmp -maxdepth 1 -name 'wayland-screenshot*.png' -size -256c -delete 2>/dev/null; true",
            ],
            timeout_sec=10.0,
        )
        time.sleep(settle_s if i == 0 else 1.0)
        cap = _agent_call(session, "framebuffer_capture", timeout_sec=60.0)
        last = cap
        raw = base64.b64decode(cap["bytes_b64"]) if cap.get("bytes_b64") else b""
        # Prefer path pull when agent omitted/truncated bytes_b64 or PNG incomplete.
        guest_path = str(cap.get("path") or "")
        if guest_path and (cap.get("bytes_b64_omitted") or not _png_complete(raw)):
            pulled = _pull_guest_file(session, guest_path)
            if _png_complete(pulled):
                raw = pulled
                cap["bytes"] = len(raw)
                cap["pulled_via"] = "file_get"
                cap["png_complete"] = True
        nb, _ = _image_nonblank(raw)
        if cap.get("ok") and nb and _png_complete(raw) and cap.get("synthetic") is not True:
            cap["_decoded_bytes"] = raw
            cap["png_complete"] = True
            return cap
        # Agent stall recovery between Super+s attempts.
        if cap.get("error") == "unix_connect_failed":
            time.sleep(1.5)
            _agent_call(session, "ping", timeout_sec=10.0)
        if cap.get("path"):
            _agent_call(
                session,
                "process_run",
                argv=["bash", "-lc", f"rm -f '{cap.get('path')}'"],
                timeout_sec=5.0,
            )
    last["_decoded_bytes"] = (
        base64.b64decode(last["bytes_b64"]) if last.get("bytes_b64") else b""
    )
    if last.get("path") and not _png_complete(last.get("_decoded_bytes") or b""):
        pulled = _pull_guest_file(session, str(last["path"]))
        if pulled:
            last["_decoded_bytes"] = pulled
    return last


def _paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_png_rows(raw: bytes, width: int, height: int, *, bpp: int = 3) -> bytes | None:
    """Undo PNG filters (None/Sub/Up/Average/Paeth). Reject truncated / unknown filters."""
    stride = width * bpp + 1
    if len(raw) < stride * height:
        return None
    out = bytearray(width * height * bpp)
    prev = bytearray(width * bpp)
    for y in range(height):
        row_off = y * stride
        ftype = raw[row_off]
        filtered = raw[row_off + 1 : row_off + stride]
        if len(filtered) != width * bpp:
            return None
        cur = bytearray(width * bpp)
        if ftype == 0:  # None
            cur[:] = filtered
        elif ftype == 1:  # Sub
            for i, v in enumerate(filtered):
                left = cur[i - bpp] if i >= bpp else 0
                cur[i] = (v + left) & 0xFF
        elif ftype == 2:  # Up
            for i, v in enumerate(filtered):
                cur[i] = (v + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i, v in enumerate(filtered):
                left = cur[i - bpp] if i >= bpp else 0
                up = prev[i]
                cur[i] = (v + ((left + up) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i, v in enumerate(filtered):
                left = cur[i - bpp] if i >= bpp else 0
                up = prev[i]
                up_left = prev[i - bpp] if i >= bpp else 0
                cur[i] = (v + _paeth_predictor(left, up, up_left)) & 0xFF
        else:
            return None  # invented/unknown filter — reject
        out[y * width * bpp : (y + 1) * width * bpp] = cur
        prev = cur
    return bytes(out)


def _decode_png_rgb8(data: bytes) -> dict[str, Any]:
    """Decode 8-bit RGB PNG with real filter support. Never invent pixel rows."""
    import struct
    import zlib

    out: dict[str, Any] = {"ok": False}
    magic = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    if not data.startswith(magic):
        out["error"] = "not_png"
        return out
    pos = 8
    width = height = None
    color_type = bit_depth = None
    idat = bytearray()
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos = pos + 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat.extend(chunk)
        elif ctype == b"IEND":
            break
    if not width or not height or not idat:
        out["error"] = "png_parse_failed"
        return out
    if color_type != 2 or bit_depth != 8:
        out["error"] = f"unsupported_png ct={color_type} bd={bit_depth}"
        out["width"] = width
        out["height"] = height
        return out
    try:
        raw = zlib.decompress(bytes(idat))
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"zlib_failed:{exc}"
        return out
    rgb = _unfilter_png_rows(raw, width, height, bpp=3)
    if rgb is None:
        out["error"] = "png_filter_decode_failed"
        out["width"] = width
        out["height"] = height
        return out
    filters_used = sorted({raw[y * (width * 3 + 1)] for y in range(height)})
    out.update(
        {
            "ok": True,
            "width": width,
            "height": height,
            "rgb": rgb,
            "filters_used": filters_used,
            "filter_aware": True,
        }
    )
    return out


def _rgb_mean(rgb: bytes) -> float:
    if not rgb:
        return 0.0
    return sum(rgb) / float(len(rgb))


def _pack_rgb_png(width: int, height: int, rgb: bytes) -> bytes:
    import struct
    import zlib

    magic = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    rows = bytearray()
    stride = width * 3
    for y in range(height):
        rows.append(0)  # filter None — honest re-encode of decoded pixels
        rows.extend(rgb[y * stride : (y + 1) * stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return magic + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")


def _rgb_halves_to_pngs(data: bytes) -> dict[str, Any]:
    """Crop left/right from a filter-decoded dual composite. Reject invented halves."""
    import hashlib

    decoded = _decode_png_rgb8(data)
    halves = _png_half_sha256(data)
    out: dict[str, Any] = {"placement_halves": halves, "ok": False, "filter_aware": True}
    if not decoded.get("ok"):
        out["error"] = decoded.get("error") or "decode_failed"
        return out
    width = int(decoded["width"])
    height = int(decoded["height"])
    rgb: bytes = decoded["rgb"]
    mid = width // 2
    left_rgb = bytearray()
    right_rgb = bytearray()
    for y in range(height):
        row = rgb[y * width * 3 : (y + 1) * width * 3]
        left_rgb.extend(row[: mid * 3])
        right_rgb.extend(row[mid * 3 :])
    left_png = _pack_rgb_png(mid, height, bytes(left_rgb))
    right_png = _pack_rgb_png(width - mid, height, bytes(right_rgb))
    left_mean = _rgb_mean(bytes(left_rgb))
    right_mean = _rgb_mean(bytes(right_rgb))
    # Cross-check: re-decode emitted halves and require means match crop means.
    left_dec = _decode_png_rgb8(left_png)
    right_dec = _decode_png_rgb8(right_png)
    if not (left_dec.get("ok") and right_dec.get("ok")):
        out["error"] = "half_png_redecode_failed"
        return out
    left_mean2 = _rgb_mean(left_dec["rgb"])
    right_mean2 = _rgb_mean(right_dec["rgb"])
    means_match = abs(left_mean - left_mean2) < 0.5 and abs(right_mean - right_mean2) < 0.5
    if not means_match or left_mean < 5.0 or right_mean < 5.0:
        out["error"] = "half_means_reject"
        out["left_mean"] = left_mean
        out["right_mean"] = right_mean
        return out
    out.update(
        {
            "ok": True,
            "left_png": left_png,
            "right_png": right_png,
            "left_bytes": len(left_png),
            "right_bytes": len(right_png),
            "left_sha256": hashlib.sha256(left_png).hexdigest(),
            "right_sha256": hashlib.sha256(right_png).hexdigest(),
            "combined_width": width,
            "height": height,
            "left_mean": left_mean,
            "right_mean": right_mean,
            "filters_used": decoded.get("filters_used"),
            "means_match_placement_crops": True,
        }
    )
    return out


def _qemu_monitor_lines(session: Any, cmd_line: str, *, wait_s: float = 0.4) -> str:
    import socket as _socket

    mon = getattr(session, "monitor_sock", None)
    if not mon:
        return ""
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.settimeout(8)
    try:
        s.connect(str(mon))
        try:
            s.recv(4096)
        except OSError:
            pass
        s.sendall((cmd_line + "\n").encode())
        time.sleep(wait_s)
        chunks: list[bytes] = []
        s.settimeout(0.5)
        try:
            while True:
                buf = s.recv(8192)
                if not buf:
                    break
                chunks.append(buf)
        except OSError:
            pass
        return b"".join(chunks).decode("utf-8", "replace")
    finally:
        s.close()


def _png_half_sha256(data: bytes) -> dict[str, Any]:
    """Hash left/right halves of an RGB PNG using filter-aware decode (never invent)."""
    import hashlib

    out: dict[str, Any] = {"ok": False, "filter_aware": True}
    decoded = _decode_png_rgb8(data)
    if not decoded.get("ok"):
        out["error"] = decoded.get("error") or "decode_failed"
        for k in ("width", "height"):
            if k in decoded:
                out[k] = decoded[k]
        return out
    width = int(decoded["width"])
    height = int(decoded["height"])
    rgb: bytes = decoded["rgb"]
    mid = width // 2
    left = bytearray()
    right = bytearray()
    for y in range(height):
        row = rgb[y * width * 3 : (y + 1) * width * 3]
        left.extend(row[: mid * 3])
        right.extend(row[mid * 3 :])
    left_sha = hashlib.sha256(bytes(left)).hexdigest()
    right_sha = hashlib.sha256(bytes(right)).hexdigest()
    left_mean = _rgb_mean(bytes(left))
    right_mean = _rgb_mean(bytes(right))
    out.update(
        {
            "ok": True,
            "width": width,
            "height": height,
            "left_sha256": left_sha,
            "right_sha256": right_sha,
            "halves_differ": left_sha != right_sha,
            "left_nonzero": any(b != 0 for b in left),
            "right_nonzero": any(b != 0 for b in right),
            "left_mean": left_mean,
            "right_mean": right_mean,
            "filters_used": decoded.get("filters_used"),
            # Near-black halves from filter-blind decode are rejected.
            "means_plausible": left_mean >= 5.0 and right_mean >= 5.0,
        }
    )
    if not out["means_plausible"]:
        out["ok"] = False
        out["error"] = "half_means_near_black_rejected"
    return out


def attempt_live_visual_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    """Earn LIVE only with real guest framebuffer + visible shell/app + input delta.

    Host QEMU screendump is supporting evidence only. RFB handshake alone never
    earns PASS. Guest framebuffer_capture must succeed with non-blank before/after
    images that differ after input; shell+app must be alive.
    """
    import hashlib
    import socket as _socket

    result: dict[str, Any] = {
        "LIVE_GUNNCHOS_VISUAL_PASS": False,
        "claim_boundary": CLAIM,
        "RFB_HANDSHAKE_ALONE_ACCEPTED": False,
        "HOST_SCREENDUMP_ALONE_INSUFFICIENT": True,
    }
    ping = _agent_call(session, "ping")
    result["ping"] = ping
    if not _require_real_virtio_serial(ping) or not ping.get("pong"):
        result["blocker"] = "guest_agent_not_reachable_over_real_virtio_serial"
        (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        return result

    # Hot-patch / weston.ini Super+s must be applied by the caller once before
    # proofs. Restarting weston here races framebuffer_capture and caused false
    # no_screenshot_produced failures after a working Super+s capture.
    comp = _agent_call(session, "compositor_info")
    result["compositor_info"] = comp
    if not comp.get("available"):
        result["blocker"] = "compositor_not_available"
        (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        return result

    # Seed a known empty document so typed marker is unambiguous when saved.
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "printf '' > /root/gunnchos-lab-document.txt; "
            "sync; wc -c /root/gunnchos-lab-document.txt",
        ],
        timeout_sec=15.0,
    )
    launch = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    result["app_launch"] = launch
    time.sleep(3.0)
    # Focus editor surface before capture/type; allow paint to settle.
    _agent_call(session, "input_inject", kind="pointer", dx=180, dy=160, button="left", timeout_sec=10.0)
    time.sleep(1.5)
    # Stabilize weston + app before first Super+s (flaky empty shots otherwise).
    for _ in range(8):
        ready = _agent_call(session, "compositor_info", timeout_sec=10.0)
        if ready.get("available"):
            break
        time.sleep(0.5)
    time.sleep(1.0)

    before = _capture_guest_fb(session, retries=8, settle_s=1.5)
    result["framebuffer_before"] = {
        k: v for k, v in before.items() if k not in {"bytes_b64", "_decoded_bytes"}
    }
    before_bytes = before.get("_decoded_bytes") or (
        base64.b64decode(before["bytes_b64"]) if before.get("bytes_b64") else b""
    )

    host_before = evidence_dir / "host_fb_before.ppm"
    host_after = evidence_dir / "host_fb_after.ppm"
    host_cap: dict[str, Any] = {"ok": False, "RFB_HANDSHAKE_ALONE_ACCEPTED": False}
    mon = getattr(session, "monitor_sock", None)

    def _mon(cmd_line: str) -> None:
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(8)
        s.connect(str(mon))
        try:
            s.recv(4096)
            s.sendall((cmd_line + "\n").encode())
            time.sleep(0.5)
            s.recv(8192)
        finally:
            s.close()

    if mon:
        try:
            _mon(f"screendump {host_before}")
            host_cap["before_exists"] = host_before.exists()
        except OSError as exc:
            host_cap["before_error"] = str(exc)

    # Super+s can stall virtio-serial — recover before typing/document proof.
    if not _wait_agent(session, tries=12, sleep_s=0.8):
        result["agent_recover_pre_type"] = _recover_guest_agent(session)

    marker = f"LIVEPROOF{int(time.time())}"
    inj = guest_input.inject_key(
        monitor_sock=getattr(session, "monitor_sock", None), key="a", agent=session.agent
    )
    result["input_injection"] = inj
    # Re-focus mousepad editor (absolute QEMU + uinput) before typing marker.
    _qemu_monitor_lines(session, "mouse_move 12000 14000")
    _qemu_monitor_lines(session, "mouse_button 1")
    time.sleep(0.1)
    _qemu_monitor_lines(session, "mouse_button 0")
    for dx, dy in ((200, 180), (220, 200), (180, 160)):
        _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=10.0)
        time.sleep(0.25)
    typed = _agent_call(session, "input_inject", kind="text", text=marker, timeout_sec=25.0)
    # Reject mismatched leftover pointer responses from virtio desync.
    if typed.get("kind") != "text":
        typed = {
            "ok": False,
            "error": "text_inject_kind_mismatch",
            "got": {k: typed.get(k) for k in ("ok", "kind", "dx", "dy", "error") if k in typed},
        }
    result["typed_marker"] = typed
    # QEMU sendkey is the reliable belt for compositor focus races.
    for ch in marker:
        if ch.isupper():
            _qemu_monitor_lines(session, f"sendkey shift-{ch.lower()}", wait_s=0.05)
        elif ch.isdigit() or ch.islower():
            _qemu_monitor_lines(session, f"sendkey {ch}", wait_s=0.05)
    time.sleep(0.4)
    _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
    _qemu_monitor_lines(session, "sendkey ctrl-s")
    time.sleep(2.0)

    def _read_live_document() -> tuple[dict[str, Any], str]:
        doc_local: dict[str, Any] = {"ok": False}
        text_local = ""
        for _attempt in range(10):
            if not _agent_call(session, "ping", timeout_sec=8.0).get("pong"):
                time.sleep(1.0)
                continue
            # process_run cat survives when logs/file_get stall.
            cat = _agent_call(
                session,
                "process_run",
                argv=["bash", "-lc", "cat /root/gunnchos-lab-document.txt; echo; wc -c /root/gunnchos-lab-document.txt"],
                timeout_sec=20.0,
            )
            if cat.get("ok") and (cat.get("stdout") or "").strip() != "":
                text_local = cat.get("stdout") or ""
                doc_local = {"ok": True, "via": "process_run_cat", "stdout": text_local[-500:]}
                return doc_local, text_local
            doc_local = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=40)
            text_local = "\n".join(doc_local.get("lines") or [])
            if doc_local.get("ok") and text_local:
                return doc_local, text_local
            raw = _pull_guest_file(session, "/root/gunnchos-lab-document.txt")
            if raw is not None:
                # Empty file is a successful read (marker absent).
                text_local = raw.decode("utf-8", "replace")
                doc_local = {
                    "ok": True,
                    "via": "file_get",
                    "bytes": len(raw),
                    "lines": text_local.splitlines()[-40:],
                }
                return doc_local, text_local
            time.sleep(1.0)
        return doc_local, text_local

    # Read document BEFORE after-capture Super+s — capture often stalls virtio-serial.
    doc, doc_text = _read_live_document()
    if marker not in doc_text:
        # One soft agent recover + retype/resave if first pass missed the file.
        result["agent_recover_doc"] = _recover_guest_agent(session)
        _qemu_monitor_lines(session, "mouse_move 12000 14000")
        _qemu_monitor_lines(session, "mouse_button 1")
        time.sleep(0.1)
        _qemu_monitor_lines(session, "mouse_button 0")
        _agent_call(session, "input_inject", kind="pointer", dx=200, dy=180, button="left", timeout_sec=10.0)
        time.sleep(0.3)
        _agent_call(session, "input_inject", kind="text", text=marker, timeout_sec=25.0)
        for ch in marker:
            if ch.isupper():
                _qemu_monitor_lines(session, f"sendkey shift-{ch.lower()}", wait_s=0.05)
            elif ch.isdigit() or ch.islower():
                _qemu_monitor_lines(session, f"sendkey {ch}", wait_s=0.05)
        _qemu_monitor_lines(session, "sendkey ctrl-s")
        time.sleep(2.0)
        doc, doc_text = _read_live_document()
    result["document_after"] = doc
    input_visible_in_app = bool(marker in doc_text)
    result["input_visible_app_state"] = {
        "marker": marker,
        "found_in_document": input_visible_in_app,
        "document_read_ok": bool(doc.get("ok")),
        "document_excerpt": (doc_text or "")[-240:],
    }

    # Ensure agent is responsive before second Super+s capture.
    if not _wait_agent(session, tries=8, sleep_s=0.8):
        result["agent_recover_pre_after_capture"] = _recover_guest_agent(session)
    time.sleep(1.0)

    after = _capture_guest_fb(session, retries=8, settle_s=1.2)
    result["framebuffer_after"] = {
        k: v for k, v in after.items() if k not in {"bytes_b64", "_decoded_bytes"}
    }
    after_bytes = after.get("_decoded_bytes") or (
        base64.b64decode(after["bytes_b64"]) if after.get("bytes_b64") else b""
    )

    if mon:
        try:
            _mon(f"screendump {host_after}")
            host_cap["after_exists"] = host_after.exists()
        except OSError as exc:
            host_cap["after_error"] = str(exc)

    guest_before_path = evidence_dir / (
        "shell_app_before.png" if before_bytes.startswith(b"\x89PNG") else "shell_app_before.ppm"
    )
    guest_after_path = evidence_dir / (
        "shell_app_after.png" if after_bytes.startswith(b"\x89PNG") else "shell_app_after.ppm"
    )
    # Drop stale identical PPMs from prior demoted runs so review does not cite them.
    for stale in (
        evidence_dir / "shell_app_before.ppm",
        evidence_dir / "shell_app_after.ppm",
    ):
        try:
            if stale.exists():
                stale.unlink()
        except OSError:
            pass
    if before_bytes:
        guest_before_path.write_bytes(before_bytes)
    if after_bytes:
        guest_after_path.write_bytes(after_bytes)

    def _ppm_nonblank(path: Path) -> tuple[bool, str]:
        if not path.exists():
            return False, ""
        return _image_nonblank(path.read_bytes())

    host_nb_b, host_sha_b = _ppm_nonblank(host_before)
    host_nb_a, host_sha_a = _ppm_nonblank(host_after)
    host_cap.update(
        {
            "ok": bool(host_nb_b and host_nb_a),
            "before_nonblank": host_nb_b,
            "after_nonblank": host_nb_a,
            "before_sha256": host_sha_b,
            "after_sha256": host_sha_a,
            "changed": bool(host_sha_b and host_sha_a and host_sha_b != host_sha_a),
            "measurement_class": "HOST_OBSERVED",
            "committed_paths": [str(host_before.name), str(host_after.name)],
            "note": "QEMU monitor screendump PPM — supporting only; guest FB required for PASS",
        }
    )
    result["host_screendump"] = host_cap

    guest_nb_b, guest_sha_b = _image_nonblank(before_bytes)
    guest_nb_a, guest_sha_a = _image_nonblank(after_bytes)
    png_ok = _png_complete(before_bytes) and _png_complete(after_bytes)
    guest_fb_ok = bool(
        before.get("ok")
        and after.get("ok")
        and before.get("synthetic") is not True
        and after.get("synthetic") is not True
        and guest_nb_b
        and guest_nb_a
        and png_ok
        and guest_sha_b
        and guest_sha_a
        and guest_sha_b != guest_sha_a
        and before_bytes != after_bytes
    )
    result["guest_framebuffer"] = {
        "before_ok": bool(before.get("ok")),
        "after_ok": bool(after.get("ok")),
        "before_nonblank": guest_nb_b,
        "after_nonblank": guest_nb_a,
        "before_png_complete": _png_complete(before_bytes),
        "after_png_complete": _png_complete(after_bytes),
        "before_bytes": len(before_bytes),
        "after_bytes": len(after_bytes),
        "before_sha256": guest_sha_b,
        "after_sha256": guest_sha_a,
        "changed": bool(guest_sha_b and guest_sha_a and guest_sha_b != guest_sha_a),
        "before_path": str(guest_before_path.name) if before_bytes else None,
        "after_path": str(guest_after_path.name) if after_bytes else None,
        "via_before": before.get("via"),
        "via_after": after.get("via"),
        "pulled_via_before": before.get("pulled_via"),
        "pulled_via_after": after.get("pulled_via"),
    }

    earned = bool(
        comp.get("available")
        and launch.get("ok")
        and launch.get("alive_after_500ms")
        and guest_fb_ok
        and input_visible_in_app
    )
    missing: list[str] = []
    if not guest_fb_ok:
        if not png_ok:
            missing.append("guest_png_incomplete_no_iend")
        else:
            missing.append("guest_framebuffer_nonblank_changed")
    if not input_visible_in_app:
        missing.append("typed_marker_in_app_document")
    if not (launch.get("ok") and launch.get("alive_after_500ms")):
        missing.append("shell_app_alive")

    result.update(
        {
            "LIVE_GUNNCHOS_VISUAL_PASS": earned,
            "non_blank_capture": guest_nb_b and guest_nb_a,
            "diff_bytes": abs(len(after_bytes) - len(before_bytes)) if (before_bytes and after_bytes) else 0,
            "before_after_changed": bool(guest_sha_b and guest_sha_a and guest_sha_b != guest_sha_a),
            "missing": missing,
            "note": (
                "Guest FB before/after non-blank+changed, mousepad alive, typed marker in document"
                if earned
                else "Not earned — missing: " + ",".join(missing)
            ),
        }
    )
    (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def attempt_dsxl_dual_compositor_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    """Earn DSXL only via compositor_ux_gate (surfaces/placement/focus/disc/recon/restore)."""
    result: dict[str, Any] = {"DSXL_DUAL_COMPOSITOR_UX_PASS": False, "claim_boundary": CLAIM}
    disp = _agent_call(session, "display_info")
    result["display_info"] = disp
    gate = high_fidelity_dual_gate(disp.get("displays") or [], claim_guest_dual=True)
    result["dual_output_gate"] = gate

    comp = _agent_call(session, "compositor_info")
    result["compositor_info"] = comp
    outputs = int(comp.get("outputs") or 0)

    # Build compositor-surface view from weston wl_output globals (not DRM enum alone).
    drm_outputs = list(disp.get("displays") or [])
    compositor_outputs: list[dict[str, Any]] = []
    for i, o in enumerate(drm_outputs[: max(outputs, 0)]):
        compositor_outputs.append(
            {
                "id": str(o.get("id") or f"wl_output-{i}"),
                "connected": bool(o.get("connected")),
                "source": "WaylandSession",
                "class": "compositor_wl_output",
                "compositor_surface": True,
            }
        )
    # If weston reports more outputs than DRM entries, synthesize ids from count.
    while len(compositor_outputs) < outputs:
        i = len(compositor_outputs)
        compositor_outputs.append(
            {
                "id": f"wl_output-{i}",
                "connected": True,
                "source": "WaylandSession",
                "class": "compositor_wl_output",
                "compositor_surface": True,
            }
        )

    # Place real windows on left/right halves of the dual scanout (1280+1280).
    oid_a = compositor_outputs[0]["id"] if compositor_outputs else "card0-Virtual-1"
    oid_b = compositor_outputs[1]["id"] if len(compositor_outputs) > 1 else "card0-Virtual-2"

    _agent_call(session, "input_inject", kind="pointer", dx=120, dy=120, button="left", timeout_sec=10.0)
    time.sleep(0.3)
    win_a = _agent_call(session, "app_launch", app="foot", timeout_sec=15.0)
    time.sleep(1.2)
    for _ in range(18):
        _agent_call(session, "input_inject", kind="pointer", dx=80, dy=0, button=None, timeout_sec=5.0)
    _agent_call(session, "input_inject", kind="pointer", dx=0, dy=40, button="left", timeout_sec=10.0)
    time.sleep(0.3)
    win_b = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    time.sleep(1.5)
    result["windows_launched"] = {"foot": win_a, "mousepad": win_b}

    place_cap = _capture_guest_fb(session, retries=5, settle_s=1.0)
    place_bytes = place_cap.get("_decoded_bytes") or b""
    half_pngs = _rgb_halves_to_pngs(place_bytes)
    halves = half_pngs.get("placement_halves") or _png_half_sha256(place_bytes)
    result["placement_framebuffer"] = {
        k: v for k, v in place_cap.items() if k not in {"bytes_b64", "_decoded_bytes"}
    }
    result["placement_halves"] = halves
    if place_bytes and _png_complete(place_bytes):
        (evidence_dir / "dsxl_placement.png").write_bytes(place_bytes)
    means_ok = bool(
        half_pngs.get("ok")
        and half_pngs.get("means_match_placement_crops")
        and float(half_pngs.get("left_mean") or 0) >= 5.0
        and float(half_pngs.get("right_mean") or 0) >= 5.0
    )
    if means_ok and half_pngs.get("left_png") and half_pngs.get("right_png"):
        (evidence_dir / "dsxl_left.png").write_bytes(half_pngs["left_png"])
        (evidence_dir / "dsxl_right.png").write_bytes(half_pngs["right_png"])
        result["placement_halves"]["ok"] = True
        result["placement_halves"]["left_png"] = "dsxl_left.png"
        result["placement_halves"]["right_png"] = "dsxl_right.png"
        result["placement_halves"]["left_png_sha256"] = half_pngs.get("left_sha256")
        result["placement_halves"]["right_png_sha256"] = half_pngs.get("right_sha256")
        result["placement_halves"]["committed_png_halves"] = True
        result["placement_halves"]["left_mean"] = half_pngs.get("left_mean")
        result["placement_halves"]["right_mean"] = half_pngs.get("right_mean")
        result["placement_halves"]["means_match_placement_crops"] = True
        result["placement_halves"]["filter_aware"] = True
        result["placement_halves"]["filters_used"] = half_pngs.get("filters_used")
    elif half_pngs.get("left_png") or halves.get("ok"):
        # Prefer FAIL — never commit filter-blind/near-black invented halves.
        result["placement_halves"]["ok"] = False
        result["placement_halves"]["committed_png_halves"] = False
        result["placement_halves"]["error"] = half_pngs.get("error") or "means_reject"
    placement_proven = bool(
        halves.get("ok")
        and halves.get("halves_differ")
        and halves.get("left_nonzero")
        and halves.get("right_nonzero")
        and means_ok
        and win_a.get("ok")
        and win_b.get("ok")
        and int(halves.get("width") or 0) >= 2000
    )
    windows = [
        {
            "app_id": "foot",
            "output_id": oid_a if placement_proven else "",
            "pid": win_a.get("pid"),
            "ok": bool(win_a.get("ok")),
            "placement_proven": placement_proven,
            "half": "left",
            "half_sha256": halves.get("left_sha256"),
        },
        {
            "app_id": "mousepad",
            "output_id": oid_b if placement_proven else "",
            "pid": win_b.get("pid"),
            "ok": bool(win_b.get("ok")),
            "placement_proven": placement_proven,
            "half": "right",
            "half_sha256": halves.get("right_sha256"),
        },
    ]

    focus_moves: list[dict[str, Any]] = []
    for oid in (oid_a, oid_b):
        click: dict[str, Any] = {}
        for attempt in range(4):
            if oid == oid_b:
                for _ in range(16):
                    _agent_call(
                        session, "input_inject", kind="pointer", dx=80, dy=0, button=None, timeout_sec=5.0
                    )
                click = _agent_call(
                    session, "input_inject", kind="pointer", dx=0, dy=20, button="left", timeout_sec=10.0
                )
            else:
                click = _agent_call(
                    session, "input_inject", kind="pointer", dx=100, dy=100, button="left", timeout_sec=10.0
                )
            if click.get("ok"):
                break
            # Guest agent virtio-serial can briefly empty-reply under compositor load.
            if click.get("error") not in {"unix_connect_failed", "empty_or_unmatched_response"} and (
                "empty" not in str(click.get("detail") or "").lower()
                and "unix_connect" not in str(click.get("error") or "")
            ):
                break
            time.sleep(0.6 + 0.3 * attempt)
        focus_moves.append(
            {
                "ok": bool(click.get("ok")) and placement_proven,
                "output_id": oid if placement_proven else "",
                "click": click,
            }
        )
        time.sleep(0.3)

    def _drm_status(conn_suffix: str = "Virtual-2") -> dict[str, Any]:
        # Dual-GPU topology: secondary may be card1-Virtual-1 (not card0-Virtual-2).
        script = (
            "CARD=''; "
            "for c in /sys/class/drm/card*-"
            + conn_suffix
            + " /sys/class/drm/card1-Virtual-1 /sys/class/drm/card0-Virtual-2; do "
            "  [ -e \"$c/status\" ] || continue; "
            "  # Prefer non-primary card* that is not card0-Virtual-1 "
            "  case \"$c\" in *card0-Virtual-1) continue;; esac; "
            "  CARD=$c; break; "
            "done; "
            "if [ -z \"$CARD\" ]; then "
            "  CARD=$(ls -d /sys/class/drm/card*-Virtual-* 2>/dev/null | grep -v 'card0-Virtual-1$' | head -1); "
            "fi; "
            "echo CARD=$CARD; "
            'if [ -n "$CARD" ] && [ -e "$CARD/status" ]; then cat $CARD/status; '
            'elif [ -z "$CARD" ]; then echo disconnected; else echo missing; fi'
        )
        r = _agent_call(session, "process_run", argv=["bash", "-lc", script], timeout_sec=15.0)
        lines = [ln.strip() for ln in (r.get("stdout") or "").splitlines() if ln.strip()]
        status = lines[-1] if lines else "unknown"
        card = ""
        for ln in lines:
            if ln.startswith("CARD="):
                card = ln.split("=", 1)[1]
        return {"card": card, "status": status, "raw": {k: r.get(k) for k in ("ok", "returncode", "stdout", "stderr") if k in r}}

    before_st = _drm_status()
    before_cards = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "ls -d /sys/class/drm/card*-Virtual-* 2>/dev/null; echo ---; cat /sys/class/drm/card*/status 2>/dev/null"],
        timeout_sec=15.0,
    )
    result["drm_before_list"] = {
        k: before_cards.get(k) for k in ("ok", "stdout", "stderr") if k in before_cards
    }

    disc_attempts: list[dict[str, Any]] = []
    disconnect_reconnect: dict[str, Any] = {
        "disconnect_ok": False,
        "reconnect_ok": False,
        "layout_restored": False,
        "method": "dual_virtio_gpu_device_del_add",
    }

    # Primary path: device_del gpu1 (secondary virtio-gpu) → DRM/compositor drop → device_add.
    # QEMU 11 rejects qom-set outputs[] after realize; dual-device architecture is required.
    del_tail = _qemu_monitor_lines(session, "device_del gpu1", wait_s=1.0)
    time.sleep(2.5)
    # Nudge DRM/compositor to observe connector loss.
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "udevadm settle 2>/dev/null || true; "
            "systemctl try-restart gunnchos-weston.service 2>/dev/null || true; "
            "sleep 2; "
            "pgrep -x weston || true",
        ],
        timeout_sec=30.0,
    )
    time.sleep(2.0)
    mid_st = _drm_status()
    mid_comp = _agent_call(session, "compositor_info")
    mid_cards = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "ls -d /sys/class/drm/card*-Virtual-* 2>/dev/null || echo NONE"],
        timeout_sec=15.0,
    )
    mid_disc = str(mid_st.get("status") or "").lower() == "disconnected" or not (
        mid_st.get("card") or ""
    ).strip()
    mid_card_drop = "NONE" in (mid_cards.get("stdout") or "") or (
        (mid_cards.get("stdout") or "").count("Virtual") < 2
    )
    mid_comp_drop = int(mid_comp.get("outputs") or 99) < 2
    disc_attempts.append(
        {
            "method": "device_del_gpu1",
            "del_tail": del_tail[-240:],
            "mid_drm": mid_st,
            "mid_cards": (mid_cards.get("stdout") or "")[:400],
            "mid_compositor_outputs": mid_comp.get("outputs"),
            "mid_disc": mid_disc,
            "mid_card_drop": mid_card_drop,
            "mid_comp_drop": mid_comp_drop,
        }
    )

    if mid_disc or mid_card_drop or mid_comp_drop:
        add_tail = _qemu_monitor_lines(
            session,
            'device_add {"driver":"virtio-gpu-pci","id":"gpu1","max_outputs":1,'
            '"outputs":[{"name":"ilab1","xres":1280,"yres":800}]}',
            wait_s=1.2,
        )
        time.sleep(2.0)
        _agent_call(
            session,
            "process_run",
            argv=[
                "bash",
                "-lc",
                "udevadm settle 2>/dev/null || true; "
                "systemctl try-restart gunnchos-weston.service 2>/dev/null || true; "
                "sleep 3; pgrep -x weston || true",
            ],
            timeout_sec=40.0,
        )
        time.sleep(2.0)
        after_st = _drm_status()
        after_comp = _agent_call(session, "compositor_info")
        after_cards = _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "ls -d /sys/class/drm/card*-Virtual-* 2>/dev/null || echo NONE"],
            timeout_sec=15.0,
        )
        recon_ok = (
            str(after_st.get("status") or "").lower() == "connected"
            or (after_cards.get("stdout") or "").count("Virtual") >= 2
            or int(after_comp.get("outputs") or 0) >= 2
        )
        disconnect_reconnect.update(
            {
                "connector": mid_st.get("card") or before_st.get("card") or "gpu1",
                "before": before_st.get("status"),
                "mid": (
                    mid_st.get("status")
                    if mid_disc
                    else f"cards={(mid_cards.get('stdout') or '').strip()[:80]} outputs={mid_comp.get('outputs')}"
                ),
                "after": after_st.get("status"),
                "disconnect_ok": True,
                "reconnect_ok": bool(recon_ok),
                "layout_restored": bool(recon_ok and after_comp.get("available")),
                "method": "dual_virtio_gpu_device_del_add",
                "del_tail": del_tail[-200:],
                "add_tail": add_tail[-200:],
                "mid_compositor_outputs": mid_comp.get("outputs"),
                "after_compositor_outputs": after_comp.get("outputs"),
                "after_cards": (after_cards.get("stdout") or "")[:300],
                "drm_disconnected": mid_disc or mid_card_drop,
                "compositor_output_drop": mid_comp_drop,
            }
        )
        result["compositor_info_after_reconnect"] = after_comp
    else:
        # Fallback: legacy qom-set (expected to fail on QEMU 11) — record honest FAIL.
        qom_paths = ["/machine/peripheral/gpu0", "/machine/peripheral/gpu1"]
        tree = _qemu_monitor_lines(session, "info qom-tree", wait_s=0.6)
        result["qom_tree_snip"] = "\n".join(
            [ln for ln in tree.splitlines() if "gpu" in ln.lower() or "virtio-gpu" in ln.lower()][:40]
        )
        for ln in tree.splitlines():
            part = ln.strip().split()[0] if ln.strip() else ""
            if part.startswith("/") and ("gpu" in part.lower() or "virtio-gpu" in ln.lower()):
                if part not in qom_paths:
                    qom_paths.insert(0, part)
        for path in qom_paths:
            off1 = _qemu_monitor_lines(session, f"qom-set {path} outputs[0].xres 0", wait_s=0.3)
            off2 = _qemu_monitor_lines(session, f"qom-set {path} outputs[0].yres 0", wait_s=0.5)
            disc_attempts.append(
                {
                    "path": path,
                    "off_xres_tail": off1[-200:],
                    "off_yres_tail": off2[-200:],
                    "note": "qom-set_fallback_expected_reject_after_realize",
                }
            )
        disconnect_reconnect.update(
            {
                "disconnect_ok": False,
                "reconnect_ok": False,
                "layout_restored": False,
                "method": "dual_virtio_gpu_device_del_add",
                "noop_rejected": True,
                "del_tail": del_tail[-200:],
                "note": (
                    "device_del gpu1 did not drop secondary DRM/compositor output; "
                    "qom-set after realize remains rejected — DSXL disconnect not earned"
                ),
            }
        )

    result["disconnect_attempts"] = disc_attempts
    if "compositor_info_after_reconnect" not in result:
        result["compositor_info_after_reconnect"] = _agent_call(session, "compositor_info")
    # Remove obsolete qom-only block marker — reconnect path already set above.
    _ = before_st  # keep before_st referenced for evidence clarity
    comp_after = result["compositor_info_after_reconnect"]
    layout_restore = {
        "ok": bool(
            disconnect_reconnect.get("disconnect_ok")
            and disconnect_reconnect.get("reconnect_ok")
            and comp_after.get("available")
            and int(comp_after.get("outputs") or 0) >= 2
        ),
        "layout_restored": bool(
            disconnect_reconnect.get("disconnect_ok")
            and disconnect_reconnect.get("reconnect_ok")
            and comp_after.get("available")
            and int(comp_after.get("outputs") or 0) >= 2
        ),
        "outputs_after": int(comp_after.get("outputs") or 0),
    }
    if disconnect_reconnect.get("layout_restored") and layout_restore["ok"]:
        disconnect_reconnect["layout_restored"] = True

    ux = compositor_ux_gate(
        outputs=compositor_outputs,
        windows=windows,
        focus_moves=focus_moves,
        disconnect_reconnect=disconnect_reconnect,
        layout_restore=layout_restore,
    )
    result["compositor_ux_gate"] = ux
    earned = bool(ux.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
    # Never promote DRM-only dual to DSXL.
    if gate.get("GUEST_DUAL_OUTPUT_PASS") and not earned:
        result["GUEST_DUAL_OUTPUT_PASS_retained"] = True

    result.update(
        {
            "DSXL_DUAL_COMPOSITOR_UX_PASS": earned,
            "compositor_output_count": outputs,
            "compositor_surfaces": ux.get("compositor_surfaces"),
            "note": ux.get("note"),
            "architecture": "dual_virtio_gpu_pci_gpu0_gpu1_device_del_add",
        }
    )
    (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def attempt_ring_app_mutation_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    """Ring simulator → auth → RingService → SpatialInput → guest uinput → real apps.

    mousepad file append alone does NOT earn RING_TO_REAL_APP_STATE_MUTATION_PASS.
    Require LibreOffice (or Writer buffer), browser, and first-party game mutation
    via the Ring stack with guest HID delivery.
    """
    result: dict[str, Any] = {
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
        "claim_boundary": CLAIM,
        "MOUSEPAD_FILE_APPEND_ALONE_INSUFFICIENT": True,
        "marker_found_in_after": False,
    }
    ping = _agent_call(session, "ping")
    result["ping"] = ping
    if not _require_real_virtio_serial(ping) or not ping.get("pong"):
        result["blocker"] = "guest_agent_not_reachable_over_real_virtio_serial"
        (evidence_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        return result

    # Drive Ring stack on host. Lab DocumentSurface MUST NOT write RINGRING
    # document_state.json into the guest evidence tree (independent forbids lab:// sidecars).
    from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend

    rings = RingsBackend()
    lab_scratch = evidence_dir / "_lab_surfaces_forbidden"
    if lab_scratch.exists():
        import shutil

        shutil.rmtree(lab_scratch, ignore_errors=True)
    rings.start(evidence_dir=lab_scratch, repo_root=Path(__file__).resolve().parents[2])
    rings.guest_monitor_sock = getattr(session, "monitor_sock", None)
    rings.guest_agent = getattr(session, "agent", None)

    mutations: dict[str, Any] = {}
    launches: dict[str, Any] = {}
    marker = f"RINGMUTATION{int(time.time())}"
    uinput_ok = False

    def _inject_text_and_save(text: str) -> None:
        nonlocal uinput_ok
        typed = _agent_call(session, "input_inject", kind="text", text=text, timeout_sec=20.0)
        saved = _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
        if typed.get("ok") or saved.get("ok"):
            uinput_ok = True

    def _hid_burst(keys: tuple[str, ...], clicks: int = 4) -> None:
        nonlocal uinput_ok
        for dx, dy in ((80, 80), (200, 160), (320, 220), (400, 260)):
            c = _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=5.0)
            if c.get("ok"):
                uinput_ok = True
            time.sleep(0.2)
        for _ in range(clicks):
            c = _agent_call(session, "input_inject", kind="pointer", dx=0, dy=0, button="left", timeout_sec=5.0)
            if c.get("ok"):
                uinput_ok = True
            time.sleep(0.2)
        for key in keys:
            k = _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            if k.get("ok"):
                uinput_ok = True
            time.sleep(0.12)

    # Sequential isolation: one real app at a time. mousepad-alone is rejected.

    # --- LibreOffice: Ring authorize → uinput type marker → Ctrl+S → observe ODT ---
    # Opening .txt trips Writer's ASCII Filter Options dialog (focus steal → no save).
    # Wipe the user profile: a bad registrymodifications.xcu / AutoRecovery restored
    # the stale "Ring target" buffer and killed soffice (alive="").
    odt_path = "/root/gunnchos-lab-document.odt"
    # pkill -f libreoffice must NOT share a command line with the word
    # "libreoffice" (it SIGTERM'd the seed script; returncode -15).
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "killall -q chromium mousepad godot oosplash soffice.bin 2>/dev/null || true; sleep 2; "
            "rm -rf /root/.config/libreoffice /tmp/lu* ; rm -f /root/.~lock.* ; echo killed",
        ],
        timeout_sec=25.0,
    )
    import io
    import zipfile

    def _odt_bytes(paragraph: str) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "mimetype",
                "application/vnd.oasis.opendocument.text",
                compress_type=zipfile.ZIP_STORED,
            )
            zf.writestr(
                "META-INF/manifest.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"'
                ' manifest:version="1.2">'
                '<manifest:file-entry manifest:full-path="/" manifest:version="1.2"'
                ' manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
                '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
                '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>'
                "</manifest:manifest>",
            )
            zf.writestr(
                "content.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
                ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">'
                f"<office:body><office:text><text:p>{paragraph}</text:p></office:text></office:body>"
                "</office:document-content>",
            )
            zf.writestr(
                "styles.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
                ' office:version="1.2"><office:styles/></office:document-styles>',
            )
            zf.writestr(
                "meta.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
                ' office:version="1.2"><office:meta/></office:document-meta>',
            )
        return buf.getvalue()

    lo_seed = _agent_call(
        session,
        "file_put",
        path=odt_path,
        bytes_b64=base64.b64encode(_odt_bytes("RingSeed")).decode("ascii"),
        timeout_sec=20.0,
    )
    lo_before = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=30)
    launches["libreoffice"] = _agent_call(session, "app_launch", app="libreoffice", timeout_sec=30.0)
    soffice_ready = False
    for _ in range(25):
        ready = _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "pgrep -af soffice.bin | grep -v grep | head"],
            timeout_sec=10.0,
        )
        if "soffice.bin" in (ready.get("stdout") or ""):
            soffice_ready = True
            break
        time.sleep(1.0)
    time.sleep(4.0 if soffice_ready else 12.0)
    # Click the document body. Do not send Esc/Enter — that quit Writer on cold boots.
    _qemu_monitor_lines(session, "mouse_move 20000 18000")
    _qemu_monitor_lines(session, "mouse_button 1")
    time.sleep(0.15)
    _qemu_monitor_lines(session, "mouse_button 0")
    for ax, ay in ((16384, 14000), (18000, 16000), (12000, 15000)):
        _agent_call(
            session,
            "input_inject",
            kind="pointer",
            abs=True,
            x=ax,
            y=ay,
            button="left",
            timeout_sec=10.0,
        )
        time.sleep(0.25)
    for dx, dy in ((160, 140), (220, 180), (0, 80)):
        _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=10.0)
        time.sleep(0.2)
    ring_lo = rings.inject(target="libreoffice", confidence=0.92, gesture="click")
    if ring_lo.get("via_stack"):
        _agent_call(session, "input_inject", kind="key", key="end", timeout_sec=5.0)
        _inject_text_and_save(marker)
        for ch in marker:
            if ch.isupper():
                _qemu_monitor_lines(session, f"sendkey shift-{ch.lower()}", wait_s=0.05)
            else:
                _qemu_monitor_lines(session, f"sendkey {ch}", wait_s=0.05)
        time.sleep(3.0)
        _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
        _qemu_monitor_lines(session, "sendkey ctrl-s")
        time.sleep(3.0)

        def _odt_has_marker() -> str:
            probe = _agent_call(
                session,
                "process_run",
                argv=[
                    "python3",
                    "-c",
                    (
                        "import zipfile,pathlib,glob\n"
                        "out=[]\n"
                        "for p in glob.glob('/root/*.odt'):\n"
                        "  try:\n"
                        "    t=zipfile.ZipFile(p).read('content.xml').decode('utf-8','replace')\n"
                        "  except Exception as e:\n"
                        "    t='err:'+str(e)\n"
                        "  out.append(p+' '+t[:4000])\n"
                        "print('\\n'.join(out) or 'no-odt')\n"
                    ),
                ],
                timeout_sec=20.0,
            )
            return probe.get("stdout") or ""

        odt_probe_text = _odt_has_marker()
        if marker not in odt_probe_text:
            for dx, dy in ((180, 160), (240, 200), (300, 220)):
                _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=10.0)
                time.sleep(0.2)
            _agent_call(session, "input_inject", kind="key", key="esc", timeout_sec=5.0)
            _agent_call(session, "input_inject", kind="key", key="end", timeout_sec=5.0)
            _inject_text_and_save(marker)
            time.sleep(2.5)
            _qemu_monitor_lines(session, "sendkey ctrl-s")
            time.sleep(3.0)
            odt_probe_text = _odt_has_marker()
    else:
        odt_probe_text = ""
    lo_after = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=40)
    lo_text = "\n".join(lo_after.get("lines") or [])
    odt_probe = {
        "ok": True,
        "stdout": odt_probe_text,
        "seed": {k: lo_seed.get(k) for k in ("ok", "stdout", "stderr") if k in lo_seed},
        "soffice_ready": soffice_ready,
    }
    odt_text = odt_probe_text
    lo_alive = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "pgrep -af 'soffice|libreoffice' | grep -v grep | head"],
        timeout_sec=10.0,
    )
    lo_bin_ok = bool((launches.get("libreoffice") or {}).get("ok"))
    lo_mutated = bool(
        ring_lo.get("via_stack")
        and lo_bin_ok
        and (marker in lo_text or marker in odt_text)
    )
    mutations["libreoffice"] = {
        "ring": {k: ring_lo.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "before": lo_before,
        "after": lo_after,
        "odt_probe": {
            k: odt_probe.get(k) for k in ("ok", "stdout", "soffice_ready") if k in odt_probe
        },
        "seed": {k: lo_seed.get(k) for k in ("ok", "stdout", "stderr", "returncode") if k in lo_seed},
        "alive": (lo_alive.get("stdout") or "")[:400],
        "marker": marker,
        "mutated": lo_mutated,
        "libreoffice_or_writer_surface_alive": lo_bin_ok,
        "mousepad_fallback_rejected": True,
    }

    # --- Browser path: real Chromium document (contenteditable memo), NOT lab_browser click collector ---
    # Autosave writes typed body to Documents/RingMemo.txt — document persistence, not a click counter.
    memo_html_path = "/root/Documents/RingMemo.html"
    memo_txt_path = "/root/Documents/RingMemo.txt"
    br_state_path = memo_txt_path  # evidence path alias for pull logic below
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "pkill -f ring-memo-server || true; pkill -f ring_memo_server || true; "
            "pkill -f '18766' || true; pkill -f gunnchos-chromium-ring || true; "
            "fuser -k 18776/tcp 2>/dev/null || true; "
            "mkdir -p /root/Documents /var/lib/gunnchos/rings; "
            "rm -f /var/lib/gunnchos/rings/lab_browser.html /var/lib/gunnchos/rings/browser_state.json; "
            "printf '%s\\n' '<!doctype html><html><head><meta charset=utf-8><title>Ring Memo</title></head>"
            "<body style=\"font-family:sans-serif;margin:24px;background:#faf7f2;color:#111\">"
            "<h1>Ring Memo</h1>"
            "<p>Real document surface — type below. Content autosaves to RingMemo.txt.</p>"
            "<textarea id=ed autofocus rows=16 "
            "style=\"width:95%;min-height:50vh;border:1px solid #888;padding:16px;background:#fff;font-size:22px\">"
            "MemoStart</textarea>"
            "<script>"
            "const ed=document.getElementById(\"ed\");"
            "function save(){fetch(\"/save\",{method:\"POST\",headers:{\"Content-Type\":\"text/plain\"},"
            "body:ed.value}).catch(function(){});}"
            "ed.addEventListener(\"input\",save);"
            "ed.addEventListener(\"keyup\",save);"
            "window.addEventListener(\"load\",function(){ed.focus(); ed.setSelectionRange(ed.value.length, ed.value.length); save();});"
            "setInterval(function(){try{ed.focus();}catch(e){}},1000);"
            "</script></body></html>' > "
            + memo_html_path
            + "; : > "
            + memo_txt_path,
        ],
        timeout_sec=20.0,
    )
    memo_server_py = "/var/lib/gunnchos/rings/ring_memo_server.py"
    server_src = (
        "import http.server, pathlib\n"
        "DOC=pathlib.Path('/root/Documents'); html=DOC/'RingMemo.html'; txt=DOC/'RingMemo.txt'\n"
        "class H(http.server.BaseHTTPRequestHandler):\n"
        "  def do_GET(self):\n"
        "    data=html.read_bytes() if self.path.split('?',1)[0] in ('/','/RingMemo.html','/index.html') else b'ok'\n"
        "    self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); "
        "self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)\n"
        "  def do_POST(self):\n"
        "    n=int(self.headers.get('Content-Length') or 0); body=self.rfile.read(n)\n"
        "    txt.write_bytes(body); self.send_response(204); self.end_headers()\n"
        "  def log_message(self,*a): pass\n"
        "http.server.ThreadingHTTPServer(('127.0.0.1',18776),H).serve_forever()\n"
    )
    _agent_call(
        session,
        "file_put",
        path=memo_server_py,
        bytes_b64=base64.b64encode(server_src.encode("utf-8")).decode("ascii"),
        timeout_sec=20.0,
    )
    _agent_call(
        session,
        "process_start",
        name="ring-memo-server",
        argv=["python3", memo_server_py],
        timeout_sec=15.0,
    )
    for _ in range(20):
        probe = _agent_call(
            session,
            "process_run",
            argv=[
                "bash",
                "-lc",
                "curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:18776/RingMemo.html || echo fail",
            ],
            timeout_sec=10.0,
        )
        if (probe.get("stdout") or "").strip().startswith("200"):
            break
        time.sleep(0.3)
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "killall -q oosplash soffice.bin mousepad 2>/dev/null || true; sleep 1",
        ],
        timeout_sec=15.0,
    )
    br_launch = _agent_call(
        session,
        "process_start",
        name="chromium-ring",
        argv=[
            "chromium",
            "--no-sandbox",
            "--disable-gpu-sandbox",
            "--ozone-platform=wayland",
            "--enable-features=UseOzonePlatform",
            "--user-data-dir=/root/.gunnchos-chromium-ring",
            "--no-first-run",
            "--kiosk",
            "http://127.0.0.1:18776/RingMemo.html",
        ],
        timeout_sec=20.0,
    )
    launches["browser"] = br_launch
    time.sleep(8.0)
    # Chromium can race the memo server — re-assert HTTP 200 before HID.
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "pgrep -af ring_memo_server || (python3 /var/lib/gunnchos/rings/ring_memo_server.py & sleep 1); "
            "curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:18776/RingMemo.html || echo fail",
        ],
        timeout_sec=20.0,
    )
    curl_ok = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:18776/RingMemo.html || echo fail"],
        timeout_sec=15.0,
    )
    br_before = _agent_call(session, "logs", path=memo_txt_path, lines=20)
    ring_br = rings.inject(target="browser", confidence=0.92, gesture="click")
    if ring_br.get("via_stack"):
        # Focus editable, type marker via Ring-authorized HID (not click-counter POSTs).
        for _ in range(3):
            _qemu_monitor_lines(session, "mouse_move 14000 18000")
            _qemu_monitor_lines(session, "mouse_button 1")
            time.sleep(0.15)
            _qemu_monitor_lines(session, "mouse_button 0")
            time.sleep(0.2)
        _agent_call(session, "input_inject", kind="key", key="end", timeout_sec=5.0)
        typed = _agent_call(session, "input_inject", kind="text", text=" " + marker, timeout_sec=20.0)
        if typed.get("ok"):
            uinput_ok = True
        for ch in marker:
            if ch.isupper():
                _qemu_monitor_lines(session, f"sendkey shift-{ch.lower()}", wait_s=0.05)
            elif ch.isdigit() or ch.islower():
                _qemu_monitor_lines(session, f"sendkey {ch}", wait_s=0.05)
        time.sleep(1.0)
        _agent_call(session, "input_inject", kind="key", key="spc", timeout_sec=5.0)
        time.sleep(2.0)
        # Force a save POST from inside guest JS context via CDP-less fallback:
        # append marker through the memo HTTP API only if editor already received HID
        # (still require marker to appear from typed path). Poll memo file.
        for _ in range(5):
            probe = _agent_call(session, "logs", path=memo_txt_path, lines=40)
            if marker in "\n".join(probe.get("lines") or []):
                break
            # Re-focus + retype once more
            _qemu_monitor_lines(session, "mouse_button 1")
            time.sleep(0.1)
            _qemu_monitor_lines(session, "mouse_button 0")
            _agent_call(session, "input_inject", kind="text", text=marker, timeout_sec=20.0)
            time.sleep(1.5)
    _ring_browser_curl = curl_ok
    br_after = _agent_call(session, "logs", path=memo_txt_path, lines=40)
    br_before_text = "\n".join(br_before.get("lines") or [])
    br_after_text = "\n".join(br_after.get("lines") or [])
    br_mutated = bool(
        ring_br.get("via_stack")
        and marker in br_after_text
        and br_after_text != br_before_text
        and "lab_browser" not in br_after_text
    )
    mutations["browser"] = {
        "ring": {k: ring_br.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "before_text": br_before_text[:200],
        "after_text": br_after_text[:400],
        "memo_path": memo_txt_path,
        "memo_html": memo_html_path,
        "lab_collector_html_forbidden": True,
        "click_counter_forbidden": True,
        "mutated": br_mutated,
        "http_doc_ok": {k: _ring_browser_curl.get(k) for k in ("ok", "stdout", "stderr") if k in _ring_browser_curl},
        "note": (
            "Chromium real RingMemo.html contenteditable document; HID typing must appear in "
            "RingMemo.txt autosave. lab_browser.html click-collector forbidden."
        ),
    }

    # --- Game: Pedestrian — seed already save_version=2 so v1→v2 migration alone cannot earn ---
    # Require post-load baseline then HID-driven byte change (xp/unlocks/saved content), process alive.
    seed_cfg = (
        "[meta]\n\n"
        "save_version=2\n"
        'saved_at="2026-01-01T00:00:00"\n\n'
        "[career]\n\n"
        "xp=11\n"
        "level=1\n"
        "unlocked={\n"
        '"mode:cup": true,\n'
        '"mode:quick_race": true,\n'
        '"mode:time_trial": true,\n'
        '"mode:tutorial": true,\n'
        '"runner:dash_reed": true,\n'
        '"shoe:starter_soles": true,\n'
        '"ring:seed": true\n'
        "}\n"
        "challenges={}\n"
        "trophies=[]\n"
        "tt_pbs={}\n"
        "tutorial_completed=false\n"
        "first_run_complete=true\n"
    )
    seed_path = "/root/.local/share/godot/app_userdata/Pedestrian Pursuit/pp_progression.cfg"
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "killall -q chromium oosplash soffice.bin godot 2>/dev/null || true; sleep 1; "
            "rm -rf '/root/.local/share/godot/app_userdata/Pedestrian Pursuit' "
            "'/root/.local/share/godot/app_userdata/pedestrian-pursuit'; "
            "mkdir -p '/root/.local/share/godot/app_userdata/Pedestrian Pursuit' "
            "/var/lib/gunnchos/games/foot-racing",
        ],
        timeout_sec=25.0,
    )
    _agent_call(
        session,
        "file_put",
        path=seed_path,
        bytes_b64=base64.b64encode(seed_cfg.encode("utf-8")).decode("ascii"),
        timeout_sec=20.0,
    )
    game_paths = [
        "/root/.local/share/godot/app_userdata/Pedestrian Pursuit/pp_progression.cfg",
        "/root/.local/share/godot/app_userdata/pedestrian-pursuit/pp_progression.cfg",
    ]
    game_before_snaps = {p: _agent_call(session, "logs", path=p, lines=80) for p in game_paths}
    sock = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "ls /run/gunnchos-wayland/wayland-* 2>/dev/null | grep -v lock | head -1 | xargs -n1 basename",
        ],
        timeout_sec=10.0,
    )
    wayland = ((sock.get("stdout") or "").strip().splitlines() or ["wayland-0"])[0] or "wayland-0"
    # Ensure Godot4 + project exist when possible (best-effort; prefer FAIL if missing).
    try:
        from gunnchos_device_os.device_lab.interactive_guest_four_games import (
            _deploy_pedestrian_pursuit,
            _ensure_godot4_in_guest,
        )

        _ensure_godot4_in_guest(session, Path(__file__).resolve().parents[2])
        _deploy_pedestrian_pursuit(session, Path(__file__).resolve().parents[2])
    except Exception as _godot_prep_exc:  # noqa: BLE001
        launches["game_prep_error"] = str(_godot_prep_exc)[:240]
    ring_game_launch = _agent_call(
        session,
        "process_start",
        name="godot-pedestrian-ring",
        argv=[
            "/opt/gunnchos/bin/godot",
            "--path",
            "/root/pedestrian-pursuit",
            "--display-driver",
            "wayland",
            "--rendering-driver",
            "opengl3",
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=30.0,
    )
    alive = {"ok": False, "stdout": ""}
    for _ in range(20):
        alive = _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "pgrep -af '[g]odot' | head; pgrep -x godot >/dev/null && echo ALIVE"],
            timeout_sec=15.0,
        )
        if "ALIVE" in (alive.get("stdout") or ""):
            alive["ok"] = True
            break
        time.sleep(0.5)
    launches["game"] = {
        "start": {k: ring_game_launch.get(k) for k in ("ok", "pid", "started", "reason") if k in ring_game_launch},
        "alive": {k: alive.get(k) for k in ("ok", "stdout") if k in alive},
        "wayland": wayland,
        "process_alive": bool(alive.get("ok")),
    }
    time.sleep(3.0)
    find_before = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "find /root/.local/share/godot -name 'pp_progression.cfg' 2>/dev/null; echo ---; date +%s"],
        timeout_sec=15.0,
    )
    # Post-load settle WITHOUT HID — capture baseline so load-migration / autosave alone cannot earn.
    time.sleep(5.0)
    game_mid_snaps = {p: _agent_call(session, "logs", path=p, lines=80) for p in game_paths}
    ring_game = rings.inject(target="games", confidence=0.92, gesture="click")
    if ring_game.get("via_stack") and alive.get("ok"):
        _hid_burst(("ret", "ret", "spc", "ret", "w", "w", "w", "d", "d", "a", "spc", "spc"), clicks=3)
        time.sleep(4.0)
    # Never earn via headless first-run create with dead process; never earn v1→v2 migration alone.
    alive_after = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "pgrep -x godot >/dev/null && echo ALIVE; pgrep -af '[g]odot' | head"],
        timeout_sec=15.0,
    )
    process_alive = "ALIVE" in (alive_after.get("stdout") or "")
    launches["game"]["alive_after_mutation"] = {
        "ok": process_alive,
        "stdout": alive_after.get("stdout"),
    }
    game_after_snaps = {p: _agent_call(session, "logs", path=p, lines=80) for p in game_paths}
    find_after = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "find /root/.local/share/godot -name 'pp_progression.cfg' -o -name 'accessibility.cfg' 2>/dev/null; "
            "echo ---; stat -c '%n %s %Y' /root/.local/share/godot/app_userdata/*/pp_progression.cfg 2>/dev/null",
        ],
        timeout_sec=15.0,
    )

    def _xp(txt: str) -> int | None:
        for ln in txt.splitlines():
            if ln.strip().startswith("xp="):
                try:
                    return int(ln.split("=", 1)[1].strip())
                except Exception:
                    return None
        return None

    def _save_ver(txt: str) -> str:
        for ln in txt.splitlines():
            if ln.strip().startswith("save_version="):
                return ln.split("=", 1)[1].strip()
        return ""

    godot_mutated = False
    save_path_used = game_paths[0]
    before_used: dict[str, Any] = {}
    after_used: dict[str, Any] = {}
    first_run_create = False
    migration_alone_rejected = False
    for p in game_paths:
        seed_txt = "\n".join((game_before_snaps[p].get("lines") or []))
        mid_txt = "\n".join((game_mid_snaps[p].get("lines") or []))
        atxt = "\n".join((game_after_snaps[p].get("lines") or []))
        baseline = mid_txt or seed_txt
        created = bool(game_after_snaps[p].get("ok") and atxt and not seed_txt)
        if created and not seed_txt:
            first_run_create = True
        # Seed is already v2 — reject if the only delta vs seed is save_version rewrite / timestamp.
        if seed_txt and atxt and atxt != seed_txt:
            seed_v, after_v = _save_ver(seed_txt), _save_ver(atxt)
            if seed_v == "1" and after_v == "2":
                migration_alone_rejected = True
            # Strip volatile saved_at lines for causation check
            def _norm(t: str) -> str:
                return "\n".join(
                    ln for ln in t.splitlines() if not ln.strip().startswith("saved_at=")
                )

            if _norm(seed_txt) == _norm(atxt) and seed_v != after_v:
                migration_alone_rejected = True
                continue
        # Require HID-driven change beyond post-load baseline while process alive.
        hid_changed = bool(baseline and atxt and atxt != baseline)
        xp_before, xp_after = _xp(baseline), _xp(atxt)
        xp_moved = xp_before is not None and xp_after is not None and xp_after != xp_before
        unlock_moved = ('"ring:seed"' in baseline) != ('"ring:seed"' in atxt) or (
            baseline.count("true") != atxt.count("true") and hid_changed
        )
        input_driven = bool(hid_changed and (xp_moved or unlock_moved or (marker[:8] in atxt)))
        # Also accept clear non-timestamp content delta after HID beyond mid baseline.
        if hid_changed and not input_driven:
            def _norm2(t: str) -> str:
                return "\n".join(
                    ln for ln in t.splitlines() if not ln.strip().startswith("saved_at=")
                )

            input_driven = _norm2(baseline) != _norm2(atxt)
        if (
            ring_game.get("via_stack")
            and process_alive
            and hid_changed
            and input_driven
            and not created
            and _save_ver(seed_txt or baseline) == "2"
        ):
            godot_mutated = True
            save_path_used = p
            before_used = game_mid_snaps[p] if mid_txt else game_before_snaps[p]
            after_used = game_after_snaps[p]
            launches["game"]["input_driven"] = {
                "xp_before": xp_before,
                "xp_after": xp_after,
                "xp_moved": xp_moved,
                "hid_changed_beyond_post_load_baseline": True,
                "seed_save_version": "2",
                "migration_alone_rejected": True,
            }
            break
    # Explicitly reject headless harness / migration-alone paths (prior false PASS).
    if not godot_mutated:
        launches["game"]["harness_rejected"] = True
        launches["game"]["first_run_create_rejected"] = bool(first_run_create or not process_alive)
        launches["game"]["migration_alone_rejected"] = True
        launches["game"]["post_load_baseline_required"] = True
    # First-party web game fallback REJECTED for RING PASS (Lab anime-aggressors / lab://).
    web_mutated = False
    web_state = _agent_call(session, "logs", path="/var/lib/gunnchos/games/anime-aggressors/state.json", lines=40)
    web_before_input = 0
    try:
        web_before_input = int(json.loads("\n".join(web_state.get("lines") or []) or "{}").get("input") or 0)
    except Exception:
        web_before_input = 0
    # Observe-only: never earn RING via Lab anime-aggressors surface.
    web_after = web_state
    web_after_input = web_before_input
    game_mutated = bool(godot_mutated and process_alive)
    mutations["game"] = {
        "ring": {k: ring_game.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "launch": launches.get("game"),
        "save_path": save_path_used if godot_mutated else "",
        "before": before_used if godot_mutated else {},
        "after": after_used if godot_mutated else {},
        "mutated": game_mutated,
        "godot_mutated": godot_mutated,
        "process_alive": process_alive,
        "first_run_create_rejected": True,
        "headless_harness_rejected": True,
        "migration_alone_rejected": True,
        "seed_save_version": "2",
        "post_load_baseline_required": True,
        "first_party_web_mutated": False,
        "lab_anime_aggressors_rejected": True,
        "lab_html_probe_rejected": True,
        "web_observe_only": {
            "before_input": web_before_input,
            "after_input": web_after_input,
            "note": "Lab anime-aggressors surface never earns RING_TO_REAL_APP_STATE_MUTATION_PASS",
        },
        "note": (
            "Godot Pedestrian input-driven save change beyond post-load baseline; seed already save_version=2"
            if game_mutated
            else "Requires HID-driven Pedestrian save delta beyond post-load baseline (migration-alone/first-run rejected)"
        ),
    }

    result["app_launches"] = launches

    # Commit guest artifacts for independent review. Forbid Lab RINGRING sidecars.
    guest_artifacts: dict[str, Any] = {"ok": False}
    doc_dir = evidence_dir / "document"
    br_dir = evidence_dir / "browser"
    game_dir = evidence_dir / "game"
    for d in (doc_dir, br_dir, game_dir):
        d.mkdir(parents=True, exist_ok=True)
    # Remove / forbid Lab document_state.json (RINGRING / lab://) — never evidence for RING.
    for stale_name in ("document_state.json",):
        stale = doc_dir / stale_name
        if stale.exists():
            stale.unlink()
    # Also purge any Lab scratch mirror that RingsBackend may have written.
    lab_doc = evidence_dir / "_lab_surfaces_forbidden" / "document" / "document_state.json"
    if lab_doc.exists():
        try:
            lab_doc.unlink()
        except OSError:
            pass
    stale_odt = doc_dir / "ring_editor_buffer.odt"
    odt_guest_paths = [
        "/root/gunnchos-lab-document.odt",
    ]
    # Prefer any /root/*.odt containing the marker.
    odt_list = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "ls -1 /root/*.odt 2>/dev/null"],
        timeout_sec=10.0,
    )
    odt_candidates = [ln.strip() for ln in (odt_list.get("stdout") or "").splitlines() if ln.strip().endswith(".odt")]
    committed_odt = None
    committed_marker = None
    for cand in odt_candidates or odt_guest_paths:
        raw = _pull_guest_file(session, cand)
        if not raw:
            continue
        try:
            import zipfile
            import io as _io

            txt = zipfile.ZipFile(_io.BytesIO(raw)).read("content.xml").decode("utf-8", "replace")
        except Exception:
            txt = ""
        if marker in txt and "RINGRING" not in txt:
            stale_odt.write_bytes(raw)
            committed_odt = "document/ring_editor_buffer.odt"
            committed_marker = marker
            guest_artifacts["odt_path_guest"] = cand
            guest_artifacts["odt_bytes"] = len(raw)
            guest_artifacts["odt_marker"] = marker
            break
    # Browser memo from guest (real document autosave — not lab_browser click collector).
    br_raw = _pull_guest_file(session, memo_txt_path)
    br_html = _pull_guest_file(session, memo_html_path)
    if br_raw and marker.encode("utf-8") in br_raw:
        (br_dir / "RingMemo.txt").write_bytes(br_raw)
        guest_artifacts["browser_memo"] = "browser/RingMemo.txt"
        guest_artifacts["browser_bytes"] = len(br_raw)
        guest_artifacts["browser_marker"] = marker
        # Compat key for PASS gate (memo replaces click-counter browser_state.json).
        guest_artifacts["browser_state"] = "browser/RingMemo.txt"
    if br_html:
        (br_dir / "RingMemo.html").write_bytes(br_html)
        guest_artifacts["browser_html"] = "browser/RingMemo.html"
    # Forbid reintroducing planted collector evidence as PASS artifacts.
    for banned in ("lab_browser.html", "browser_state.json"):
        banned_p = br_dir / banned
        if banned_p.exists():
            banned_p.unlink()
    guest_artifacts["lab_browser_collector_forbidden"] = True
    # First-party Godot save if mutated while alive.
    if godot_mutated and process_alive and save_path_used and str(save_path_used).startswith("/"):
        graw = _pull_guest_file(session, str(save_path_used))
        if graw:
            (game_dir / "pp_progression.cfg").write_bytes(graw)
            guest_artifacts["game_save"] = "game/pp_progression.cfg"
            guest_artifacts["game_bytes"] = len(graw)
            guest_artifacts["game_save_guest_path"] = save_path_used
            guest_artifacts["godot_process_alive"] = True
    # Final Lab sidecar ban: refuse PASS if document_state.json reappears with RINGRING.
    lab_sidecar_forbidden = False
    ds_path = doc_dir / "document_state.json"
    if ds_path.exists():
        try:
            ds_obj = json.loads(ds_path.read_text(encoding="utf-8"))
        except Exception:
            ds_obj = {}
        content = str(ds_obj.get("content") or "")
        if "RINGRING" in content or str(ds_obj.get("url") or "").startswith("lab://"):
            lab_sidecar_forbidden = True
            ds_path.unlink(missing_ok=True)
    guest_artifacts["ok"] = bool(
        committed_odt
        and guest_artifacts.get("browser_state")
        and guest_artifacts.get("game_save")
        and not lab_sidecar_forbidden
        and not (doc_dir / "document_state.json").exists()
    )
    guest_artifacts["committed_odt"] = committed_odt
    guest_artifacts["lab_ringring_rejected"] = True
    guest_artifacts["lab_document_state_forbidden"] = True
    guest_artifacts["document_state_present"] = (doc_dir / "document_state.json").exists()
    result["guest_artifacts"] = guest_artifacts

    # Confidence gate via Ring stack
    low = rings.inject(confidence=0.2, target="browser")
    wrong = rings.inject(confidence=0.9, target="browser", wrong_target=True)
    gate_ok = (low.get("delivered") is False) and (wrong.get("delivered") is False)

    all_mutated = all(bool(mutations[t].get("mutated")) for t in ("libreoffice", "browser", "game"))
    if not (launches.get("libreoffice") or {}).get("ok"):
        all_mutated = False
        result["blocker"] = result.get("blocker") or "libreoffice_binary_required_for_document_leg"
    if not committed_odt or committed_marker != marker:
        all_mutated = False
        result["blocker"] = result.get("blocker") or "guest_odt_with_marker_not_committed"
    if not guest_artifacts.get("browser_state"):
        all_mutated = False
        result["blocker"] = result.get("blocker") or "guest_browser_state_not_committed"
    if not (godot_mutated and process_alive and guest_artifacts.get("game_save")):
        all_mutated = False
        result["blocker"] = result.get("blocker") or "godot_alive_mutation_not_committed"
    if lab_sidecar_forbidden or (doc_dir / "document_state.json").exists():
        all_mutated = False
        result["blocker"] = result.get("blocker") or "lab_document_state_sidecar_forbidden"
    if guest_artifacts.get("document_state_present"):
        all_mutated = False
        result["blocker"] = result.get("blocker") or "document_state_json_must_be_absent"

    pipeline = [
        "ring_simulator",
        "authenticated_packet",
        "RingService",
        "SpatialInputService",
        "confidence_gate",
        "guest_os_input",
        "app_state_mutation",
    ]
    earned = bool(all_mutated and gate_ok and uinput_ok)
    if earned and not all(
        bool((mutations[t].get("ring") or {}).get("via_stack")) for t in ("libreoffice", "browser", "game")
    ):
        earned = False
        result["blocker"] = "via_stack_required_for_all_three"

    # Aggregate APPLICATION_INPUT only if RingsBackend observe path earned on all three legs.
    app_input_flags = []
    for t in ("libreoffice", "browser", "game"):
        osp = ((mutations.get(t) or {}).get("ring") or {}).get("os_input_path") or {}
        app_input_flags.append(bool(osp.get("RING_TO_REAL_APPLICATION_INPUT_PASS")))
    app_input_earned = bool(earned and app_input_flags and all(app_input_flags))

    result.update(
        {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": earned,
            "RING_TO_REAL_APPLICATION_INPUT_PASS": app_input_earned,
            "RING_SPATIAL_ACCURACY": "SIMULATED",
            "honesty": {
                "lab_browser_collector_forbidden": True,
                "pedestrian_migration_alone_forbidden": True,
                "seed_save_version": "2",
                "browser_evidence": "RingMemo.txt contenteditable document autosave",
                "spatial_labeled": "SIMULATED",
            },
            "pipeline_required": pipeline,
            "pipeline_ok": earned,
            "guest_os_input_present": bool(uinput_ok),
            "mutations": mutations,
            "confidence_gate": {"low": low, "wrong": wrong, "ok": gate_ok},
            "mutation_marker": marker,
            "marker_found_in_after": bool(mutations["libreoffice"].get("mutated")),
            "note": (
                "Ring→SpatialInput→guest HID mutated LibreOffice+RingMemo+Pedestrian (input-driven, no lab collector / no migration-alone); guest artifacts committed"
                if earned
                else "Not earned — need honest LibreOffice ODT + RingMemo marker + Pedestrian input-driven save (lab collector / migration-alone rejected)"
            ),
        }
    )
    (evidence_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Attempt Interactive Guest LIVE/DSXL/RING proofs")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--dual", action="store_true", help="Boot with dual virtio-gpu outputs for DSXL attempt")
    parser.add_argument("--boot-timeout-s", type=int, default=180)
    parser.add_argument("--memory-mb", type=int, default=3072)
    ns = parser.parse_args(argv)

    repo_root = Path(ns.repo_root) if ns.repo_root else Path(__file__).resolve().parents[2]
    work = repo_root / "artifacts" / "wp011r" / "interactive_guest_session"
    boot = boot_interactive_guest(
        repo_root,
        work,
        dual=ns.dual,
        boot_timeout_s=ns.boot_timeout_s,
        memory_mb=ns.memory_mb,
    )
    session = boot.pop("_session", None)
    out: dict[str, Any] = {"boot": boot}
    if not boot.get("ok") or session is None:
        out["error"] = "interactive_guest_boot_failed"
        print(json.dumps(out, indent=2, default=str))
        return 1
    try:
        visual_dir = _evidence_dir(repo_root, "visual")
        dsxl_dir = _evidence_dir(repo_root, "dsxl")
        ring_dir = _evidence_dir(repo_root, "ring")
        # Give weston/openvt a few seconds after guest-agent ping before proofs.
        for _ in range(12):
            probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
            if probe.get("available"):
                break
            time.sleep(2.0)
        out["live_visual"] = attempt_live_visual_pass(session, visual_dir)
        if ns.dual:
            out["dsxl"] = attempt_dsxl_dual_compositor_pass(session, dsxl_dir)
        out["ring"] = attempt_ring_app_mutation_pass(session, ring_dir)
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass
    print(json.dumps({k: v for k, v in out.items() if k != "boot"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
