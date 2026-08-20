#!/usr/bin/env python3
"""Pixel 6a client probe — evidence only, does not gate digital validation."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    out = ROOT / "artifacts/engineering_wave004/PIXEL_CLIENT_PROBE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    probe = {
        "schema": "gunnchos.engineering_wave004.pixel_client_probe.v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "client_evidence_only": True,
        "blocks_digital_validation": False,
        "adb_devices_l": "",
        "device_detected": False,
        "model": None,
    }
    try:
        raw = subprocess.check_output(["adb", "devices", "-l"], text=True, stderr=subprocess.STDOUT)
        probe["adb_devices_l"] = raw.strip()
        probe["device_detected"] = "bluejay" in raw or "Pixel" in raw
        if "model:" in raw:
            for part in raw.split():
                if part.startswith("model:"):
                    probe["model"] = part.split(":", 1)[1]
    except Exception as exc:  # noqa: BLE001
        probe["error"] = str(exc)
    out.write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(out), "device_detected": probe["device_detected"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
