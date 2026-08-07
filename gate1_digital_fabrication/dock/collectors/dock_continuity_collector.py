#!/usr/bin/env python3.11
"""Dock continuity collector — simulation / fixture automation (nonphysical)."""
from __future__ import annotations
import json, datetime, argparse
from pathlib import Path

LINES = ["USB2_D+", "USB2_D-", "CC1", "CC2", "VBUS_SENSE", "GND", "HPD", "HDMI_5V"]

def simulate() -> dict:
    return {
        "collected_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_class": "SOFTWARE_SIMULATED",
        "lines": {n: {"continuity_ohm": 0.2, "pass": True} for n in LINES},
        "physical_dock_claimed": False,
        "tokens": ["DOCK_CONTINUITY_SIMULATION_PASS", "PHYSICAL_DOCK_EVIDENCE_PENDING"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("gate1_digital_fabrication/dock/collectors/last_continuity.json"))
    a = ap.parse_args()
    doc = simulate()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=2)+"\n")
    print(json.dumps({"ok": True, "physical_dock_claimed": False, "lines": len(doc["lines"])}))

if __name__ == "__main__":
    main()
