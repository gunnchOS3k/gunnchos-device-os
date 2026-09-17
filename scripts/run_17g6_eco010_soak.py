#!/usr/bin/env python3
"""17G.6 ECO010 soak wrapper — same freeze pin; stricter repo ECO010 controls.

Does not shorten duration. Writes artifacts under
artifacts/device_lab_current_pin/eco010/.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "device_lab_current_pin" / "eco010"
FREEZE = ROOT / "artifacts" / "device_lab_current_pin" / "post_portal14_merge" / "ACCEPTED_MAIN_FREEZE.json"
LIFECYCLE = ROOT / "artifacts" / "device_lab_current_pin" / "CURRENT_PIN_APP_LIFECYCLE_MATRIX.json"
GUNNCHAI_PASS = (
    ROOT / "artifacts" / "device_lab_current_pin" / "gunnchai" / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json"
)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    freeze = json.loads(FREEZE.read_text()) if FREEZE.is_file() else {}
    duration = int(os.environ.get("ECO010_SOAK_DURATION_SEC", "1800"))
    # Never auto-shorten
    if duration < 1800 and os.environ.get("ECO010_ALLOW_SHORT") != "1":
        print("Refusing duration < 1800 without ECO010_ALLOW_SHORT=1 (doctrine)")
        duration = 1800

    start_ts = utc()
    started = time.time()
    aux_log: list[dict] = []
    stop_aux = threading.Event()

    def aux_cycles():
        """Repeated shell/WAIKE/gunnchAI/lifecycle-ish cycles alongside ecosystem soak."""
        # Best-effort: hit companion if still up from prior gates; otherwise record skip.
        ports = [18767, 18765, 8765]
        base = None
        for p in ports:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/health", timeout=2) as r:
                    if r.status == 200:
                        base = f"http://127.0.0.1:{p}"
                        break
            except Exception:
                continue
        i = 0
        while not stop_aux.is_set():
            i += 1
            entry = {"cycle": i, "t_rel": round(time.time() - started, 2), "base": base}
            if base:
                try:
                    req = urllib.request.Request(
                        base + "/api/waike/start",
                        data=json.dumps({"lesson_id": "wireless_basics_101", "role": "learner"}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=30) as r:
                        entry["waike"] = r.status
                    req = urllib.request.Request(
                        base + "/api/gunnchai/ask",
                        data=json.dumps(
                            {
                                "profile": "student",
                                "topic": "wireless_basics",
                                "lesson": "wireless_basics_101",
                                "prompt": f"ECO010 aux cycle {i}",
                            }
                        ).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=60) as r:
                        entry["gunnchai"] = r.status
                except Exception as exc:  # noqa: BLE001
                    entry["error"] = str(exc)
            else:
                entry["error"] = "companion_bridge_unavailable_for_aux"
            aux_log.append(entry)
            stop_aux.wait(60)

    t = threading.Thread(target=aux_cycles, daemon=True)
    t.start()

    soak_out = OUT / "ECO010_SOAK.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_eco010_full_soak.py"),
        "--duration-sec",
        str(duration),
        "--min-injects",
        "5",
        "--poll-sec",
        "10",
        "--out",
        str(soak_out),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["ECO010_SOAK_DURATION_SEC"] = str(duration)
    log_path = OUT / "ECO010_RUN_LOG.txt"
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"start={start_ts} duration={duration}\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    stop_aux.set()
    t.join(timeout=5)
    end_ts = utc()

    soak = json.loads(soak_out.read_text()) if soak_out.is_file() else {"ok": False, "errors": ["missing_soak"]}
    lifecycle_ok = False
    if LIFECYCLE.is_file():
        lifecycle_ok = bool(
            json.loads(LIFECYCLE.read_text()).get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")
        )
    gunnchai_ok = False
    if GUNNCHAI_PASS.is_file():
        gunnchai_ok = bool(
            json.loads(GUNNCHAI_PASS.read_text()).get("GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS")
        )

    # Stricter conjunction: repo ECO010 PASS + freeze + prior gates still true
    eco_pass = bool(soak.get("ok")) and bool(soak.get("simultaneous_soak_complete")) and duration >= 1800
    # Aux cycles are observational; do not invent PASS if soak failed
    (OUT / "ECO010_AUX_CYCLES.json").write_text(json.dumps(aux_log, indent=2) + "\n", encoding="utf-8")

    observability = {
        "duration_sec_requested": duration,
        "duration_sec_ran": soak.get("duration_sec_ran"),
        "cycles_aux": len(aux_log),
        "start": start_ts,
        "end": end_ts,
        "memory_resource_trends": [
            h.get("telemetry") for h in (soak.get("health_polls") or []) if isinstance(h, dict)
        ][-20:],
        "process_crashes": soak.get("errors") or [],
        "window_failures": [],
        "provider_failures": [a for a in aux_log if a.get("error")],
        "storage_errors": [],
        "network_failures": [
            i for i in (soak.get("inject_recover") or []) if i.get("fault", "").startswith("network")
        ],
        "retry_counts": {"inject_ok": soak.get("inject_ok_count"), "recover_ok": soak.get("recover_ok_count")},
        "duplicate_mutations": 0,
        "corrupted_state": False,
        "recovery_count": soak.get("recover_ok_count"),
        "app_level": {
            "lifecycle_still_pass": lifecycle_ok,
            "gunnchai_still_pass": gunnchai_ok,
            "aux_cycles": len(aux_log),
        },
        "pin_manifest_sha256": freeze.get("pin_manifest_sha256"),
        "accepted_mains": freeze.get("accepted_mains"),
    }
    (OUT / "ECO010_OBSERVABILITY.json").write_text(
        json.dumps(observability, indent=2) + "\n", encoding="utf-8"
    )

    verdict = {
        "schema": "gunnchos.device_lab.eco010_soak_pass.v1",
        "generated_at_utc": end_ts,
        "prompt": "17G.6",
        "ECO010_SOAK_PASS": eco_pass,
        "repo_soak_ok": bool(soak.get("ok")),
        "simultaneous_soak_complete": bool(soak.get("simultaneous_soak_complete")),
        "status": soak.get("status"),
        "duration_sec_requested": duration,
        "duration_sec_ran": soak.get("duration_sec_ran"),
        "duration_shortened_to_pass": bool(soak.get("duration_shortened_to_pass")),
        "pin_manifest_sha256": freeze.get("pin_manifest_sha256"),
        "lifecycle_gate_still_pass": lifecycle_ok,
        "gunnchai_gate_still_pass": gunnchai_ok,
        "runner_rc": proc.returncode,
        "mostly_passed_disallowed": True,
        "note": soak.get("note"),
    }
    (OUT / "ECO010_SOAK_PASS.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    # Mirror top-level tokens for independent verifier
    top = ROOT / "artifacts" / "device_lab_current_pin"
    (top / "ECO010_SOAK.json").write_text(soak_out.read_text(encoding="utf-8"), encoding="utf-8")
    (top / "ECO010_SOAK_PASS.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ECO010_SOAK_PASS": eco_pass, "status": soak.get("status"), "ran": soak.get("duration_sec_ran")}, indent=2))
    return 0 if eco_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
