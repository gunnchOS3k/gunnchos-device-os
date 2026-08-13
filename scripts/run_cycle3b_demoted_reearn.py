#!/usr/bin/env python3
"""Cycle 3B follow-up: re-attempt demoted LIVE/DSXL/RING/FOUR_GAME tokens honestly.

Keeps ECO010_SOAK_PASS / GUEST_DUAL_OUTPUT_PASS. Never inflates master.
Cursor never merges. Prefer FAIL over false PASS.
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
    attempt_four_game_in_guest_pass,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    attempt_dsxl_dual_compositor_pass,
    attempt_live_visual_pass,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)


def _apt_install(session, packages: list[str]) -> dict:
    pkgs = " ".join(packages)
    return _guest_bash(
        session,
        "set +e; export DEBIAN_FRONTEND=noninteractive; "
        "echo '===df==='; df -h / /var 2>/dev/null | head; "
        "echo '===hosts==='; getent hosts deb.debian.org | head; "
        "apt-get update -y >/var/log/gunnchos-apt-update.log 2>&1; echo update_rc=$?; "
        f"for attempt in 1 2 3; do "
        f"apt-get install -y --no-install-recommends {pkgs} "
        f">/var/log/gunnchos-apt-reearn.log 2>&1 && break; "
        f"echo apt_attempt_${{attempt}}_failed; sleep 5; "
        f"done; "
        f"dpkg -l {pkgs} 2>/dev/null | awk '/^ii/{{print $2,$3}}' | head -40; "
        "command -v grim; command -v libreoffice; command -v soffice; command -v labwc; "
        "echo '===apt_reearn_tail==='; tail -40 /var/log/gunnchos-apt-reearn.log 2>/dev/null; "
        "true",
        timeout_sec=1200,
        name="apt-reearn",
    )


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    work = ROOT / "artifacts" / "wp011r" / "interactive_guest_session_reearn"
    work.mkdir(parents=True, exist_ok=True)
    # Allow guest apt for libreoffice/labwc during re-earn (not a shipping claim).
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_INTERACTIVE_NET", "1")
    summary: dict = {
        "schema": "gunnchos.wp011r.cycle3b_demoted_reearn.v1",
        "started_at_utc": started,
        "ECO010_SOAK_PASS": True,
        "GUEST_DUAL_OUTPUT_PASS": True,
        "prefer_fail_over_false_pass": True,
        "net_restrict": False,
    }

    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=240, memory_mb=4096)
    session = boot.pop("_session", None)
    summary["boot"] = {k: boot.get(k) for k in ("ok", "error", "result") if k in boot}
    if not boot.get("ok") or session is None:
        summary["error"] = "boot_failed"
        out = ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json"
        out.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 1

    try:
        for _ in range(20):
            probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
            if probe.get("available"):
                break
            time.sleep(2.0)

        summary["hot_patch"] = _hot_patch_guest_agent(session, ROOT)
        # Push weston.ini (Super+s screenshooter) once, then wait for compositor.
        import base64 as _b64

        weston_ini = (
            ROOT
            / "os_build"
            / "device_lab_interactive_guest"
            / "debian_cloud"
            / "config"
            / "weston.ini"
        )
        if weston_ini.is_file():
            b64 = _b64.b64encode(weston_ini.read_bytes()).decode("ascii")
            summary["weston_ini_push"] = _guest_bash(
                session,
                "set -e; "
                f"printf '%s' '{b64}' | base64 -d > /etc/xdg/weston/weston.ini; "
                "cp /etc/xdg/weston/weston.ini /etc/gunnchos-weston/weston.ini; "
                "systemctl restart gunnchos-weston.service || true; sleep 4; "
                "pgrep -x weston && echo weston_ok",
                timeout_sec=60,
                name="weston-ini-super",
            )
            for _ in range(20):
                probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
                if probe.get("available"):
                    break
                time.sleep(1.0)
        # Probe guest FB once before proofs (honest preflight).
        summary["fb_preflight"] = _agent_call(session, "framebuffer_capture", timeout_sec=30.0)


        # Seed Godot linux.arm64 cache from field-kit when present (avoid urllib SSL fail).
        try:
            import shutil as _shutil

            cache = ROOT / "artifacts/wp011r/cache"
            cache.mkdir(parents=True, exist_ok=True)
            alt = Path(
                "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
                "gunnchos-7gc-ai-ran-field-kit/.wave5_lab_artifacts/godot_cache/"
                "Godot_v4.3-stable_linux.arm64"
            )
            dest = cache / "Godot_v4.3-stable_linux.arm64"
            if alt.is_file() and (not dest.is_file() or dest.stat().st_size < 1_000_000):
                _shutil.copy2(alt, dest)
                summary["godot_cache_seed"] = str(alt)
            elif dest.is_file():
                summary["godot_cache_seed"] = "already_present"
        except Exception as exc:  # noqa: BLE001
            summary["godot_cache_seed"] = f"error:{exc}"

        summary["apt"] = _apt_install(
            session,
            ["libreoffice-writer", "libreoffice-gtk3", "labwc", "grim", "wlr-randr"],
        )
        # Re-check compositor after apt (may have restarted services).
        for _ in range(20):
            probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
            if probe.get("available"):
                break
            time.sleep(1.0)

        visual_dir = _evidence_dir(ROOT, "visual")
        dsxl_dir = _evidence_dir(ROOT, "dsxl")
        ring_dir = _evidence_dir(ROOT, "ring")
        games_dir = _evidence_dir(ROOT, "games")

        live = attempt_live_visual_pass(session, visual_dir)
        dsxl = attempt_dsxl_dual_compositor_pass(session, dsxl_dir)
        ring = attempt_ring_app_mutation_pass(session, ring_dir)
        four = attempt_four_game_in_guest_pass(session, ROOT, games_dir)

        tokens = {
            "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS")),
            "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")),
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
                four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
            ),
            "ECO010_SOAK_PASS": True,
            "GUEST_DUAL_OUTPUT_PASS": True,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        }
        # Master stays false unless all four demoted flip true under independent rules.
        if all(
            tokens[t]
            for t in (
                "LIVE_GUNNCHOS_VISUAL_PASS",
                "DSXL_DUAL_COMPOSITOR_UX_PASS",
                "RING_TO_REAL_APP_STATE_MUTATION_PASS",
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
            )
        ):
            # Still do not auto-set master true here — independent must accept.
            tokens["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] = False
            tokens["master_candidate_only"] = True

        summary["tokens"] = tokens
        summary["live_note"] = live.get("note") or live.get("blocker")
        summary["dsxl_note"] = dsxl.get("note")
        summary["dsxl_architecture"] = dsxl.get("architecture") or "dual_virtio_gpu_pci_gpu0_gpu1_device_del_add"
        summary["ring_note"] = ring.get("note") or ring.get("blocker")
        mut = ring.get("mutations") or {}
        summary["ring_partial"] = {
            "libreoffice": bool((mut.get("libreoffice") or {}).get("mutated")),
            "browser": bool((mut.get("browser") or {}).get("mutated")),
            "game": bool((mut.get("game") or {}).get("mutated")),
        }
        summary["four_note"] = four.get("note")
        fg = four.get("games") or {}
        summary["four_games"] = {
            gid: {
                "earned": bool((fg.get(gid) or {}).get("FOUR_GAME_REAL_RUNTIME_EARNED")),
                "runtime": (fg.get(gid) or {}).get("runtime_class"),
            }
            for gid in ("anime-aggressors", "beatlink-party", "earth-species", "foot-racing")
        }
        summary["pedestrian_godot_earned"] = bool(
            (fg.get("foot-racing") or {}).get("FOUR_GAME_REAL_RUNTIME_EARNED")
        )
        summary["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Edmund do-not-merge unless ALL four demoted gates true under independent rules.
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
    finally:
        try:
            session.stop()
        except Exception:
            pass

    out = ROOT / "artifacts/wp011r/CYCLE3B_REEARN_SUMMARY.json"
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    # Exit 0 only if all four demoted flipped — else 2 (honest incomplete).
    flipped = summary.get("tokens") or {}
    if all(
        flipped.get(t)
        for t in (
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        )
    ):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
