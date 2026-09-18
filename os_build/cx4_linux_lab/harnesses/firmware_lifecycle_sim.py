#!/usr/bin/env python3
"""Simulated firmware lifecycle harness — never sets physical/firmware PASS."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    fixture = {"device": "sim-fw-001", "version": "1.0.0", "signed": True}
    upgraded = {**fixture, "version": "1.0.1"}
    rolled = {**fixture, "version": "1.0.0", "rolled_back": True}
    payload = {
        "schema": "gunnchos.cx4.firmware_lifecycle_sim.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": [fixture],
        "upgrade": upgraded,
        "rollback": rolled,
        "failed_update_recovery": {"ok": True, "simulated": True},
        "signed_image_verification": {
            "ok": True,
            "simulated": True,
            "sha256": hashlib.sha256(b"sim-image").hexdigest(),
        },
        "physical_pass": False,
        "note": "simulation only",
    }
    (out / "FIRMWARE_LIFECYCLE_SIM.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/complete_experience/cx4_0/firmware")
    print(json.dumps(run(target), indent=2))
