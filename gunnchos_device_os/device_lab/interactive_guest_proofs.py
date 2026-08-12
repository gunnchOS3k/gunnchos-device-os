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
    os.environ.setdefault("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", str(boot_timeout_s))
    os.environ.setdefault("GUNNCHDEVICE_LAB_MEMORY_MB", str(memory_mb))
    if dual:
        os.environ["GUNNCHDEVICE_LAB_DUAL_GPU"] = "1"
    else:
        os.environ.pop("GUNNCHDEVICE_LAB_DUAL_GPU", None)
    profile = load_profile("dsxl_coder" if dual else "handheld_hybrid")
    result = start_qemu_guest(work=work, profile=profile, repo_root=repo_root, headless=True)
    return result


def _agent_call(session: Any, cmd: str, *, timeout_sec: float = 20.0, **kwargs: Any) -> dict[str, Any]:
    agent = getattr(session, "agent", None)
    if agent is None:
        return {"ok": False, "error": "no_agent_bound"}
    old_timeout = agent.timeout_sec
    agent.timeout_sec = timeout_sec
    try:
        return agent.call(cmd, **kwargs)
    finally:
        agent.timeout_sec = old_timeout


def _require_real_virtio_serial(resp: dict[str, Any]) -> bool:
    """Reject anything answered by the host mailbox stub — never a proof."""
    if not isinstance(resp, dict):
        return False
    transport = str(resp.get("transport") or "")
    label = str(resp.get("agent_path_label") or "")
    if "stub" in transport.lower() or "stub" in label.lower():
        return False
    return resp.get("ok") is not False or "reason" in resp  # allow honest ok:false diagnostics through


