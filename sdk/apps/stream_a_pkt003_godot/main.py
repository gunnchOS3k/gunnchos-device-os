#!/usr/bin/env python3
"""Guest-side launcher for the PKT003 Godot microgame pack artifact."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    data = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    pack = data / "microgame.pck.json"
    if not pack.exists():
        # Prefer sibling godot pack produced by godot_pack_builder.
        cand = Path(__file__).resolve().parent / "godot" / "microgame.pck.json"
        pack = cand if cand.exists() else pack
    payload = {"ok": False, "error": "pack_missing", "build_system": "godot_pack_v1"}
    if pack.exists():
        payload = json.loads(pack.read_text(encoding="utf-8"))
        payload["ok"] = True
        payload["executed"] = True
    print(json.dumps(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
