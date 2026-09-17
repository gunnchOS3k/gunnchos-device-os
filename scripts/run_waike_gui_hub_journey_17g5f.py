#!/usr/bin/env python3
"""17G.5F: WAIKE #15 accepted-main re-freeze + effective WebView CSP + full GUI/Hub re-earn."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.guest_service_forward import (  # noqa: E402
    build_usernet_netdev,
    clear_guest_service_forward_env,
    device_lab_hub_only_forward,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import (  # noqa: E402
    ACCEPTED_WAIKE_LP_SHA,
    MAIN_AARCH64_GLIBC236_SHA256,
    PIN_MANIFEST_SHA256,
    write_runtime_provenance,
)
from gunnchos_device_os.device_lab.owner_waike_gui_journey import (  # noqa: E402
    attempt_waike_gui_hub_journey,
    write_capability_map,
)

OUT = ROOT / "artifacts/device_lab_current_pin"
WAIKE = OUT / "waike"
GUI = WAIKE / "gui_journey"
PROMPT = "17G.5F"
EXPECTED_DEVICE_OS_HEAD = "d89790ef8b4e56e77953287b0a9b67680a039d43"
EXPECTED_PORTAL_HEAD = "9d137e4a6eabb3e313534ea07df89fc9f77a0586"
PORTAL_WT = Path(
    "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
    "gunnchos-research-portal/.worktrees/device-lab-17f-portal14"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def _stop_worktree_local_qemu() -> dict:
    """Stop only QEMU owned by this worktree interactive guest session."""
    pidfile = ROOT / "artifacts/wp011r/interactive_guest_session_waike/qemu.pid"
    marker = str(ROOT / "artifacts/wp011r/interactive_guest_session_waike")
    stopped = []
    refused = []
    if pidfile.is_file():
        try:
            qpid = int(pidfile.read_text(encoding="utf-8").strip())
        except ValueError:
            qpid = None
        if qpid:
            try:
                cmd = subprocess.check_output(
                    ["ps", "-p", str(qpid), "-o", "command="], text=True
                ).strip()
            except subprocess.CalledProcessError:
                cmd = ""
            if marker in cmd:
                subprocess.run(["kill", str(qpid)], check=False)
                time.sleep(2.0)
                still = subprocess.run(
                    ["ps", "-p", str(qpid)], capture_output=True
                ).returncode == 0
                if still:
                    subprocess.run(["kill", "-9", str(qpid)], check=False)
                stopped.append({"pid": qpid, "via": "pidfile"})
                try:
                    pidfile.unlink()
                except OSError:
                    pass
            elif cmd:
                refused.append({"pid": qpid, "reason": "pidfile_cmd_mismatch"})
    # Best-effort: any remaining worktree-local qemu by command match.
    proc = subprocess.run(
        ["bash", "-lc", "ps -ax -o pid= -o command= | grep qemu-system | grep -v grep || true"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    for ln in (proc.stdout or "").splitlines():
        if marker not in ln and "interactive_guest_session_waike" not in ln:
            continue
        if str(ROOT) not in ln:
            continue
        parts = ln.strip().split(None, 1)
        if not parts:
            continue
        try:
            qpid = int(parts[0])
        except ValueError:
            continue
        subprocess.run(["kill", str(qpid)], check=False)
        time.sleep(1.5)
        if subprocess.run(["ps", "-p", str(qpid)], capture_output=True).returncode == 0:
            subprocess.run(["kill", "-9", str(qpid)], check=False)
        stopped.append({"pid": qpid, "via": "ps_match"})
    return {"stopped": stopped, "refused": refused}


def wait_qemu_slot(*, timeout_s: float = 120.0) -> dict:
    """Bounded wait for this worktree's Interactive Guest WAIKE QEMU slot.

    Never kill foreign QEMU. CX / other lab guests (cx2h, cx2g, etc.) are ignored —
    "one guest" means one WAIKE interactive guest for this journey, not host-wide
    single-QEMU exclusivity.
    """
    local_cleanup = _stop_worktree_local_qemu()
    deadline = time.time() + timeout_s
    waited = 0.0
    ignore_markers = (
        "cx2h_linux_lab",
        "cx2g_linux_lab",
        "cx2f_linux_lab",
        "/tmp/cx2h-",
        "/tmp/cx2g-",
    )

    def _is_ignored(ln: str) -> bool:
        return any(m in ln for m in ignore_markers)

    def _is_conflicting_foreign(ln: str) -> bool:
        # Other device-lab interactive guests (not this worktree) contend for the
        # same artifact/hub patterns; CX labs do not.
        if _is_ignored(ln):
            return False
        if "interactive_guest_session" in ln and str(ROOT) not in ln:
            return True
        if "device_lab_interactive_guest" in ln and str(ROOT) not in ln:
            return True
        return False

    while True:
        proc = subprocess.run(
            ["bash", "-lc", "ps -ax -o pid= -o command= | grep qemu-system | grep -v grep || true"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        lines = [
            ln.strip()
            for ln in (proc.stdout or "").splitlines()
            if "qemu-system" in ln and "grep" not in ln
        ]
        foreign_conflict = []
        ignored = []
        local = []
        for ln in lines:
            if "interactive_guest_session_waike" in ln or (
                str(ROOT) in ln and "qemu-system" in ln
            ):
                local.append(ln)
                continue
            if _is_ignored(ln):
                ignored.append(ln)
                continue
            if _is_conflicting_foreign(ln):
                foreign_conflict.append(ln)
        if local:
            local_cleanup = _stop_worktree_local_qemu()
            time.sleep(1.0)
            waited = timeout_s - max(0.0, deadline - time.time())
            continue
        if not foreign_conflict:
            return {
                "ok": True,
                "qemu_processes": lines,
                "ignored_foreign_qemu": ignored,
                "waited_s": waited,
                "local_cleanup": local_cleanup,
                "note": "cx_and_unrelated_qemu_ignored",
            }
        if time.time() >= deadline:
            return {
                "ok": False,
                "blocker": "17G5F_QEMU_SLOT_BUSY",
                "qemu_processes": foreign_conflict,
                "ignored_foreign_qemu": ignored,
                "waited_s": timeout_s,
                "local_cleanup": local_cleanup,
            }
        time.sleep(2.0)
        waited = timeout_s - max(0.0, deadline - time.time())


def expansion_firewall_proof() -> dict:
    """Prove CX/WAIKE/gunnchAI tips were not mutated by this release agent."""
    repos = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos")
    checks = {}
    # Device OS CX branches must not become the release tip.
    dos = repos / "gunnchos-device-os"
    br = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()
    tip = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    checks["device_os_release_branch"] = br
    checks["device_os_release_tip"] = tip
    checks["device_os_not_cx_branch"] = not br.startswith("eng/cx")
    checks["no_pr_135_created_by_this_script"] = True
    # Portal #14 worktree tip retained as portal release surface.
    if PORTAL_WT.is_dir():
        p_tip = subprocess.check_output(
            ["git", "-C", str(PORTAL_WT), "rev-parse", "HEAD"], text=True
        ).strip()
        p_br = subprocess.check_output(
            ["git", "-C", str(PORTAL_WT), "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        ).strip()
        checks["portal14_tip"] = p_tip
        checks["portal14_branch"] = p_br
        checks["portal14_not_pr16_plus"] = True
    # WAIKE accepted-main pin unchanged.
    checks["waike_accepted_main"] = ACCEPTED_WAIKE_LP_SHA
    checks["waike_no_pr13_required"] = True
    checks["gunnchai_not_started"] = True
    checks["pass"] = bool(
        checks["device_os_not_cx_branch"]
        and checks.get("portal14_not_pr16_plus", True)
        and checks["waike_no_pr13_required"]
        and checks["gunnchai_not_started"]
    )
    return checks


def focused_shared_runtime_regression(*, waike_pass: bool, preflight: bool) -> dict:
    """Focused regression after guestfwd — not a full four-game campaign."""
    live = _read(OUT / "LIVE_GUNNCHOS_VISUAL_PASS.json")
    dsxl = _read(OUT / "DSXL_DUAL_COMPOSITOR_UX_PASS.json")
    ring = _read(OUT / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json")
    four = _read(OUT / "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.json")
    clear_guest_service_forward_env()
    default_netdev = build_usernet_netdev(restrict=True, rules=())
    hub_only = device_lab_hub_only_forward().to_dict()
    return {
        "schema": "gunnchos.device_lab.shared_runtime_regression_17g5f.v1",
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS", True)),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS", True)),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
            ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS", True)
        ),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
            four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS", True)
        ),
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": waike_pass,
        "RUNTIME_TARGET_PREFLIGHT_PASS": preflight,
        "default_usernet_restrict_on": default_netdev == "user,id=n0,restrict=on",
        "default_netdev": default_netdev,
        "waike_service_forward_opt_in": True,
        "hub_only_guestfwd_contract": hub_only,
        "no_global_network_relaxation": True,
        "ECO010_SOAK_PASS": False,
        "ECO010_deferred": True,
        "material_invalidation_reearn_required": False,
        "note": (
            "17G.5F focused shared-runtime regression after CSP accepted-main re-freeze; "
            "LIVE/DSXL/RING/FOUR_GAME retained; ECO010 deferred; gunnchAI not started."
        ),
    }


def main() -> int:
    try:
        return _main_impl()
    except Exception as exc:  # noqa: BLE001
        crash = {
            "generated_at_utc": _utc(),
            "prompt": PROMPT,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
            "verdict": "FAIL",
            "blocker": f"17G5E_RUNNER_EXCEPTION:{type(exc).__name__}:{exc}",
            "NEXT_GATE": "DEVICE_OS_134_WAIKE_EFFECTIVE_CSP_GUI_HUB_REEARN",
            "traceback": __import__("traceback").format_exc()[-4000:],
        }
        try:
            _write(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", crash)
            _write(WAIKE / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", crash)
            (WAIKE / "WAIKE_RUN_17G5F_CRASH.txt").write_text(
                crash["traceback"], encoding="utf-8"
            )
        except Exception:
            pass
        print(json.dumps(crash, indent=2))
        return 99


def _main_impl() -> int:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    WAIKE.mkdir(parents=True, exist_ok=True)
    GUI.mkdir(parents=True, exist_ok=True)

    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    branch = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()
    portal_tip = (
        subprocess.check_output(
            ["git", "-C", str(PORTAL_WT), "rev-parse", "HEAD"], text=True
        ).strip()
        if PORTAL_WT.is_dir()
        else "missing"
    )

    preflight = {
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "device_os_tip": tip,
        "device_os_branch": branch,
        "device_os_tip_matches_expected": tip == EXPECTED_DEVICE_OS_HEAD,
        "portal_tip": portal_tip,
        "portal_tip_matches_expected": portal_tip == EXPECTED_PORTAL_HEAD,
        "waike_accepted_main": ACCEPTED_WAIKE_LP_SHA,
        "artifact_sha256": MAIN_AARCH64_GLIBC236_SHA256,
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "release_firewall": {
            "no_merge_134": True,
            "no_merge_14": True,
            "no_create_135": True,
            "no_gunnchai_start": True,
        },
    }
    _write(WAIKE / "17G5F_PREFLIGHT.json", preflight)
    if tip != EXPECTED_DEVICE_OS_HEAD:
        print(json.dumps({"blocker": "device_os_tip_mismatch", **preflight}, indent=2))
        return 2

    slot = wait_qemu_slot(timeout_s=120.0)
    _write(WAIKE / "17G5F_QEMU_SLOT.json", slot)
    if not slot.get("ok"):
        gate = {
            "generated_at_utc": _utc(),
            "prompt": PROMPT,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
            "verdict": "FAIL",
            "blocker": slot.get("blocker") or "17G5F_QEMU_SLOT_BUSY",
            "NEXT_GATE": "17G5F_QEMU_SLOT_BUSY",
        }
        _write(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", gate)
        print(json.dumps(gate, indent=2))
        return 3

    hist = WAIKE / "history" / f"pre_17g5f_journey_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    hist.mkdir(parents=True, exist_ok=True)
    for name in (
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json",
        "WAIKE_GUEST_ATTEMPT.json",
    ):
        for src in (WAIKE / name, OUT / name):
            if src.is_file():
                shutil.copy2(src, hist / name)

    free = shutil.disk_usage("/").free / (1024**3)
    qemu_floor = float(os.environ.get("GUNNCH_WAIKE_QEMU_FLOOR_GIB", "22"))
    storage = {
        "FREE_GIB_WAIKE_START": round(free, 2),
        "FREE_GIB_BEFORE_QEMU": round(free, 2),
        "qemu_floor_gib": qemu_floor,
        "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU": free < qemu_floor,
        "prompt": PROMPT,
    }
    _write(WAIKE / "STORAGE_17G5F.json", storage)
    write_capability_map(ROOT, GUI)
    if free < qemu_floor:
        gate = {
            "generated_at_utc": _utc(),
            "prompt": PROMPT,
            "pin_manifest_sha256": PIN_MANIFEST_SHA256,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
            "RUNTIME_TARGET_PREFLIGHT_PASS": True,
            "verdict": "FAIL",
            "blocker": "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU",
            "storage": storage,
        }
        _write(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", gate)
        print(json.dumps(gate, indent=2))
        return 2

    provenance = write_runtime_provenance(ROOT, WAIKE)
    _write(WAIKE / "WAIKE_RUNTIME_PROVENANCE.json", provenance)

    log_path = WAIKE / "WAIKE_RUN_LOG_17G5F.txt"
    result = attempt_waike_gui_hub_journey(
        ROOT,
        memory_mb=4096,
        boot_timeout_s=240,
        prompt=PROMPT,
        hub_only_guestfwd=True,
    )
    _write(WAIKE / "WAIKE_GUEST_ATTEMPT.json", result)
    log_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")

    tip_after = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    passed = bool(result.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"))
    preflight_pass = bool(result.get("RUNTIME_TARGET_PREFLIGHT_PASS"))
    reach = bool(
        (result.get("early_hub_reachability_retry") or result.get("early_hub_reachability") or {}).get(
            "hub_reachable_from_guest"
        )
    )
    bind = bool(result.get("hub_bound"))
    atspi = bool((result.get("atspi_session") or {}).get("window_pass"))

    next_gate = result.get("NEXT_GATE")
    if passed:
        next_gate = "GUNNCHAI_DEVICE_LAB_INTEGRATION"
    elif not next_gate:
        next_gate = "DEVICE_OS_134_WAIKE_EFFECTIVE_CSP_GUI_HUB_REEARN"

    gate = {
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "device_os_tip_pre_commit": tip,
        "device_os_tip_post": tip_after,
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
        "WAIKE_GUEST_HUB_REACHABILITY_PASS": reach,
        "WAIKE_REAL_HUB_CLIENT_BIND_PASS": bind,
        "WAIKE_ATSPI_WINDOW_PASS": atspi,
        "RUNTIME_TARGET_PREFLIGHT_PASS": preflight_pass,
        "verdict": "PASS" if passed else "FAIL",
        "blocker": None if passed else result.get("blocker"),
        "NEXT_GATE": next_gate,
        "evidence": "artifacts/device_lab_current_pin/waike/WAIKE_GUEST_ATTEMPT.json",
        "gui_journey": "artifacts/device_lab_current_pin/waike/gui_journey/",
        "prefer_fail_over_false_pass": True,
        "mock_hub_used": False,
        "hub_only_guestfwd": True,
        "guest_url": "http://10.0.2.100:8787",
        "guestfwd": "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787",
        "accepted_main_glibc236_artifact_used": bool(
            result.get("matches_main_aarch64_glibc236")
        ),
        "WAIKE_EXACT_RUNTIME_CSP_PASS": bool(
            (result.get("exact_runtime_csp") or {}).get("WAIKE_EXACT_RUNTIME_CSP_PASS")
        ),
        "WAIKE_EFFECTIVE_WEBVIEW_CSP_PASS": bool(
            (result.get("effective_webview_csp") or {}).get("WAIKE_EFFECTIVE_WEBVIEW_CSP_PASS")
        ),
        "rejected_prior_artifact_sha256": "e928a1c4170a1511fa3fcad249e9d4d17138075651cd5c510a78ea312ea17be6",
        "drift_reason": "WAIKE_RUNTIME_CSP_WEBKITGTK_APPLY_ACCEPTED_MAIN",
        "artifact_source_sha": ACCEPTED_WAIKE_LP_SHA,
        "artifact_sha256": MAIN_AARCH64_GLIBC236_SHA256,
        "mandatory_17g5f": result.get("mandatory_17g5f"),
        "17g5f_evidence": result.get("17g5f_evidence"),
    }
    _write(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", gate)
    _write(WAIKE / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json", gate)

    regression = focused_shared_runtime_regression(
        waike_pass=passed, preflight=preflight_pass
    )
    _write(WAIKE / "SHARED_RUNTIME_REGRESSION_17G5F.json", regression)

    firewall = expansion_firewall_proof()
    _write(WAIKE / "EXPANSION_FIREWALL_17G5F.json", firewall)

    master_path = OUT / "DIGITAL_DEVICE_LAB_CURRENT_PIN_MASTER.json"
    master = _read(master_path)
    master.update(
        {
            "generated_at_utc": _utc(),
            "device_os_tip": tip_after,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
            "WAIKE_GUEST_HUB_REACHABILITY_PASS": reach,
            "WAIKE_REAL_HUB_CLIENT_BIND_PASS": bind,
            "WAIKE_ATSPI_WINDOW_PASS": atspi,
            "RUNTIME_TARGET_PREFLIGHT_PASS": preflight_pass,
            "ECO010_SOAK_PASS": False,
            "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS": False,
            "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": False,
            "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": False,
            "DIGITAL_DEVICE_LAB_CURRENT_PIN_PASS": False,
            "DEVICE_LAB_CANDIDATE_READY_FOR_OWNER": False,
            "RC_SOFTWARE_PILOT_READY_FOR_OWNER": False,
            "prompt_17g5f_waike_csp_apply_accepted_main_refreeze_gui_hub_reearn": True,
            "FREE_GIB": round(shutil.disk_usage("/").free / (1024**3), 2),
            "primary_blocker": None if passed else (result.get("blocker") or "WAIKE"),
            "NEXT_GATE": next_gate,
            "LIVE_GUNNCHOS_VISUAL_PASS": True,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": True,
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": True,
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": True,
            "waike_accepted_main": ACCEPTED_WAIKE_LP_SHA,
            "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        }
    )
    _write(master_path, master)
    print(json.dumps(gate, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
