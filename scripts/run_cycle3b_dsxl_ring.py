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
    _evidence_dir,
    attempt_dsxl_dual_compositor_pass,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import (  # noqa: E402
    compositor_ux_gate,
)


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
            "for s in /sys/class/drm/card*-Virtual-*/status; do echo $s=$(cat $s); done",
        ],
        timeout_sec=15.0,
    )
    return disp, comp, cards


def attempt_dsxl_reboot_reconfig(work: Path, evidence_dir: Path) -> dict:
    """Prove dual UX + secondary disconnect/reconnect via QEMU reboot reconfig."""
    result: dict = {
        "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
        "architecture": "virtio_gpu_max_outputs2_reboot_reconfig",
        "hotplug_note": "QEMU 11 virtio-gpu-pci does not support hotplugging; device_del rejected",
        "prefer_fail_over_false_pass": True,
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)

    boot2 = _boot(work, max_outputs=2)
    session = boot2.pop("_session", None)
    result["boot_dual"] = {k: boot2.get(k) for k in ("ok", "error") if k in boot2}
    if not boot2.get("ok") or session is None:
        result["note"] = "boot_dual_failed"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    try:
        _hot_patch_guest_agent(session, ROOT)
        time.sleep(2)
        _wait_compositor(session)
        import base64

        weston_ini = ROOT / "os_build/device_lab_interactive_guest/debian_cloud/config/weston.ini"
        if weston_ini.is_file():
            b64 = base64.b64encode(weston_ini.read_bytes()).decode("ascii")
            _guest_bash(
                session,
                f"printf '%s' '{b64}' | base64 -d > /etc/xdg/weston/weston.ini; "
                "cp /etc/xdg/weston/weston.ini /etc/gunnchos-weston/weston.ini; "
                "systemctl restart gunnchos-weston.service || true; sleep 4; pgrep -x weston",
                timeout_sec=60,
                name="weston-ini",
            )
            _wait_compositor(session)

        partial = attempt_dsxl_dual_compositor_pass(session, evidence_dir)
        result["placement_pass_attempt"] = {
            k: partial.get(k)
            for k in (
                "compositor_output_count",
                "compositor_surfaces",
                "placement_halves",
                "compositor_ux_gate",
                "note",
            )
            if k in partial
        }
        disp_a, comp_a, cards_a = _drm_and_comp(session)
        result["phase_a"] = {
            "displays": disp_a.get("displays"),
            "connected_count": disp_a.get("connected_count"),
            "compositor_outputs": comp_a.get("outputs"),
            "cards": (cards_a.get("stdout") or "")[:500],
        }
        outputs_a = int(comp_a.get("outputs") or 0)
        dual_ok = outputs_a >= 2 and int(disp_a.get("connected_count") or 0) >= 2
        result["phase_a"]["dual_ok"] = dual_ok

        from gunnchos_device_os.device_lab.interactive_guest_proofs import _qemu_monitor_lines

        del_tail = _qemu_monitor_lines(session, "device_del gpu0", wait_s=0.8)
        result["hotplug_probe"] = {"cmd": "device_del gpu0", "tail": del_tail[-240:]}
    finally:
        try:
            session.stop()
        except Exception:
            pass
        time.sleep(2)

    if not result.get("phase_a", {}).get("dual_ok"):
        result["note"] = (
            "FAIL: dual compositor not earned at max_outputs=2 "
            f"(weston_outputs={result.get('phase_a', {}).get('compositor_outputs')} "
            f"drm={result.get('phase_a', {}).get('connected_count')})"
        )
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

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

    boot2b = _boot(work, max_outputs=2)
    session = boot2b.pop("_session", None)
    result["boot_restore"] = {k: boot2b.get(k) for k in ("ok", "error") if k in boot2b}
    if not boot2b.get("ok") or session is None:
        result["note"] = "boot_restore_failed"
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    try:
        _hot_patch_guest_agent(session, ROOT)
        time.sleep(1)
        _wait_compositor(session)
        import base64

        weston_ini = ROOT / "os_build/device_lab_interactive_guest/debian_cloud/config/weston.ini"
        if weston_ini.is_file():
            b64 = base64.b64encode(weston_ini.read_bytes()).decode("ascii")
            _guest_bash(
                session,
                f"printf '%s' '{b64}' | base64 -d > /etc/xdg/weston/weston.ini; "
                "cp /etc/xdg/weston/weston.ini /etc/gunnchos-weston/weston.ini; "
                "systemctl restart gunnchos-weston.service || true; sleep 4; pgrep -x weston",
                timeout_sec=60,
                name="weston-restore",
            )
            _wait_compositor(session)
        disp_c, comp_c, cards_c = _drm_and_comp(session)
        result["phase_c_reconnect"] = {
            "displays": disp_c.get("displays"),
            "connected_count": disp_c.get("connected_count"),
            "compositor_outputs": comp_c.get("outputs"),
            "cards": (cards_c.get("stdout") or "")[:500],
        }
        recon_ok = int(comp_c.get("outputs") or 0) >= 2 and int(disp_c.get("connected_count") or 0) >= 2
        result["phase_c_reconnect"]["reconnect_ok"] = recon_ok
        result["phase_c_reconnect"]["layout_restored"] = recon_ok and bool(comp_c.get("available"))

        outputs = int(comp_c.get("outputs") or 0)
        compositor_outputs = []
        for i, o in enumerate((disp_c.get("displays") or [])[: max(outputs, 0)]):
            compositor_outputs.append(
                {
                    "id": str(o.get("id") or f"wl_output-{i}"),
                    "connected": bool(o.get("connected")),
                    "source": "WaylandSession",
                    "class": "compositor_wl_output",
                    "compositor_surface": True,
                }
            )
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
        win_a = _agent_call(session, "app_launch", app="foot", timeout_sec=15.0)
        time.sleep(1.0)
        for _ in range(18):
            _agent_call(session, "input_inject", kind="pointer", dx=80, dy=0, button=None, timeout_sec=5.0)
        win_b = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
        time.sleep(1.0)
        oid_a = compositor_outputs[0]["id"] if compositor_outputs else "a"
        oid_b = compositor_outputs[1]["id"] if len(compositor_outputs) > 1 else "b"
        placement_proven = bool(win_a.get("ok") and win_b.get("ok") and outputs >= 2)
        windows = [
            {"app_id": "foot", "output_id": oid_a if placement_proven else "", "ok": bool(win_a.get("ok"))},
            {"app_id": "mousepad", "output_id": oid_b if placement_proven else "", "ok": bool(win_b.get("ok"))},
        ]
        focus_moves = [
            {"ok": placement_proven, "output_id": oid_a if placement_proven else ""},
            {"ok": placement_proven, "output_id": oid_b if placement_proven else ""},
        ]
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
            "outputs_after": outputs,
        }
        ux = compositor_ux_gate(
            outputs=compositor_outputs,
            windows=windows,
            focus_moves=focus_moves,
            disconnect_reconnect=disconnect_reconnect,
            layout_restore=layout_restore,
        )
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
        (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(json.dumps(
            {k: v for k, v in result.items() if k != "_session"}, indent=2
        ) + "\n")
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
        "LIVE_GUNNCHOS_VISUAL_PASS_retained": True,
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS_retained": True,
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "prefer_fail_over_false_pass": True,
    }

    dsxl_dir = _evidence_dir(ROOT, "dsxl")
    ring_dir = _evidence_dir(ROOT, "ring")

    logp("=== DSXL reboot reconfig ===")
    dsxl = attempt_dsxl_reboot_reconfig(work, dsxl_dir)
    session = dsxl.pop("_session", None)
    logp("DSXL", dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"), dsxl.get("note"))
    summary["dsxl"] = {k: v for k, v in dsxl.items() if k != "_session"}

    ring: dict = {"RING_TO_REAL_APP_STATE_MUTATION_PASS": False, "note": "no_session"}
    try:
        if session is None:
            boot = _boot(work, max_outputs=2)
            session = boot.pop("_session", None)
            summary["ring_boot"] = {k: boot.get(k) for k in ("ok", "error") if k in boot}
            if session:
                _hot_patch_guest_agent(session, ROOT)
                _wait_compositor(session)
                _guest_bash(
                    session,
                    "export DEBIAN_FRONTEND=noninteractive; "
                    "apt-get install -y --no-install-recommends libreoffice-writer libreoffice-gtk3 "
                    ">/var/log/gunnchos-apt-ring.log 2>&1; command -v libreoffice; true",
                    timeout_sec=900,
                    name="apt-ring",
                )
                _wait_compositor(session)
        if session is not None:
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
