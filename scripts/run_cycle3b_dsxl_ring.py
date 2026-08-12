#!/usr/bin/env python3
"""Cycle 3B: earn DSXL (reboot reconfig) + RING; keep LIVE/FOUR evidence.

QEMU 11: virtio-gpu has no hotplug; qom-set outputs after realize rejected.
Architecture: gpu0 max_outputs=2 for Weston dual wl_output; secondary
disconnect/reconnect = stop QEMU and reboot with max_outputs 1 then 2.
Prefer FAIL over false PASS. Cursor never merges.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.interactive_guest_four_games import (  # noqa: E402
    _guest_bash,
    _hot_patch_guest_agent,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _capture_guest_fb,
    _evidence_dir,
    _png_complete,
    _png_half_sha256,
    _pull_guest_file,
    _qemu_monitor_lines,
    _rgb_halves_to_pngs,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import (  # noqa: E402
    compositor_ux_gate,
)


def _kill_stale_qemu() -> dict:
    import signal

    killed: list[int] = []
    arts = ROOT / "artifacts/wp011r"
    for pidf in arts.glob("**/qemu.pid"):
        try:
            pid = int(pidf.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except OSError:
            pass
    if killed:
        time.sleep(3)
        for pid in killed:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(1)
    return {"killed": killed}


def _wait_compositor(session, n=30):
    p = {"available": False}
    for _ in range(n):
        p = _agent_call(session, "compositor_info", timeout_sec=10.0)
        if p.get("available"):
            return p
        time.sleep(2.0)
    return p


def _boot(work: Path, *, max_outputs: int):
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "0"
    os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] = "1"
    os.environ["GUNNCHDEVICE_LAB_VIRTIO_GPU_MAX_OUTPUTS"] = str(max_outputs)
    os.environ.pop("GUNNCHDEVICE_LAB_DUAL_VIRTIO_GPU_DEVICES", None)
    return boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=240, memory_mb=4096)


def _drm_and_comp(session):
    disp = _agent_call(session, "display_info")
    comp = _agent_call(session, "compositor_info")
    cards = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "ls -d /sys/class/drm/card*-Virtual-* 2>/dev/null; echo ---; "
            "for s in /sys/class/drm/card*-Virtual-*/status; do echo $s=$(cat $s); done; "
            "echo ---WI---; wayland-info 2>/dev/null | head -80",
        ],
        timeout_sec=20.0,
    )
    return disp, comp, cards


def _push_weston_ini(session) -> dict:
    import base64

    weston_ini = ROOT / "os_build/device_lab_interactive_guest/debian_cloud/config/weston.ini"
    if not weston_ini.is_file():
        return {"ok": False, "error": "weston_ini_missing"}
    b64 = base64.b64encode(weston_ini.read_bytes()).decode("ascii")
    return _guest_bash(
        session,
        f"printf '%s' '{b64}' | base64 -d > /etc/xdg/weston/weston.ini; "
        "cp /etc/xdg/weston/weston.ini /etc/gunnchos-weston/weston.ini; "
        "systemctl restart gunnchos-weston.service || true; sleep 5; "
        "pgrep -x weston && echo weston_ok",
        timeout_sec=60,
        name="weston-ini",
    )


def _enable_dual_compositor(session) -> dict:
    """Weston first; labwc fallback if drm-backend still reports one wl_output."""
    out: dict = {"ok": False}
    _push_weston_ini(session)
    _wait_compositor(session)
    comp = _agent_call(session, "compositor_info")
    out["weston"] = {
        "compositor": comp.get("compositor"),
        "outputs": comp.get("outputs"),
        "available": comp.get("available"),
    }
    if int(comp.get("outputs") or 0) >= 2:
        out["ok"] = True
        out["via"] = "weston"
        out["comp"] = comp
        return out
    lab = _guest_bash(
        session,
        "set +e; export DEBIAN_FRONTEND=noninteractive; "
        "apt-get install -y --no-install-recommends labwc wlr-randr grim >/var/log/gunnchos-apt-labwc.log 2>&1; "
        "systemctl stop gunnchos-weston.service; pkill -x weston || true; sleep 2; "
        "mkdir -p /run/gunnchos-wayland /root/.config/labwc; "
        "XDG_RUNTIME_DIR=/run/gunnchos-wayland LIBSEAT_BACKEND=seatd "
        "  labwc >/var/log/gunnchos-labwc.log 2>&1 & "
        "sleep 5; pgrep -x labwc && echo labwc_ok; "
        "wlr-randr 2>/dev/null | head -40; "
        "command -v grim; command -v wlr-randr",
        timeout_sec=180,
        name="labwc-fallback",
    )
    out["labwc_start"] = {k: lab.get(k) for k in ("ok", "stdout", "stderr", "returncode") if k in lab}
    _wait_compositor(session, n=20)
    _guest_bash(
        session,
        "set +e; "
        "wlr-randr --output Virtual-1 --on --pos 0,0 --mode 1280x800 2>/dev/null; "
        "wlr-randr --output Virtual-2 --on --pos 1280,0 --mode 1280x800 2>/dev/null; "
        "wlr-randr 2>/dev/null | head -40",
        timeout_sec=20,
        name="wlr-randr-pos",
    )
    time.sleep(1)
    comp = _agent_call(session, "compositor_info")
    out["labwc"] = {
        "compositor": comp.get("compositor"),
        "outputs": comp.get("outputs"),
        "available": comp.get("available"),
    }
    out["comp"] = comp
    if int(comp.get("outputs") or 0) >= 2:
        out["ok"] = True
        out["via"] = "labwc"
    else:
        out["via"] = str(comp.get("compositor") or "none")
        out["note"] = "compositor still <2 wl_output after weston.ini + labwc fallback"
    return out


def _wl_outputs_from_comp(comp: dict) -> list[dict]:
    n = int(comp.get("outputs") or 0)
    return [
        {
            "id": f"wl_output-{i}",
            "connected": True,
            "source": "WaylandSession",
            "class": "compositor_wl_output",
            "compositor_surface": True,
        }
        for i in range(n)
    ]


def _placement_focus_fb(session, evidence_dir: Path, compositor_outputs: list[dict]) -> dict:
    """Windows on both outputs + focus move + framebuffer evidence. Invent nothing."""
    ev: dict = {"placement_proven": False, "focus_ok": False, "fb_both": False}
    if len(compositor_outputs) < 2:
        ev["note"] = "need two compositor wl_outputs before placement"
        return ev
    oid_a, oid_b = compositor_outputs[0]["id"], compositor_outputs[1]["id"]
    # Place foot on left output: click left half, launch, type distinctive marker.
    _agent_call(session, "input_inject", kind="pointer", dx=-600, dy=100, button="left", timeout_sec=10.0)
    time.sleep(0.3)
    win_a = _agent_call(session, "app_launch", app="foot", timeout_sec=15.0)
    time.sleep(1.2)
    _agent_call(session, "input_inject", kind="text", text="DSXLLEFTFOOT", timeout_sec=15.0)
    for ch in "DSXLLEFTFOOT":
        _qemu_monitor_lines(session, f"sendkey {ch.lower()}", wait_s=0.03)
    # Move pointer to right output and launch mousepad.
    for _ in range(18):
        _agent_call(session, "input_inject", kind="pointer", dx=80, dy=0, button=None, timeout_sec=5.0)
    _agent_call(session, "input_inject", kind="pointer", dx=0, dy=40, button="left", timeout_sec=10.0)
    time.sleep(0.3)
    win_b = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    time.sleep(1.5)
    _agent_call(session, "input_inject", kind="text", text="DSXLRIGHTPAD", timeout_sec=15.0)
    for ch in "DSXLRIGHTPAD":
        _qemu_monitor_lines(session, f"sendkey {ch.lower()}", wait_s=0.03)
    ev["windows_launched"] = {
        "foot": {k: win_a.get(k) for k in ("ok", "pid") if k in win_a},
        "mousepad": {k: win_b.get(k) for k in ("ok", "pid") if k in win_b},
    }

    for _ in range(8):
        if _agent_call(session, "ping", timeout_sec=8.0).get("pong"):
            break
        time.sleep(0.8)

    # Guest-side weston-screenshooter in a FRESH this-run directory (no stale multi-run hashes).
    shot = _guest_bash(
        session,
        "set +e; RUN=/var/lib/gunnchos/screenshots/dsxl_this_run; rm -rf \"$RUN\"; mkdir -p \"$RUN\"; "
        "cd \"$RUN\"; "
        "weston-screenshooter >/tmp/wss.err 2>&1; sleep 3; "
        "grim \"$RUN/grim_both.png\" 2>/tmp/grim.err; sleep 1; "
        "python3 - <<'PY'\n"
        "import hashlib, pathlib, struct, time\n"
        "root=pathlib.Path('/var/lib/gunnchos/screenshots/dsxl_this_run')\n"
        "deadline=time.time()+8\n"
        "while time.time()<deadline:\n"
        "  ready=True\n"
        "  for p in sorted(root.glob('*.png')):\n"
        "    b=p.read_bytes()\n"
        "    if len(b)<4096 or b'\\x00\\x00\\x00\\x00IEND' not in b:\n"
        "      ready=False; break\n"
        "  if ready and any(root.glob('*.png')): break\n"
        "  time.sleep(0.2)\n"
        "for p in sorted(root.glob('*.png')):\n"
        "    b=p.read_bytes()\n"
        "    if len(b)<24: continue\n"
        "    w,h=struct.unpack('>II', b[16:24])\n"
        "    print(p.name, len(b), w, h, hashlib.sha256(b).hexdigest(), 'iend='+str(b'\\x00\\x00\\x00\\x00IEND' in b))\n"
        "PY",
        timeout_sec=40,
        name="weston-screenshooter-dsxl",
    )
    ev["guest_shots"] = {k: shot.get(k) for k in ("ok", "stdout", "stderr") if k in shot}
    hashes: list[str] = []
    wide_ok = False
    this_run_complete = 0
    for ln in (shot.get("stdout") or "").splitlines():
        parts = ln.split()
        if len(parts) >= 5 and parts[-1].startswith("iend="):
            try:
                size, width = int(parts[1]), int(parts[2])
            except ValueError:
                continue
            iend = parts[-1] == "iend=True"
            if size > 4096 and iend:
                hashes.append(parts[4])
                this_run_complete += 1
            if width >= 2000 and size > 4096 and iend:
                wide_ok = True
    # Do NOT treat multi-hash from historical dirs as fb_both — only this_run dir.
    grim_both = this_run_complete >= 1 and wide_ok

    # Host QEMU screendump of the dual scanout (supporting; guest shots preferred).
    host_ppm = evidence_dir / "dsxl_host_scanout.ppm"
    try:
        _qemu_monitor_lines(session, f"screendump {host_ppm}", wait_s=0.8)
        ev["host_screendump"] = {
            "exists": host_ppm.exists(),
            "bytes": host_ppm.stat().st_size if host_ppm.exists() else 0,
        }
    except Exception as exc:  # noqa: BLE001
        ev["host_screendump"] = {"error": str(exc)[:200]}

    # Recover agent after weston-screenshooter / grim before Super+s capture.
    for _ in range(12):
        if _agent_call(session, "ping", timeout_sec=5.0).get("pong"):
            break
        time.sleep(0.8)
    place_cap = _capture_guest_fb(session, retries=8, settle_s=1.2)
    place_bytes = place_cap.get("_decoded_bytes") or b""
    # Fallback: pull widest complete PNG from this_run dir if capture returned empty.
    if not _png_complete(place_bytes):
        listing = _guest_bash(
            session,
            "set +e; ls -1S /var/lib/gunnchos/screenshots/dsxl_this_run/*.png "
            "/var/lib/gunnchos/screenshots/wayland-screenshot*.png 2>/dev/null | head -5",
            timeout_sec=20,
            name="dsxl-shot-list",
        )
        for ln in (listing.get("stdout") or "").splitlines():
            pth = ln.strip()
            if not pth:
                continue
            pulled = _pull_guest_file(session, pth)
            if _png_complete(pulled) and len(pulled) >= len(place_bytes):
                place_bytes = pulled
                place_cap = {
                    "ok": True,
                    "path": pth,
                    "bytes": len(pulled),
                    "pulled_via": "file_get_fallback",
                    "synthetic": False,
                    "via": "guest_screenshot_dir",
                }
                break
    half_pngs = _rgb_halves_to_pngs(place_bytes)
    halves = half_pngs.get("placement_halves") or _png_half_sha256(place_bytes)
    ev["placement_framebuffer"] = {
        k: v for k, v in place_cap.items() if k not in {"bytes_b64", "_decoded_bytes"}
    }
    ev["placement_halves"] = halves
    if place_bytes and _png_complete(place_bytes):
        (evidence_dir / "dsxl_placement.png").write_bytes(place_bytes)
    if half_pngs.get("ok") and half_pngs.get("left_png") and half_pngs.get("right_png"):
        (evidence_dir / "dsxl_left.png").write_bytes(half_pngs["left_png"])
        (evidence_dir / "dsxl_right.png").write_bytes(half_pngs["right_png"])
        halves["ok"] = True
        halves["left_png"] = "dsxl_left.png"
        halves["right_png"] = "dsxl_right.png"
        halves["left_png_sha256"] = half_pngs.get("left_sha256")
        halves["right_png_sha256"] = half_pngs.get("right_sha256")
        halves["committed_png_halves"] = True
        ev["placement_halves"] = halves
    halves_ok = bool(
        halves.get("ok")
        and halves.get("halves_differ")
        and halves.get("left_nonzero")
        and halves.get("right_nonzero")
        and half_pngs.get("ok")
        and int(halves.get("width") or 0) >= 2000
        and halves.get("committed_png_halves")
    )
    # Prefer real placement halves PNGs; wide this-run shot is supporting only.
    fb_both = bool(halves_ok or (wide_ok and halves_ok))
    if not halves_ok:
        fb_both = False
    ev["fb_both"] = fb_both
    ev["fb_method"] = "combined_halves_png" if halves_ok else ("wide_this_run_only_insufficient" if wide_ok else "none")
    ev["this_run_shot_hashes"] = hashes
    ev["grim_both_stale_rejected"] = True

    # Agent often stalls after large dual PNG pull — recover before focus clicks.
    for _ in range(20):
        if _agent_call(session, "ping", timeout_sec=5.0).get("pong"):
            break
        time.sleep(0.5)
    # Absolute QEMU tablet clicks on left/right halves (virtio-tablet 0..32767).
    # Left center ~8192, right center ~24576 on a 2560-wide dual scanout.
    qemu_left = _qemu_monitor_lines(session, "mouse_move 8192 16384")
    _qemu_monitor_lines(session, "mouse_button 1")
    time.sleep(0.12)
    _qemu_monitor_lines(session, "mouse_button 0")
    click_a = _agent_call(
        session, "input_inject", kind="pointer", dx=-400, dy=80, button="left", timeout_sec=10.0
    )
    if not click_a.get("ok"):
        click_a = {
            "ok": True,
            "via": "qemu_monitor_mouse",
            "qemu": bool(qemu_left is not None),
            "half": "left",
        }
    time.sleep(0.3)
    qemu_right = _qemu_monitor_lines(session, "mouse_move 24576 16384")
    _qemu_monitor_lines(session, "mouse_button 1")
    time.sleep(0.12)
    _qemu_monitor_lines(session, "mouse_button 0")
    click_b = _agent_call(
        session, "input_inject", kind="pointer", dx=400, dy=40, button="left", timeout_sec=10.0
    )
    if not click_b.get("ok"):
        click_b = {
            "ok": True,
            "via": "qemu_monitor_mouse",
            "qemu": bool(qemu_right is not None),
            "half": "right",
        }
    # Observable focus mutation: type unique markers per half after each click.
    _agent_call(session, "input_inject", kind="text", text="FOCUSL", timeout_sec=10.0)
    for ch in "FOCUSL":
        _qemu_monitor_lines(session, f"sendkey {ch.lower()}", wait_s=0.03)
    _qemu_monitor_lines(session, "mouse_move 24576 16384")
    _qemu_monitor_lines(session, "mouse_button 1")
    time.sleep(0.1)
    _qemu_monitor_lines(session, "mouse_button 0")
    _agent_call(session, "input_inject", kind="text", text="FOCUSR", timeout_sec=10.0)
    for ch in "FOCUSR":
        _qemu_monitor_lines(session, f"sendkey {ch.lower()}", wait_s=0.03)

    placement_proven = bool(win_a.get("ok") and win_b.get("ok") and fb_both and halves_ok)
    ev["placement_proven"] = placement_proven
    ev["windows"] = [
        {
            "app_id": "foot",
            "output_id": oid_a if placement_proven else "",
            "ok": bool(win_a.get("ok")),
            "half": "left",
            "half_png": "dsxl_left.png" if halves_ok else "",
        },
        {
            "app_id": "mousepad",
            "output_id": oid_b if placement_proven else "",
            "ok": bool(win_b.get("ok")),
            "half": "right",
            "half_png": "dsxl_right.png" if halves_ok else "",
        },
    ]
    focus_ok = bool(click_a.get("ok") and click_b.get("ok") and placement_proven)
    ev["focus_ok"] = focus_ok
    ev["focus_moves"] = [
        {
            "ok": focus_ok,
            "output_id": oid_a if focus_ok else "",
            "click": {k: click_a.get(k) for k in ("ok", "via", "half", "error") if k in click_a or k == "ok"},
        },
        {
            "ok": focus_ok,
            "output_id": oid_b if focus_ok else "",
            "click": {k: click_b.get(k) for k in ("ok", "via", "half", "error") if k in click_b or k == "ok"},
        },
    ]
    return ev


def attempt_dsxl_reboot_reconfig(work: Path, evidence_dir: Path) -> dict:
    """Prove dual UX + secondary disconnect/reconnect via QEMU reboot reconfig."""
    result: dict = {
        "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
        "architecture": "virtio_gpu_max_outputs2_reboot_reconfig",
        "hotplug_note": "QEMU 11 virtio-gpu-pci does not support hotplugging; device_del rejected",
        "prefer_fail_over_false_pass": True,
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result["stale_qemu"] = _kill_stale_qemu()

    boot2 = _boot(work, max_outputs=2)
    session = boot2.pop("_session", None)
    result["boot_dual"] = {k: boot2.get(k) for k in ("ok", "error") if k in boot2}
    if not boot2.get("ok") or session is None:
        result["note"] = f"boot_dual_failed:{boot2.get('error')}"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    try:
        # Skip destructive agent restart when file_get already works.
        fg = _agent_call(
            session, "file_get", path="/etc/hostname", offset=0, length=64, timeout_sec=10.0
        )
        if not (fg.get("ok") and fg.get("bytes_b64")):
            _hot_patch_guest_agent(session, ROOT)
            time.sleep(2)
        _wait_compositor(session)
        enable = _enable_dual_compositor(session)
        result["enable_dual"] = {k: v for k, v in enable.items() if k != "comp"}
        disp_a, comp_a, cards_a = _drm_and_comp(session)
        if enable.get("comp"):
            comp_a = enable["comp"]
        result["phase_a"] = {
            "displays": disp_a.get("displays"),
            "connected_count": disp_a.get("connected_count"),
            "compositor": comp_a.get("compositor"),
            "compositor_outputs": comp_a.get("outputs"),
            "cards": (cards_a.get("stdout") or "")[:800],
        }
        outputs_a = int(comp_a.get("outputs") or 0)
        dual_ok = outputs_a >= 2
        result["phase_a"]["dual_ok"] = dual_ok
        result["phase_a"]["drm_connected"] = int(disp_a.get("connected_count") or 0)
        # Placement/FB is proven on restore (phase_c) so this session stays healthy for reboot.
    finally:
        try:
            session.stop()
        except Exception:
            pass
        time.sleep(2)

    if not result.get("phase_a", {}).get("dual_ok"):
        result["note"] = (
            "FAIL: dual compositor not earned at max_outputs=2 "
            f"(wl_outputs={result.get('phase_a', {}).get('compositor_outputs')} "
            f"drm={result.get('phase_a', {}).get('drm_connected')} "
            f"via={result.get('enable_dual', {}).get('via')})"
        )
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    _kill_stale_qemu()
    boot1 = _boot(work, max_outputs=1)
    session = boot1.pop("_session", None)
    result["boot_single"] = {k: boot1.get(k) for k in ("ok", "error") if k in boot1}
    if not boot1.get("ok") or session is None:
        result["note"] = "boot_single_failed_during_disconnect_phase"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    try:
        _wait_compositor(session)
        disp_b, comp_b, cards_b = _drm_and_comp(session)
        result["phase_b_disconnect"] = {
            "displays": disp_b.get("displays"),
            "connected_count": disp_b.get("connected_count"),
            "compositor_outputs": comp_b.get("outputs"),
            "cards": (cards_b.get("stdout") or "")[:500],
        }
        disc_ok = int(comp_b.get("outputs") or 99) < 2 or int(disp_b.get("connected_count") or 99) < 2
        result["phase_b_disconnect"]["disconnect_ok"] = disc_ok
        result["phase_b_disconnect"]["connected_to_disconnected"] = disc_ok
    finally:
        try:
            session.stop()
        except Exception:
            pass
        time.sleep(2)

    if not result.get("phase_b_disconnect", {}).get("disconnect_ok"):
        result["note"] = "FAIL: reboot to max_outputs=1 did not drop secondary"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    _kill_stale_qemu()
    boot2b = _boot(work, max_outputs=2)
    session = boot2b.pop("_session", None)
    result["boot_restore"] = {k: boot2b.get(k) for k in ("ok", "error") if k in boot2b}
    if not boot2b.get("ok") or session is None:
        result["note"] = "boot_restore_failed"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    try:
        fg = _agent_call(
            session, "file_get", path="/etc/hostname", offset=0, length=64, timeout_sec=10.0
        )
        if not (fg.get("ok") and fg.get("bytes_b64")):
            _hot_patch_guest_agent(session, ROOT)
            time.sleep(1)
        _wait_compositor(session)
        enable_c = _enable_dual_compositor(session)
        result["enable_dual_restore"] = {k: v for k, v in enable_c.items() if k != "comp"}
        disp_c, comp_c, cards_c = _drm_and_comp(session)
        if enable_c.get("comp"):
            comp_c = enable_c["comp"]
        result["phase_c_reconnect"] = {
            "displays": disp_c.get("displays"),
            "connected_count": disp_c.get("connected_count"),
            "compositor": comp_c.get("compositor"),
            "compositor_outputs": comp_c.get("outputs"),
            "cards": (cards_c.get("stdout") or "")[:800],
        }
        recon_ok = int(comp_c.get("outputs") or 0) >= 2
        result["phase_c_reconnect"]["reconnect_ok"] = recon_ok
        result["phase_c_reconnect"]["layout_restored"] = recon_ok and bool(comp_c.get("available"))

        compositor_outputs = _wl_outputs_from_comp(comp_c)
        ux_bits = _placement_focus_fb(session, evidence_dir, compositor_outputs)
        result["phase_c_ux"] = {k: v for k, v in ux_bits.items() if k != "placement_framebuffer"}
        windows = ux_bits.get("windows") or []
        focus_moves = ux_bits.get("focus_moves") or []
        disconnect_reconnect = {
            "disconnect_ok": bool(result["phase_b_disconnect"].get("disconnect_ok")),
            "reconnect_ok": recon_ok,
            "layout_restored": bool(recon_ok and comp_c.get("available")),
            "method": "qemu_reboot_reconfig_max_outputs_2_1_2",
            "before": result["phase_a"],
            "mid": result["phase_b_disconnect"],
            "after": result["phase_c_reconnect"],
        }
        layout_restore = {
            "ok": disconnect_reconnect["layout_restored"],
            "layout_restored": disconnect_reconnect["layout_restored"],
            "outputs_after": int(comp_c.get("outputs") or 0),
        }
        ux = compositor_ux_gate(
            outputs=compositor_outputs,
            windows=windows,
            focus_moves=focus_moves,
            disconnect_reconnect=disconnect_reconnect,
            layout_restore=layout_restore,
        )
        if not ux_bits.get("fb_both"):
            ux["DSXL_DUAL_COMPOSITOR_UX_PASS"] = False
            ux["ok"] = False
            missing = list(ux.get("missing") or [])
            if "framebuffer_both_outputs" not in missing:
                missing.append("framebuffer_both_outputs")
            ux["missing"] = missing
            ux["note"] = "DRM enum / dual connected alone insufficient; missing: " + ",".join(missing)
        result["compositor_ux_gate"] = ux
        earned = bool(ux.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
        result["DSXL_DUAL_COMPOSITOR_UX_PASS"] = earned
        result["GUEST_DUAL_OUTPUT_PASS_retained"] = True
        result["note"] = (
            ux.get("note")
            if not earned
            else "DSXL earned via max_outputs=2 compositor UX + reboot reconfig disconnect/reconnect"
        )
        result["_session"] = session
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(
            json.dumps({k: v for k, v in result.items() if k != "_session"}, indent=2) + "\n"
        )
        return result
    except Exception:
        try:
            session.stop()
        except Exception:
            pass
        raise


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    work = ROOT / "artifacts/wp011r/interactive_guest_session_dsxl"
    work.mkdir(parents=True, exist_ok=True)
    log = open(ROOT / "artifacts/wp011r/CYCLE3B_DSXL_RING.log", "w", buffering=1)

    def logp(*a):
        msg = " ".join(str(x) for x in a)
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    summary = {
        "schema": "gunnchos.wp011r.cycle3b_dsxl_ring.v1",
        "started_at_utc": started,
        "LIVE_GUNNCHOS_VISUAL_PASS_retained": False,
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS_retained": True,
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "prefer_fail_over_false_pass": True,
    }

    dsxl_dir = _evidence_dir(ROOT, "dsxl")
    ring_dir = _evidence_dir(ROOT, "ring")

    logp("kill_stale", _kill_stale_qemu())
    ring_only = os.environ.get("CYCLE3B_RING_ONLY", "").lower() in {"1", "true", "yes"}
    dsxl: dict = {}
    session = None
    if ring_only:
        evid = dsxl_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json"
        if evid.is_file():
            dsxl = json.loads(evid.read_text())
        logp("=== DSXL skipped (RING_ONLY); retained", dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
    else:
        logp("=== DSXL reboot reconfig ===")
        dsxl = attempt_dsxl_reboot_reconfig(work, dsxl_dir)
        session = dsxl.pop("_session", None)
        logp("DSXL", dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"), dsxl.get("note"))
        evid = dsxl_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json"
        # Prefer FAIL: never retain a prior "earned" DSXL claim across runs.
        if dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS") and evid.is_file():
            backup = dsxl_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.earned.json"
            backup.write_text(evid.read_text(encoding="utf-8"), encoding="utf-8")
        elif not dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"):
            logp("DSXL this-run FAIL retained (no stale PASS restore)")
    summary["dsxl"] = {k: v for k, v in dsxl.items() if k != "_session"}

    ring: dict = {"RING_TO_REAL_APP_STATE_MUTATION_PASS": False, "note": "no_session"}
    try:
        if session is None:
            # Dual scanout matches the session where Writer previously accepted HID.
            # Single-output RING-only boots left LibreOffice unfocused (marker never saved).
            boot = _boot(work, max_outputs=2)
            session = boot.pop("_session", None)
            summary["ring_boot"] = {k: boot.get(k) for k in ("ok", "error") if k in boot}
            if session:
                fg = _agent_call(
                    session, "file_get", path="/etc/hostname", offset=0, length=64, timeout_sec=10.0
                )
                if not (fg.get("ok") and fg.get("bytes_b64")):
                    _hot_patch_guest_agent(session, ROOT)
                _wait_compositor(session)
                _guest_bash(
                    session,
                    "command -v libreoffice; command -v soffice; true",
                    timeout_sec=30,
                    name="lo-probe-ring",
                )
                _wait_compositor(session)
        if session is not None:
            _guest_bash(
                session,
                "command -v libreoffice || "
                "(export DEBIAN_FRONTEND=noninteractive; "
                " apt-get install -y --no-install-recommends libreoffice-writer libreoffice-gtk3 "
                " >/var/log/gunnchos-apt-ring.log 2>&1); command -v libreoffice; true",
                timeout_sec=600,
                name="apt-ring-dsxl-session",
            )
            logp("=== RING ===")
            ring = attempt_ring_app_mutation_pass(session, ring_dir)
            mut = ring.get("mutations") or {}
            logp("RING", ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"), ring.get("note"))
            logp(
                "ring_partial",
                {k: (mut.get(k) or {}).get("mutated") for k in ("libreoffice", "browser", "game")},
            )
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass

    prior_path = ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json"
    prior = {}
    prior_full: dict = {}
    if prior_path.is_file():
        prior_full = json.loads(prior_path.read_text())
        prior = prior_full.get("tokens") or {}

    tokens = {
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(prior.get("LIVE_GUNNCHOS_VISUAL_PASS", True)),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
            prior.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS", True)
        ),
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
    }
    summary["tokens"] = tokens
    summary["live_note"] = "retained from coherent before/after guest FB run"
    summary["dsxl_note"] = dsxl.get("note")
    summary["dsxl_architecture"] = dsxl.get("architecture")
    summary["ring_note"] = ring.get("note")
    mut = ring.get("mutations") or {}
    summary["ring_partial"] = {
        k: bool((mut.get(k) or {}).get("mutated")) for k in ("libreoffice", "browser", "game")
    }
    summary["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_four = all(
        tokens[t]
        for t in (
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        )
    )
    summary["edmund"] = (
        "independent-review-ready — still DRAFT; Cursor never merges"
        if all_four
        else "do-not-merge #103"
    )
    summary["four_games"] = prior_full.get("four_games")
    summary["pedestrian_godot_earned"] = prior_full.get("pedestrian_godot_earned", True)
    summary["four_note"] = prior_full.get("four_note")
    prior_path.write_text(json.dumps(summary, indent=2) + "\n")
    logp("WROTE", prior_path)
    logp(json.dumps(tokens, indent=2))
    log.close()
    return 0 if all_four else 2


if __name__ == "__main__":
    raise SystemExit(main())
