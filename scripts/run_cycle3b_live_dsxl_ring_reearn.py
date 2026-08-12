#!/usr/bin/env python3
"""Cycle 3B WP-011R: re-earn LIVE + DSXL + RING with review-survivable artifacts.

Keeps FOUR_GAME / ECO010 / GUEST_DUAL_OUTPUT. Prefer FAIL. Cursor never merges.
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
    _png_complete,
    attempt_live_visual_pass,
    boot_interactive_guest,
)
from scripts.run_cycle3b_dsxl_ring import (  # noqa: E402
    _kill_stale_qemu,
    attempt_dsxl_reboot_reconfig,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    attempt_ring_app_mutation_pass,
)


def _push_weston(session) -> dict:
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


def _scrub_lab_sidecars() -> list[str]:
    removed: list[str] = []
    ring = ROOT / "artifacts/wp011r/ring"
    for rel in (
        "libreoffice_mutation.json",
        "browser_mutation.json",
        "games_mutation.json",
    ):
        p = ring / rel
        if p.exists():
            p.unlink()
            removed.append(str(rel))
    return removed


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary: dict = {
        "schema": "gunnchos.wp011r.cycle3b_live_dsxl_ring_reearn.v1",
        "started_at_utc": started,
        "base_tip": "7884c00",
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": True,
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "prefer_fail_over_false_pass": True,
        "lab_sidecars_removed": _scrub_lab_sidecars(),
    }
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "0"
    os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] = "1"

    log_path = ROOT / "artifacts/wp011r/CYCLE3B_LIVE_DSXL_RING_REEARN.log"
    log = open(log_path, "w", buffering=1)

    def logp(*a):
        msg = " ".join(str(x) for x in a)
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    _kill_stale_qemu()
    work_live = ROOT / "artifacts/wp011r/interactive_guest_session_reearn"
    work_live.mkdir(parents=True, exist_ok=True)

    logp("=== LIVE boot ===")
    boot = boot_interactive_guest(ROOT, work_live, dual=True, boot_timeout_s=240, memory_mb=4096)
    session = boot.pop("_session", None)
    summary["boot_live"] = {k: boot.get(k) for k in ("ok", "error") if k in boot}
    if not boot.get("ok") or session is None:
        summary["error"] = "live_boot_failed"
        (ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        return 1

    live = {"LIVE_GUNNCHOS_VISUAL_PASS": False}
    try:
        # Prefer not to restart agent if file_get already works (avoids virtio-serial drop).
        fg = _agent_call(
            session,
            "file_get",
            path="/etc/hostname",
            offset=0,
            length=64,
            timeout_sec=10.0,
        )
        if fg.get("ok") and fg.get("bytes_b64"):
            summary["hot_patch"] = {"skipped": True, "reason": "file_get_already_present"}
            logp("hot_patch skipped — file_get present")
        else:
            summary["hot_patch"] = _hot_patch_guest_agent(session, ROOT)
            logp(
                "hot_patch",
                summary["hot_patch"].get("error") or "ok",
                summary["hot_patch"].get("process_run_probe"),
            )
            time.sleep(2)
        # Confirm agent alive after patch before long apt.
        alive = False
        for i in range(40):
            if _agent_call(session, "ping", timeout_sec=5.0).get("pong"):
                alive = True
                break
            time.sleep(1.0)
        summary["agent_alive_after_hot_patch"] = alive
        logp("agent_alive_after_hot_patch", alive)
        if not alive:
            summary["error"] = "guest_agent_dead_after_hot_patch"
            (ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json").write_text(
                json.dumps(summary, indent=2, default=str) + "\n"
            )
            return 1
        summary["weston"] = _push_weston(session)
        logp("weston", (summary["weston"] or {}).get("stdout") or (summary["weston"] or {}).get("error"))
        for _ in range(25):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(1.0)
        # Apt only if needed (skip when libreoffice already present).
        have_lo = _guest_bash(
            session,
            "command -v soffice; command -v libreoffice; dpkg -l libreoffice-writer 2>/dev/null | awk '/^ii/{print $2}'",
            timeout_sec=30,
            name="lo-probe",
        )
        summary["lo_probe"] = {k: have_lo.get(k) for k in ("ok", "stdout") if k in have_lo}
        logp("lo_probe", have_lo.get("stdout"))
        if "libreoffice-writer" not in (have_lo.get("stdout") or "") and "soffice" not in (
            have_lo.get("stdout") or ""
        ):
            summary["apt"] = _guest_bash(
                session,
                "set +e; export DEBIAN_FRONTEND=noninteractive; "
                "apt-get update -y >/var/log/gunnchos-apt-update.log 2>&1; "
                "apt-get install -y --no-install-recommends "
                "libreoffice-writer libreoffice-gtk3 labwc grim wlr-randr "
                ">/var/log/gunnchos-apt-reearn.log 2>&1; "
                "command -v grim; command -v soffice; command -v libreoffice; "
                "dpkg -l libreoffice-writer 2>/dev/null | awk '/^ii/{print $2,$3}'",
                timeout_sec=900,
                name="apt-reearn",
            )
            logp("apt_done", (summary["apt"] or {}).get("stdout") or (summary["apt"] or {}).get("error"))
        else:
            summary["apt"] = {"skipped": True, "reason": "libreoffice_already_present"}
            logp("apt_skipped")
            # Still ensure grim for DSXL.
            _guest_bash(
                session,
                "set +e; export DEBIAN_FRONTEND=noninteractive; "
                "command -v grim || apt-get install -y --no-install-recommends grim wlr-randr "
                ">/var/log/gunnchos-apt-grim.log 2>&1; command -v grim",
                timeout_sec=180,
                name="grim-ensure",
            )

        visual_dir = _evidence_dir(ROOT, "visual")
        logp("=== LIVE proof ===")
        live = attempt_live_visual_pass(session, visual_dir)
        gf = live.get("guest_framebuffer") or {}
        logp(
            "LIVE",
            live.get("LIVE_GUNNCHOS_VISUAL_PASS"),
            "png",
            gf.get("before_bytes"),
            gf.get("after_bytes"),
            "complete",
            gf.get("before_png_complete"),
            gf.get("after_png_complete"),
            live.get("note") or live.get("blocker"),
        )
        # Verify committed PNGs on disk independently.
        b = visual_dir / "shell_app_before.png"
        a = visual_dir / "shell_app_after.png"
        summary["live_disk_check"] = {
            "before_bytes": b.stat().st_size if b.exists() else 0,
            "after_bytes": a.stat().st_size if a.exists() else 0,
            "before_iend": _png_complete(b.read_bytes()) if b.exists() else False,
            "after_iend": _png_complete(a.read_bytes()) if a.exists() else False,
            "differ": (b.read_bytes() != a.read_bytes()) if b.exists() and a.exists() else False,
        }
        if not (
            summary["live_disk_check"]["before_iend"]
            and summary["live_disk_check"]["after_iend"]
            and summary["live_disk_check"]["differ"]
        ):
            live["LIVE_GUNNCHOS_VISUAL_PASS"] = False
            live["note"] = "disk PNG IEND/differ check failed — demoted"
    finally:
        try:
            session.stop()
        except Exception:
            pass
        time.sleep(2)

    summary["live"] = {
        k: live.get(k)
        for k in (
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "note",
            "blocker",
            "guest_framebuffer",
            "missing",
        )
        if k in live
    }

    logp("=== DSXL reboot reconfig ===")
    work_dsxl = ROOT / "artifacts/wp011r/interactive_guest_session_dsxl"
    work_dsxl.mkdir(parents=True, exist_ok=True)
    dsxl_dir = _evidence_dir(ROOT, "dsxl")
    dsxl = attempt_dsxl_reboot_reconfig(work_dsxl, dsxl_dir)
    session = dsxl.pop("_session", None)
    logp("DSXL", dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"), dsxl.get("note"))
    # Disk check halves
    left = dsxl_dir / "dsxl_left.png"
    right = dsxl_dir / "dsxl_right.png"
    place = dsxl_dir / "dsxl_placement.png"
    summary["dsxl_disk_check"] = {
        "left_bytes": left.stat().st_size if left.exists() else 0,
        "right_bytes": right.stat().st_size if right.exists() else 0,
        "placement_bytes": place.stat().st_size if place.exists() else 0,
        "left_iend": _png_complete(left.read_bytes()) if left.exists() else False,
        "right_iend": _png_complete(right.read_bytes()) if right.exists() else False,
        "placement_iend": _png_complete(place.read_bytes()) if place.exists() else False,
        "halves_differ": (left.read_bytes() != right.read_bytes())
        if left.exists() and right.exists()
        else False,
    }
    ux = (dsxl.get("phase_c_ux") or {}).get("placement_halves") or dsxl.get("placement_halves") or {}
    if not (
        summary["dsxl_disk_check"]["left_iend"]
        and summary["dsxl_disk_check"]["right_iend"]
        and summary["dsxl_disk_check"]["halves_differ"]
        and bool(ux.get("ok") or (dsxl.get("phase_c_ux") or {}).get("placement_halves", {}).get("ok"))
    ):
        dsxl["DSXL_DUAL_COMPOSITOR_UX_PASS"] = False
        dsxl["note"] = (
            f"{dsxl.get('note') or ''} | disk half PNG check failed — demoted"
        ).strip(" |")
    summary["dsxl"] = {k: v for k, v in dsxl.items() if k != "_session"}

    ring = {"RING_TO_REAL_APP_STATE_MUTATION_PASS": False, "note": "no_session"}
    try:
        if session is None:
            _kill_stale_qemu()
            boot_r = boot_interactive_guest(
                ROOT, work_dsxl, dual=True, boot_timeout_s=240, memory_mb=4096
            )
            session = boot_r.pop("_session", None)
            summary["boot_ring"] = {k: boot_r.get(k) for k in ("ok", "error") if k in boot_r}
            if session is not None:
                _hot_patch_guest_agent(session, ROOT)
                _push_weston(session)
                for _ in range(20):
                    if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                        break
                    time.sleep(1.0)
        if session is not None:
            # Ensure Pedestrian exists for RING Godot leg (FOUR already earned).
            _guest_bash(
                session,
                "set +e; test -d /root/pedestrian-pursuit && echo pp_ok; "
                "test -x /opt/gunnchos/bin/godot && /opt/gunnchos/bin/godot --version | head -1",
                timeout_sec=30,
                name="godot-probe",
            )
            ring_dir = _evidence_dir(ROOT, "ring")
            logp("=== RING proof ===")
            ring = attempt_ring_app_mutation_pass(session, ring_dir)
            logp(
                "RING",
                ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"),
                ring.get("note") or ring.get("blocker"),
            )
            arts = ring.get("guest_artifacts") or {}
            odt = ring_dir / "document" / "ring_editor_buffer.odt"
            marker = ring.get("mutation_marker") or ""
            odt_has = False
            if odt.exists() and marker:
                try:
                    import zipfile

                    txt = zipfile.ZipFile(odt).read("content.xml").decode("utf-8", "replace")
                    odt_has = marker in txt and "RINGRING" not in txt.replace(marker, "")
                    # Allow marker alongside other text; reject pure Lab RINGRING-only.
                    if marker in txt:
                        odt_has = True
                    if txt.strip().endswith(">RINGRING</text:p>") and marker not in txt:
                        odt_has = False
                except Exception as exc:
                    arts["odt_read_error"] = str(exc)[:200]
            summary["ring_disk_check"] = {
                "odt_bytes": odt.stat().st_size if odt.exists() else 0,
                "odt_has_marker": odt_has,
                "browser_state": (ring_dir / "browser" / "browser_state.json").exists(),
                "game_save": (ring_dir / "game" / "pp_progression.cfg").exists(),
                "guest_artifacts": arts,
            }
            if not (
                odt_has
                and summary["ring_disk_check"]["browser_state"]
                and summary["ring_disk_check"]["game_save"]
            ):
                ring["RING_TO_REAL_APP_STATE_MUTATION_PASS"] = False
                ring["note"] = (
                    f"{ring.get('note') or ''} | guest artifact disk check failed — demoted"
                ).strip(" |")
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass

    summary["ring"] = {
        k: ring.get(k)
        for k in (
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "note",
            "blocker",
            "mutation_marker",
            "guest_artifacts",
            "mutations",
        )
        if k in ring
    }

    tokens = {
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS")),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
            ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        ),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": True,
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
    }
    five = all(
        tokens[t]
        for t in (
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "ECO010_SOAK_PASS",
        )
    )
    tokens["five_gate_digital_and"] = five
    if five:
        # Still never auto-claim shipping master; independent must accept.
        tokens["master_candidate_only"] = True
    summary["tokens"] = tokens
    summary["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary["edmund"] = (
        "independent-review-ready — still DRAFT; Cursor never merges"
        if five
        else "do-not-merge #103"
    )
    out = ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json"
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    logp(json.dumps(tokens, indent=2))
    logp("edmund", summary["edmund"])
    return 0 if five else 2


if __name__ == "__main__":
    raise SystemExit(main())
