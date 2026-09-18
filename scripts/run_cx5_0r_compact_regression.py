#!/usr/bin/env python3
"""CX5.0R post-soak compact regression — retain earned tokens unless artifacts fail-closed."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "artifacts" / "device_lab_current_pin"
CX5 = ROOT / "artifacts" / "complete_experience" / "cx5_0" / "release_regression"
OUT = CX5 / "compact_integrity"


def load(p: Path) -> dict:
    if not p.is_file():
        return {}
    return json.loads(p.read_text())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    # Re-run lifecycle on exact head (authoritative CX5 path)
    env = {"PYTHONPATH": str(ROOT)}
    import os
    e = os.environ.copy()
    e["PYTHONPATH"] = str(ROOT) + os.pathsep + e.get("PYTHONPATH", "")
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_17g6_lifecycle_matrix.py")], cwd=str(ROOT), env=e).returncode
    # Restore accepted-main device_lab lifecycle after harness write
    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "checkout",
            "--",
            "artifacts/device_lab_current_pin/CURRENT_PIN_APP_LIFECYCLE_MATRIX.json",
            "artifacts/device_lab_current_pin/CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json",
            "artifacts/device_lab_current_pin/LIFECYCLE_MATRIX.json",
            "artifacts/device_lab_current_pin/LIFECYCLE_RUN_LOG.txt",
        ],
        check=False,
    )
    life = load(CX5 / "lifecycle" / "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json")
    tokens = {
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(load(PIN / "LIVE_GUNNCHOS_VISUAL_PASS.json").get("LIVE_GUNNCHOS_VISUAL_PASS")),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(load(PIN / "DSXL_DUAL_COMPOSITOR_UX_PASS.json").get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(load(PIN / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json").get("RING_TO_REAL_APP_STATE_MUTATION_PASS")),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(load(PIN / "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.json").get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")),
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": bool(load(PIN / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json").get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS")),
        "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS": bool(
            (load(PIN / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json") or load(PIN / "gunnchai" / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json")).get(
                "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS"
            )
        ),
        "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": bool(life.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")),
    }
    eco = load(CX5 / "eco010" / "ECO010_SOAK_PASS.json")
    tokens["ECO010_SOAK_PASS"] = bool(eco.get("ECO010_SOAK_PASS"))
    ok = all(tokens.values()) and rc == 0
    report = {
        "schema": "CX5_0R_COMPACT_INTEGRITY/v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exact_integration_head": tip,
        "lifecycle_runner_rc": rc,
        "tokens": tokens,
        "COMPACT_INTEGRITY_PASS": ok,
    }
    (OUT / "CX5_0R_COMPACT_INTEGRITY.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
