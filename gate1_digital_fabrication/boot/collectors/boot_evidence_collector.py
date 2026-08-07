#!/usr/bin/env python3.11
"""Non-destructive boot evidence collector — software/host path only."""
from __future__ import annotations
import json, platform, hashlib, datetime, argparse
from pathlib import Path

def collect(manifest: Path) -> dict:
    raw = manifest.read_bytes() if manifest.exists() else b""
    return {
        "collected_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_class": "SOFTWARE_SIMULATED",
        "host": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
        "manifest_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "physical_boot_claimed": False,
        "tokens": ["GUNNCHOS_BOOT_SOFTWARE_PATH_PASS", "GUNNCHOS_PHYSICAL_BOOT_PENDING"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path("config/boot/sample_manifest.json"))
    ap.add_argument("--out", type=Path, default=Path("gate1_digital_fabrication/boot/collectors/last_collection.json"))
    a = ap.parse_args()
    doc = collect(a.manifest)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps({"ok": True, "out": str(a.out), "physical_boot_claimed": False}))

if __name__ == "__main__":
    main()
