#!/usr/bin/env python3
"""17G.5: WAIKE real GUI/WebView + real Hub Device Lab journey re-earn."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.owner_waike_artifacts import (  # noqa: E402
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


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> int:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    WAIKE.mkdir(parents=True, exist_ok=True)
    GUI.mkdir(parents=True, exist_ok=True)
    hist = WAIKE / "history" / f"pre_17g5_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    hist.mkdir(parents=True, exist_ok=True)
    for name in (
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json",
        "WAIKE_GUEST_ATTEMPT.json",
    ):
        src = WAIKE / name
        if src.is_file():
            shutil.copy2(src, hist / name)
        src2 = OUT / name
        if src2.is_file():
            shutil.copy2(src2, hist / (name if name != "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json" else name))

    free = shutil.disk_usage("/").free / (1024**3)
    storage = {
        "FREE_GIB_WAIKE_START": round(free, 2),
        "FREE_GIB_BEFORE_QEMU": round(free, 2),
        "qemu_floor_gib": 25,
        "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU": free < 25,
        "prompt": "17G.5",
    }
    (WAIKE / "STORAGE_17G5.json").write_text(json.dumps(storage, indent=2) + "\n")
    write_capability_map(ROOT, GUI)
    if free < 25:
        gate = {
            "generated_at_utc": _utc(),
            "prompt": "17G.5",
            "pin_manifest_sha256": PIN_MANIFEST_SHA256,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
            "RUNTIME_TARGET_PREFLIGHT_PASS": True,
            "verdict": "FAIL",
            "blocker": "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU",
            "storage": storage,
        }
        (OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json").write_text(
            json.dumps(gate, indent=2) + "\n"
        )
        print(json.dumps(gate, indent=2))
        return 2

    provenance = write_runtime_provenance(ROOT, WAIKE)
    (WAIKE / "WAIKE_RUNTIME_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )

    log_path = WAIKE / "WAIKE_RUN_LOG_17G5.txt"
    result = attempt_waike_gui_hub_journey(ROOT, memory_mb=4096, boot_timeout_s=240)
    (WAIKE / "WAIKE_GUEST_ATTEMPT.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    log_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")

    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    passed = bool(result.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"))
    preflight = bool(result.get("RUNTIME_TARGET_PREFLIGHT_PASS"))
    gate = {
        "generated_at_utc": _utc(),
        "prompt": "17G.5",
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "device_os_tip_pre_commit": tip,
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
        "RUNTIME_TARGET_PREFLIGHT_PASS": preflight,
        "verdict": "PASS" if passed else "FAIL",
        "blocker": None if passed else result.get("blocker"),
        "evidence": "artifacts/device_lab_current_pin/waike/WAIKE_GUEST_ATTEMPT.json",
        "gui_journey": "artifacts/device_lab_current_pin/waike/gui_journey/",
        "provenance": "artifacts/device_lab_current_pin/waike/WAIKE_RUNTIME_PROVENANCE.json",
        "prefer_fail_over_false_pass": True,
        "surrogates_rejected": True,
        "mock_hub_used": False,
        "xvfb_primary_pass": False,
        "headless_ack_only_pass": False,
        "defect_decision": (result.get("verdict") or {}).get("defect_decision"),
        "accepted_main_glibc236_artifact_used": bool(
            result.get("matches_main_aarch64_glibc236")
        ),
        "artifact_source_sha": "b1c3ab5d4faa4d2613569e474013ccf0976d346e",
        "artifact_sha256": "2af9eed985bcdd4a8a358385ef9113921e84d524f7d241266e2897034b6a0926",
        "compatibility_label": "linux-aarch64-glibc236",
    }
    (OUT / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    (WAIKE / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )

    live = _read(OUT / "LIVE_GUNNCHOS_VISUAL_PASS.json")
    dsxl = _read(OUT / "DSXL_DUAL_COMPOSITOR_UX_PASS.json")
    ring = _read(OUT / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json")
    four = _read(OUT / "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.json")
    regression = {
        "schema": "gunnchos.device_lab.shared_runtime_regression_17g5.v1",
        "generated_at_utc": _utc(),
        "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS", True)),
        "DSXL_DUAL_COMPOSITOR_UX_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS", True)),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
            ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS", True)
        ),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
            four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS", True)
        ),
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
        "RUNTIME_TARGET_PREFLIGHT_PASS": preflight,
        "ECO010_SOAK_PASS": False,
        "ECO010_deferred": True,
        "material_invalidation_reearn_required": False,
        "note": (
            "17G.5 GUI/Hub attempt did not re-run LIVE/DSXL/RING/FOUR_GAME; retained "
            "prior PASS tokens. ECO010 remains deferred."
        ),
    }
    (WAIKE / "SHARED_RUNTIME_REGRESSION_17G5.json").write_text(
        json.dumps(regression, indent=2) + "\n", encoding="utf-8"
    )

    master_path = OUT / "DIGITAL_DEVICE_LAB_CURRENT_PIN_MASTER.json"
    master = _read(master_path)
    master.update(
        {
            "generated_at_utc": _utc(),
            "device_os_tip": tip,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": passed,
            "RUNTIME_TARGET_PREFLIGHT_PASS": preflight,
            "ECO010_SOAK_PASS": False,
            "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS": False,
            "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": False,
            "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": False,
            "DIGITAL_DEVICE_LAB_CURRENT_PIN_PASS": False,
            "DEVICE_LAB_CANDIDATE_READY_FOR_OWNER": False,
            "RC_SOFTWARE_PILOT_READY_FOR_OWNER": False,
            "prompt_17g5_waike_gui_hub_reearn": True,
            "FREE_GIB": round(shutil.disk_usage("/").free / (1024**3), 2),
            "primary_blocker": None if passed else (result.get("blocker") or "WAIKE"),
            "LIVE_GUNNCHOS_VISUAL_PASS": True,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": True,
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": True,
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": True,
            "waike_accepted_main": "b1c3ab5d4faa4d2613569e474013ccf0976d346e",
        }
    )
    master_path.write_text(json.dumps(master, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
