#!/usr/bin/env python3
"""Run STREAM-A-PKT-003 reliability + continuity + creation depth."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from gunnchos_device_os.a_pkt003.runner import run_packet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-guest", action="store_true")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    status = run_packet(root, skip_guest=bool(args.skip_guest))
    print(
        json.dumps(
            {
                "merge_ready": status.get("merge_ready"),
                "tokens": status.get("tokens"),
                "OPEN": status.get("OPEN"),
                "tip_sha": status.get("tip_sha"),
                "duration_ms": status.get("duration_ms"),
            },
            indent=2,
        )
    )
    return 0 if status.get("merge_ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
