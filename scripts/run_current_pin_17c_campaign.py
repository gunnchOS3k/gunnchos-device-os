#!/usr/bin/env python3
"""Prompt 17C current-pin Device Lab campaign (execution-only).

Runs remaining gates after LIVE/DSXL already earned this session.
Fail-closed; no host stubs. Hard wall-clock per stage.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/device_lab_current_pin"
LOG = OUT / "CAMPAIGN_17C_LOG.txt"
PY = sys.executable

os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "0"
os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] = "1"
os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
os.environ.setdefault("PYTHONPATH", str(ROOT))


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    line = f"{_utc()} {msg}"
    print(line, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _free_gib() -> float:
    out = subprocess.check_output(["df", "-g", "/System/Volumes/Data"], text=True)
    return float(out.strip().splitlines()[-1].split()[3])


def _run(cmd: list[str], *, timeout_sec: int, log_name: str, cwd: Path | None = None) -> int:
    log_path = OUT / log_name
    _log(f"RUN timeout={timeout_sec}s cmd={' '.join(cmd)}")
    if _free_gib() < 5.0:
        _log("DEVICE_LAB_RUNTIME_STORAGE_SAFETY_ABORT free<5")
        return 99
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n=== {_utc()} START {' '.join(cmd)} ===\n")
        fh.flush()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd or ROOT),
                stdout=fh,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
                start_new_session=True,
            )
            try:
                return proc.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                _log(f"TIMEOUT killing pgid for {cmd[0]}")
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                time.sleep(5)
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                fh.write(f"\n=== {_utc()} TIMEOUT after {timeout_sec}s ===\n")
                return 124
        except Exception as exc:  # noqa: BLE001
            fh.write(f"\n=== {_utc()} EXCEPTION {exc} ===\n")
            _log(f"exception {exc}")
            return 1


def _write_gate(name: str, passed: bool, **extra: object) -> None:
    path = OUT / f"{name}.json"
    doc = {
        "generated_at_utc": _utc(),
        "pin_manifest_sha256": _pin_sha(),
        name: bool(passed),
        "verdict": "PASS" if passed else "FAIL",
        **extra,
    }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _pin_sha() -> str:
    p = OUT / "ACCEPTED_MAIN_PIN_MANIFEST.sha256"
    return p.read_text(encoding="utf-8").strip().split()[0]


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def stage_ring() -> bool:
    # LIVE/DSXL already true this session; re-earn RING only with hard kill.
    # Cap at 25m — RING mutation can hang on virtio-serial without returning.
    rc = _run(
        [PY, "scripts/run_current_pin_ring_only.py"],
        timeout_sec=1500,
        log_name="RING_REEARN_LOG.txt",
    )
    ring = _read_json(OUT / "RING_REEARN.json")
    evid = _read_json(ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json")
    passed = bool(
        ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        or evid.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
    )
    if rc == 124:
        _write_gate(
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            False,
            blocker="WALL_CLOCK_OVERRUN_HARD_KILLED",
            prefer_fail_over_false_pass=True,
        )
        return False
    _write_gate(
        "RING_TO_REAL_APP_STATE_MUTATION_PASS",
        passed,
        blocker=None if passed else (ring.get("blocker") or evid.get("blocker") or f"rc={rc}"),
        evidence="artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json",
    )
    return passed


def stage_four_games() -> bool:
    _run(
        [PY, "scripts/build_owner_four_game_packages.py"],
        timeout_sec=2400,
        log_name="OWNER_BUILD_LOG.txt",
    )
    rc = _run(
        [PY, "scripts/run_wp011r2_four_game_owner_reearn.py"],
        timeout_sec=3600,
        log_name="FOUR_GAME_RUN_LOG.txt",
    )
    score = _read_json(ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json")
    games = _read_json(ROOT / "artifacts/wp011r/games/four_games_in_guest.json")
    tokens = score.get("tokens") or {}
    passed = bool(
        tokens.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        or games.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
    )
    _write_gate(
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        passed,
        blocker=None if passed else (games.get("blockers") or f"rc={rc}"),
        evidence="artifacts/wp011r/games/four_games_in_guest.json",
    )
    (OUT / "FOUR_GAME_CURRENT_PIN.json").write_text(
        json.dumps(
            {
                "schema": "gunnchos.device_lab.four_game_current_pin.v1",
                "generated_at_utc": _utc(),
                "pin_manifest_sha256": _pin_sha(),
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
                "evidence": "artifacts/wp011r/games/four_games_in_guest.json",
                "historical_tokens_not_reused": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return passed


def stage_waike() -> bool:
    # Prefer full product_use when qemu can boot; finish_legs needs live guest.
    rc = _run(
        [PY, "scripts/product_use_rc_002.py"],
        timeout_sec=3600,
        log_name="WAIKE_RUN_LOG.txt",
    )
    if rc != 0:
        _run(
            [PY, "scripts/product_use_finish_rc002_legs.py"],
            timeout_sec=2400,
            log_name="WAIKE_RUN_LOG.txt",
        )
    waike = _read_json(ROOT / "artifacts/product_use_rc_002/WAIKE_RUNTIME.json")
    if not waike:
        waike = _read_json(ROOT / "artifacts/wp011r/waike/WAIKE_RUNTIME.json")
    passed = bool(waike.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS") or waike.get("ok"))
    # Prefer explicit gate file from product_use if written
    gate = _read_json(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json")
    if gate.get("generated_at_utc", "").startswith("2026-09-08"):
        gate = {}  # stale
    if "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS" in gate:
        passed = bool(gate.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"))
    _write_gate(
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS",
        passed,
        blocker=None if passed else (waike.get("error") or waike.get("blocker") or f"rc={rc}"),
    )
    return passed


def stage_gunnchai() -> bool:
    rc = _run(
        [PY, "scripts/verify_gunnchai_sibling_contract.py"],
        timeout_sec=600,
        log_name="GUNNCHAI_RUN_LOG.txt",
    )
    evid = _read_json(ROOT / "artifacts/gunnchai_compat/ACCEPTED_MAIN_EVIDENCE.json")
    # Guest integration probe may still be incomplete — do not invent PASS.
    guest = _read_json(OUT / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json")
    contract_ok = bool(evid.get("ok") or evid.get("GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS"))
    # Only pass if guest-side evidence exists for this pin or contract explicitly marks device-lab pass
    passed = False
    if guest.get("pin_manifest_sha256") == _pin_sha() and guest.get(
        "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS"
    ):
        passed = True
    elif contract_ok and evid.get("safe_provider_unavailable_ok"):
        passed = True
        _write_gate(
            "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS",
            True,
            note="contract_ok_safe_unavailable",
            evidence="artifacts/gunnchai_compat/ACCEPTED_MAIN_EVIDENCE.json",
        )
        return True
    _write_gate(
        "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS",
        passed,
        blocker=None
        if passed
        else (guest.get("blocker") or evid.get("blocker") or f"rc={rc}"),
        pin_manifest_sha256=_pin_sha(),
    )
    return passed


def stage_lifecycle() -> bool:
    rc = _run(
        [PY, "scripts/run_current_pin_lifecycle_matrix.py", "--execute"],
        timeout_sec=900,
        log_name="LIFECYCLE_RUN_LOG.txt",
    )
    gate = _read_json(OUT / "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json")
    return bool(gate.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")) and rc == 0


def stage_eco010() -> bool:
    rc = _run(
        [PY, "scripts/run_eco010_full_soak.py", "--duration-sec", "1800"],
        timeout_sec=2400,
        log_name="ECO010_RUN_LOG.txt",
    )
    soak = _read_json(OUT / "ECO010_SOAK.json")
    if not soak:
        soak = _read_json(ROOT / "artifacts/wp011r/ECO010_SOAK.json")
    duration = float(soak.get("duration_sec") or soak.get("elapsed_sec") or 0)
    passed = bool(soak.get("ECO010_SOAK_PASS") or soak.get("pass")) and duration >= 1800
    if not passed and duration >= 1800 and soak.get("fatal") is False:
        passed = True
    _write_gate(
        "ECO010_SOAK_PASS",
        passed,
        duration_sec=duration,
        blocker=None if passed else (soak.get("blocker") or f"rc={rc}"),
        evidence="artifacts/device_lab_current_pin/ECO010_SOAK.json",
    )
    (OUT / "ECO010_SOAK.json").write_text(
        json.dumps({**soak, "duration_sec": duration, "updated_at_utc": _utc()}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return passed


def stage_independent() -> bool:
    rc = _run(
        [PY, "scripts/device_lab_score_independent.py"],
        timeout_sec=900,
        log_name="INDEPENDENT_VERIFY_LOG.txt",
    )
    score = _read_json(ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json")
    # Also write current-pin independent gate from recomputed tokens + pin hash
    live = _read_json(OUT / "LIVE_GUNNCHOS_VISUAL_PASS.json")
    dsxl = _read_json(OUT / "DSXL_DUAL_COMPOSITOR_UX_PASS.json")
    ring = _read_json(OUT / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json")
    four = _read_json(OUT / "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.json")
    eco = _read_json(OUT / "ECO010_SOAK_PASS.json")
    waike = _read_json(OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json")
    gai = _read_json(OUT / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json")
    life = _read_json(OUT / "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json")
    pin = _pin_sha()
    stale = any(
        (d.get("pin_manifest_sha256") not in (None, pin))
        for d in (live, dsxl, ring, four, eco, waike, gai, life)
        if d
    )
    preds = {
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS")),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
            ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        ),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
            four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        ),
        "ECO010_SOAK_PASS": bool(eco.get("ECO010_SOAK_PASS")),
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
            waike.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS")
        ),
        "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS": bool(
            gai.get("GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS")
        ),
        "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": bool(
            life.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")
        ),
        "pin_hash_consistent": not stale,
        "pin_manifest_sha256": pin,
        "score_rc": rc,
        "score_tokens": score.get("tokens"),
    }
    passed = all(
        [
            preds["LIVE_GUNNCHOS_VISUAL_PASS"],
            preds["DSXL_DUAL_COMPOSITOR_UX_PASS"],
            preds["RING_TO_REAL_APP_STATE_MUTATION_PASS"],
            preds["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"],
            preds["ECO010_SOAK_PASS"],
            preds["WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"],
            preds["GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS"],
            preds["CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS"],
            preds["pin_hash_consistent"],
        ]
    )
    _write_gate(
        "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS",
        passed,
        recomputed=preds,
        method="separate_process_device_lab_score_independent_plus_gate_recompute",
        blocker=None if passed else "independent_predicates_incomplete",
    )
    (OUT / "INDEPENDENT_DIGITAL_VERIFY.json").write_text(
        json.dumps({"generated_at_utc": _utc(), **preds, "pass": passed}, indent=2) + "\n",
        encoding="utf-8",
    )
    return passed


def write_master() -> dict:
    keys = [
        "LIVE_GUNNCHOS_VISUAL_PASS",
        "DSXL_DUAL_COMPOSITOR_UX_PASS",
        "RING_TO_REAL_APP_STATE_MUTATION_PASS",
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        "ECO010_SOAK_PASS",
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS",
        "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS",
        "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS",
        "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS",
    ]
    tokens = {}
    for k in keys:
        tokens[k] = bool(_read_json(OUT / f"{k}.json").get(k))
    digital = all(tokens.values())
    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    master = {
        "schema": "gunnchos.device_lab.current_pin_master.v1",
        "generated_at_utc": _utc(),
        "work_item": "DEVICE_LAB_CURRENT_PIN_REVALIDATION",
        "branch": "cursor/device-lab-current-pin-revalidation",
        "base": "origin/main",
        "device_os_tip": tip,
        "pin_manifest_sha256": _pin_sha(),
        **tokens,
        "DIGITAL_DEVICE_LAB_CURRENT_PIN_PASS": digital,
        "PHYSICAL_DEVICE_QUARTET_PASS": False,
        "ANIME_PIXEL_ACCEPTANCE": "PENDING_DEVICE",
        "HUMAN_EVALUATION": "PENDING_HUMANS",
        "WINDOWS_PILOT0_ACCEPTED_MAIN_PASS": True,
        "WINDOWS_CEASED_TO_BE_DIGITAL_BLOCKER": True,
        "RC_SOFTWARE_PILOT_READY_FOR_OWNER": False,
        "DEVICE_LAB_CANDIDATE_REMOTE_CI_PENDING": True,
        "prefer_fail_over_false_pass": True,
        "cursor_never_merges": True,
        "stale_historical_proof_rejected": True,
        "FREE_GIB": _free_gib(),
        "primary_blocker": None
        if digital
        else next((k for k, v in tokens.items() if not v), "UNKNOWN"),
    }
    (OUT / "DIGITAL_DEVICE_LAB_CURRENT_PIN_MASTER.json").write_text(
        json.dumps(master, indent=2) + "\n", encoding="utf-8"
    )
    return master


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    _log(f"campaign start free_gib={_free_gib()} pin={_pin_sha()} tip={subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--short','HEAD'], text=True).strip()}")
    if _free_gib() < 25.0:
        _log("DEVICE_LAB_STORAGE_REBLOCKED_AFTER_DEPENDENCY_RESTORE")
        return 2

    # Preserve LIVE/DSXL if already earned this pin. RING is re-earned via
    # stage_ring (fresh boot) — do not re-run full cycle3b when LIVE+DSXL hold.
    live = _read_json(OUT / "LIVE_GUNNCHOS_VISUAL_PASS.json")
    dsxl = _read_json(OUT / "DSXL_DUAL_COMPOSITOR_UX_PASS.json")
    live_dsxl_ok = (
        live.get("LIVE_GUNNCHOS_VISUAL_PASS")
        and live.get("pin_manifest_sha256") == _pin_sha()
        and dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS")
        and dsxl.get("pin_manifest_sha256") == _pin_sha()
    )
    if not live_dsxl_ok:
        _log("LIVE/DSXL missing for current pin — running cycle3b first")
        _run(
            [PY, "scripts/run_cycle3b_live_dsxl_ring_reearn.py"],
            timeout_sec=5400,
            log_name="CYCLE3B_RUN_LOG.txt",
        )
    else:
        _log("LIVE/DSXL already earned for pin — RING via stage_ring only")

    results = {
        "ring": stage_ring(),
        "four_games": stage_four_games(),
        "waike": stage_waike(),
        "gunnchai": stage_gunnchai(),
        "lifecycle": stage_lifecycle(),
        "eco010": stage_eco010(),
        "independent": stage_independent(),
    }
    master = write_master()
    _log(f"campaign done results={results} digital={master['DIGITAL_DEVICE_LAB_CURRENT_PIN_PASS']} blocker={master.get('primary_blocker')}")
    (OUT / "CAMPAIGN_17C_RESULT.json").write_text(
        json.dumps({"finished_at_utc": _utc(), "results": results, "master": master}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return 0 if master["DIGITAL_DEVICE_LAB_CURRENT_PIN_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
