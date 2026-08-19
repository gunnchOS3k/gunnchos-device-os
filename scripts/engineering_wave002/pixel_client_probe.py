#!/usr/bin/env python3
"""Pixel client-path probe — adb authorized devices only; no fake full OS image."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def probe_pixel() -> dict:
    try:
        proc = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "provenance": "UNAVAILABLE",
            "error": "adb_missing",
            "PHYSICAL_VALIDATION": False,
        }
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip() and "List of devices" not in ln]
    authorized = [ln for ln in lines if " device " in f" {ln} " or ln.endswith(" device")]
    if not authorized:
        return {
            "ok": False,
            "provenance": "UNAVAILABLE",
            "devices": lines,
            "note": "No authorized adb device; client paths not exercised",
            "PHYSICAL_VALIDATION": False,
        }
    serial = authorized[0].split()[0]
    props = {}
    for prop in ("ro.product.model", "ro.build.version.release"):
        p = subprocess.run(
            ["adb", "-s", serial, "shell", "getprop", prop],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        props[prop] = (p.stdout or "").strip()
    return {
        "ok": True,
        "provenance": "TARGET_DEVICE_OBSERVED",
        "serial": serial,
        "props": props,
        "scope": "client_paths_only",
        "full_os_image": False,
        "PHYSICAL_VALIDATION": False,
        "HUMAN_E6": False,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out = root / "artifacts/engineering_wave002/PIXEL_CLIENT_PROBE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    result = probe_pixel()
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