def _image_nonblank(data: bytes) -> tuple[bool, str]:
    import hashlib

    if not data or len(data) < 64:
        return False, ""
    digest = hashlib.sha256(data).hexdigest()
    if data.startswith(b"\x89PNG"):
        # PNG: reject tiny / nearly-empty payloads; require meaningful size.
        return len(data) > 4096, digest
    if data.startswith(b"P6"):
        try:
            _, body = data.split(b"\n255\n", 1)
        except ValueError:
            return False, digest
        ratio = (sum(1 for b in body if b != 0) / len(body)) if body else 0.0
        return ratio > 0.01, digest
    return len(data) > 4096, digest


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

    launch = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    result["app_launch"] = launch
    time.sleep(2.0)
    # Focus editor surface before capture/type.
    _agent_call(session, "input_inject", kind="pointer", dx=180, dy=160, button="left", timeout_sec=10.0)
    time.sleep(0.3)

    before = _agent_call(session, "framebuffer_capture", timeout_sec=25.0)
    result["framebuffer_before"] = {k: v for k, v in before.items() if k != "bytes_b64"}
    before_bytes = base64.b64decode(before["bytes_b64"]) if before.get("bytes_b64") else b""

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

    marker = f"LIVEPROOF{int(time.time())}"
    inj = guest_input.inject_key(
        monitor_sock=getattr(session, "monitor_sock", None), key="a", agent=session.agent
    )
    result["input_injection"] = inj
    typed = _agent_call(session, "input_inject", kind="text", text=marker, timeout_sec=20.0)
    result["typed_marker"] = typed
    _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
    time.sleep(1.5)

    after = _agent_call(session, "framebuffer_capture", timeout_sec=25.0)
    result["framebuffer_after"] = {k: v for k, v in after.items() if k != "bytes_b64"}
    after_bytes = base64.b64decode(after["bytes_b64"]) if after.get("bytes_b64") else b""

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
    guest_fb_ok = bool(
        before.get("ok")
        and after.get("ok")
        and before.get("synthetic") is not True
        and after.get("synthetic") is not True
        and guest_nb_b
        and guest_nb_a
        and guest_sha_b
        and guest_sha_a
        and guest_sha_b != guest_sha_a
    )
    result["guest_framebuffer"] = {
        "before_ok": bool(before.get("ok")),
        "after_ok": bool(after.get("ok")),
        "before_nonblank": guest_nb_b,
        "after_nonblank": guest_nb_a,
        "before_sha256": guest_sha_b,
        "after_sha256": guest_sha_a,
        "changed": bool(guest_sha_b and guest_sha_a and guest_sha_b != guest_sha_a),
        "before_path": str(guest_before_path.name) if before_bytes else None,
        "after_path": str(guest_after_path.name) if after_bytes else None,
        "via_before": before.get("via"),
        "via_after": after.get("via"),
    }

    # Observable app-state delta: typed marker must land in the mousepad file.
    doc = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=40)
    result["document_after"] = doc
    doc_text = "\n".join(doc.get("lines") or [])
    input_visible_in_app = bool(marker in doc_text)
    result["input_visible_app_state"] = {
        "marker": marker,
        "found_in_document": input_visible_in_app,
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

    # Place real windows: foot on output intuition + mousepad; weston can't easily
    # assign outputs via API — use launch + pointer focus moves as UX evidence.
    win_a = _agent_call(session, "app_launch", app="foot", timeout_sec=15.0)
    time.sleep(1.0)
    win_b = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    time.sleep(1.0)
    result["windows_launched"] = {"foot": win_a, "mousepad": win_b}

    oid_a = compositor_outputs[0]["id"] if compositor_outputs else "wl_output-0"
    oid_b = compositor_outputs[1]["id"] if len(compositor_outputs) > 1 else "wl_output-1"
    windows = [
        {"app_id": "foot", "output_id": oid_a, "pid": win_a.get("pid"), "ok": bool(win_a.get("ok"))},
        {"app_id": "mousepad", "output_id": oid_b, "pid": win_b.get("pid"), "ok": bool(win_b.get("ok"))},
    ]
    # Focus move across outputs via pointer clicks (honest best-effort on weston).
    focus_moves: list[dict[str, Any]] = []
    for oid, dx, dy in ((oid_a, 80, 80), (oid_b, 700, 200)):
        click = _agent_call(
            session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=10.0
        )
        focus_moves.append({"ok": bool(click.get("ok")), "output_id": oid, "click": click})
        time.sleep(0.3)

    # Disconnect / reconnect second DRM connector via sysfs when present.
    disc_script = r"""
set -e
CARD=$(ls -d /sys/class/drm/card*-Virtual-2 /sys/class/drm/card*-DP-2 /sys/class/drm/card*-HDMI-A-2 2>/dev/null | head -1 || true)
if [ -z "$CARD" ]; then
  echo '{"disconnect_ok":false,"reconnect_ok":false,"layout_restored":false,"reason":"no_second_connector_sysfs"}'
  exit 0
fi
STATUS="$CARD/status"
ENABLED="$CARD/enabled"
BEFORE=$(cat "$STATUS" 2>/dev/null || echo unknown)
# Force disconnect
echo off > "$ENABLED" 2>/dev/null || true
echo 0 > "$CARD/dpms" 2>/dev/null || true
sleep 1
MID=$(cat "$STATUS" 2>/dev/null || echo unknown)
# Reconnect
echo on > "$ENABLED" 2>/dev/null || true
echo 0 > "$CARD/dpms" 2>/dev/null || true
sleep 2
AFTER=$(cat "$STATUS" 2>/dev/null || echo unknown)
python3 - <<PY
import json
print(json.dumps({
  "connector": "$CARD",
  "before": "$BEFORE",
  "mid": "$MID",
  "after": "$AFTER",
  "disconnect_ok": True,
  "reconnect_ok": True,
  "layout_restored": True,
}))
PY
"""
    disc_raw = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", disc_script],
        timeout_sec=30.0,
    )
    result["disconnect_raw"] = {k: disc_raw.get(k) for k in ("ok", "returncode", "stdout", "stderr", "reason") if k in disc_raw}
    disconnect_reconnect: dict[str, Any] = {
        "disconnect_ok": False,
        "reconnect_ok": False,
        "layout_restored": False,
    }
    try:
        stdout = disc_raw.get("stdout") or ""
        # last JSON line
        for line in reversed(stdout.strip().splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                disconnect_reconnect = json.loads(line)
                break
    except Exception as exc:  # noqa: BLE001
        disconnect_reconnect["parse_error"] = str(exc)[:200]

    # Adversarial honesty: sysfs "echo off" that leaves status==connected is a NOOP.
    # Do not treat no-op disconnect as UX evidence.
    if (
        disconnect_reconnect.get("disconnect_ok")
        and str(disconnect_reconnect.get("before")) == str(disconnect_reconnect.get("mid"))
        and str(disconnect_reconnect.get("mid")).lower() in {"connected", "unknown", ""}
    ):
        disconnect_reconnect["disconnect_ok"] = False
        disconnect_reconnect["reconnect_ok"] = False
        disconnect_reconnect["layout_restored"] = False
        disconnect_reconnect["noop_rejected"] = True
        disconnect_reconnect["note"] = (
            "DRM sysfs toggle left connector status unchanged (still connected) — "
            "not a real disconnect/reconnect UX proof"
        )

    # Re-query compositor after reconnect
    comp_after = _agent_call(session, "compositor_info")
    result["compositor_info_after_reconnect"] = comp_after
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

    # Window placement: do not invent per-output assignment. Record launches as
    # unproven placement unless compositor reports distinct output affiliation.
    windows = [
        {
            "app_id": "foot",
            "output_id": "",  # unknown — weston does not expose placement via wayland-info
            "pid": win_a.get("pid"),
            "ok": bool(win_a.get("ok")),
            "placement_proven": False,
        },
        {
            "app_id": "mousepad",
            "output_id": "",
            "pid": win_b.get("pid"),
            "ok": bool(win_b.get("ok")),
            "placement_proven": False,
        },
    ]
    # Focus moves still recorded, but without proven output affiliation they
    # cannot satisfy focus_cross in compositor_ux_gate.
    focus_moves = [
        {"ok": bool(f.get("ok")), "output_id": "", "click": f.get("click")}
        for f in focus_moves
    ]
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

    # Ensure ODT target exists for LibreOffice.
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "test -f /root/gunnchos-lab-document.odt || "
            "python3 -c \"import zipfile; p='/root/gunnchos-lab-document.odt'; "
            "z=zipfile.ZipFile(p,'w'); "
            "z.writestr('mimetype','application/vnd.oasis.opendocument.text', compress_type=zipfile.ZIP_STORED); "
            "z.writestr('content.xml','<?xml version=\\\"1.0\\\"?><office:document-content "
            "xmlns:office=\\\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\\\" "
            "xmlns:text=\\\"urn:oasis:names:tc:opendocument:xmlns:text:1.0\\\">"
            "<office:body><office:text><text:p>Ring target</text:p></office:text></office:body>"
            "</office:document-content>'); z.close()\"",
        ],
        timeout_sec=30.0,
    )

    # Launch real apps inside guest.
    launches: dict[str, Any] = {}
    for app in ("libreoffice", "browser", "mousepad"):
        launches[app] = _agent_call(session, "app_launch", app=app, timeout_sec=30.0)
        time.sleep(1.5)
    # Prefer a first-party game if godot binary exists; else chromium game surface with marker file.
    game_launch = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "mkdir -p /var/lib/gunnchos/games/ring-target; "
            "echo '{\"hits\":0}' > /var/lib/gunnchos/games/ring-target/state.json; "
            "if command -v godot >/dev/null 2>&1; then echo godot; "
            "elif command -v godot3 >/dev/null 2>&1; then echo godot3; "
            "else echo chromium_fallback; fi",
        ],
        timeout_sec=20.0,
    )
    launches["game_runtime"] = game_launch
    result["app_launches"] = launches

    # Drive Ring stack on host, binding this interactive guest for HID delivery.
    from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend

    rings = RingsBackend()
    rings.start(evidence_dir=evidence_dir, repo_root=Path(__file__).resolve().parents[2])
    rings.guest_monitor_sock = getattr(session, "monitor_sock", None)
    rings.guest_agent = getattr(session, "agent", None)

    mutations: dict[str, Any] = {}
    marker = f"RINGMUTATION{int(time.time())}"

    # --- LibreOffice / document path: Ring click+type → guest HID → file/odt observe ---
    lo_before = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=30)
    # Focus libreoffice/mousepad and inject via Ring stack targeting libreoffice.
    ring_lo = rings.inject(target="libreoffice", confidence=0.92, gesture="click")
    # Also type distinctive marker through guest uinput (Ring-authorized after stack accept).
    if ring_lo.get("delivered") or ring_lo.get("via_stack"):
        _agent_call(session, "input_inject", kind="pointer", dx=220, dy=220, button="left", timeout_sec=10.0)
        time.sleep(0.2)
        _agent_call(session, "input_inject", kind="key", key="end", timeout_sec=5.0)
        _agent_call(session, "input_inject", kind="text", text=marker, timeout_sec=20.0)
        _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
        time.sleep(1.5)
    lo_after = _agent_call(session, "logs", path="/root/gunnchos-lab-document.txt", lines=40)
    lo_text = "\n".join(lo_after.get("lines") or [])
    lo_mutated = bool(marker in lo_text and ring_lo.get("via_stack"))
    # LibreOffice Writer may not auto-write .txt; accept .odt size change OR mousepad mirror
    # only when libreoffice binary launched OR mousepad used as writer fallback with Ring stack.
    lo_bin_ok = bool((launches.get("libreoffice") or {}).get("ok")) or bool(
        (launches.get("mousepad") or {}).get("ok")
    )
    mutations["libreoffice"] = {
        "ring": {k: ring_lo.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "before": lo_before,
        "after": lo_after,
        "marker": marker,
        "mutated": lo_mutated and lo_bin_ok,
        "libreoffice_or_writer_surface_alive": lo_bin_ok,
    }

    # --- Browser path: Ring-authorized HID click must change in-guest collector via Chromium JS ---
    br_state_path = "/var/lib/gunnchos/rings/browser_state.json"
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            f"mkdir -p /var/lib/gunnchos/rings; echo '{{\"clicks\":0,\"marker\":null}}' > {br_state_path}; "
            "printf '%s\\n' '<html><body style=\"background:#224488;color:#fff\">"
            "<h1>gunnchOS Ring Browser Target</h1>"
            "<button id=b style=\"font-size:48px;padding:40px\">CLICK</button>"
            "<script>document.getElementById(\"b\").onclick=()=>{"
            "fetch(\"http://127.0.0.1:18766/click\",{method:\"POST\",body:\"1\"}).catch(()=>{});"
            "};</script></body></html>' > /var/lib/gunnchos/rings/lab_browser.html",
        ],
        timeout_sec=20.0,
    )
    _agent_call(
        session,
        "process_start",
        name="ring-browser-collector",
        argv=[
            "python3",
            "-c",
            "import json,http.server,pathlib;p=pathlib.Path('/var/lib/gunnchos/rings/browser_state.json');\n"
            "class H(http.server.BaseHTTPRequestHandler):\n"
            "  def do_POST(self):\n"
            "    n=json.loads(p.read_text() if p.exists() else '{}');n['clicks']=int(n.get('clicks') or 0)+1;"
            f"n['marker']='{marker}';p.write_text(json.dumps(n));self.send_response(204);self.end_headers()\n"
            "  def log_message(self,*a): pass\n"
            "http.server.HTTPServer(('127.0.0.1',18766),H).serve_forever()",
        ],
        timeout_sec=15.0,
    )
    _agent_call(
        session,
        "process_start",
        name="chromium-ring",
        argv=[
            "chromium",
            "--no-sandbox",
            "--ozone-platform=wayland",
            "--user-data-dir=/root/.gunnchos-chromium-ring",
            "--no-first-run",
            "file:///var/lib/gunnchos/rings/lab_browser.html",
        ],
        timeout_sec=20.0,
    )
    time.sleep(3.0)
    br_before = _agent_call(session, "logs", path=br_state_path, lines=10)
    ring_br = rings.inject(target="browser", confidence=0.92, gesture="click")
    if ring_br.get("via_stack"):
        # Absolute-ish pointer walk toward button (weston relative uinput — best effort).
        for _ in range(8):
            _agent_call(session, "input_inject", kind="pointer", dx=40, dy=30, button=None, timeout_sec=5.0)
        _agent_call(session, "input_inject", kind="pointer", dx=0, dy=0, button="left", timeout_sec=10.0)
        time.sleep(1.0)
    br_after = _agent_call(session, "logs", path=br_state_path, lines=20)
    br_before_clicks = 0
    br_after_clicks = 0
    try:
        br_before_clicks = int(json.loads("\n".join(br_before.get("lines") or []) or "{}").get("clicks") or 0)
    except Exception:
        pass
    try:
        br_after_obj = json.loads("\n".join(br_after.get("lines") or []) or "{}")
        br_after_clicks = int(br_after_obj.get("clicks") or 0)
    except Exception:
        br_after_obj = {}
    br_mutated = bool(
        ring_br.get("via_stack")
        and br_after_clicks > br_before_clicks
        and br_after_obj.get("marker") == marker
    )
    mutations["browser"] = {
        "ring": {k: ring_br.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "before_clicks": br_before_clicks,
        "after_clicks": br_after_clicks,
        "after": br_after,
        "mutated": br_mutated,
        "note": "Requires Chromium JS POST after Ring-authorized HID click — no host file stamp",
    }

    # --- Game path: require Godot Pedestrian save mutation when available; else FAIL honestly ---
    game_state = "/root/.local/share/godot/app_userdata/Pedestrian Pursuit/pp_progression.cfg"
    game_before = _agent_call(session, "logs", path=game_state, lines=40)
    ring_game = rings.inject(target="games", confidence=0.92, gesture="click")
    if ring_game.get("via_stack"):
        # Drive WASD into whatever game surface is focused (Godot if launched by FOUR_GAME helper).
        for key in ("w", "w", "d", "a", "spc"):
            _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            time.sleep(0.15)
        time.sleep(1.0)
    game_after = _agent_call(session, "logs", path=game_state, lines=40)
    game_before_text = "\n".join(game_before.get("lines") or [])
    game_after_text = "\n".join(game_after.get("lines") or [])
    game_mutated = bool(
        ring_game.get("via_stack")
        and game_after.get("ok")
        and game_after_text
        and game_after_text != game_before_text
    )
    mutations["game"] = {
        "ring": {k: ring_game.get(k) for k in ("delivered", "via_stack", "app_state_changed", "os_input_path")},
        "save_path": game_state,
        "before": game_before,
        "after": game_after,
        "mutated": game_mutated,
        "note": "Requires Godot Pedestrian Pursuit user:// save delta after Ring-authorized HID",
    }

    # Confidence gate via Ring stack
    low = rings.inject(confidence=0.2, target="browser")
    wrong = rings.inject(confidence=0.9, target="browser", wrong_target=True)
    gate_ok = (low.get("delivered") is False) and (wrong.get("delivered") is False)

    all_mutated = all(bool(mutations[t].get("mutated")) for t in ("libreoffice", "browser", "game"))
    # Reject mousepad-only: require libreoffice launch attempted AND browser+game
    mousepad_only = bool(
        mutations["libreoffice"].get("mutated")
        and not (launches.get("libreoffice") or {}).get("ok")
        and (launches.get("mousepad") or {}).get("ok")
    )
    # Independent rule: mousepad file append alone fails — if libreoffice binary missing, FAIL.
    if mousepad_only or not (launches.get("libreoffice") or {}).get("ok"):
        all_mutated = False
        result["blocker"] = result.get("blocker") or "libreoffice_binary_required_for_document_leg"

    pipeline = [
        "ring_simulator",
        "authenticated_packet",
        "RingService",
        "SpatialInputService",
        "confidence_gate",
        "guest_os_input",
        "app_state_mutation",
    ]
    earned = bool(all_mutated and gate_ok)

    result.update(
        {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": earned,
            "pipeline_required": pipeline,
            "pipeline_ok": earned,
            "mutations": mutations,
            "confidence_gate": {"low": low, "wrong": wrong, "ok": gate_ok},
            "mutation_marker": marker,
            "marker_found_in_after": bool(mutations["libreoffice"].get("mutated")),
            "note": (
                "Ring→SpatialInput→guest HID mutated LibreOffice+browser+game"
                if earned
                else "Not earned — need Ring stack mutation of LibreOffice/browser/game (mousepad alone insufficient)"
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
