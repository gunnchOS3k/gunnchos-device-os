"""Phase XII defect register helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_defects(root: Path, defects: list[dict[str, Any]]) -> dict[str, Any]:
    reg = {
        "schema": "gunnchos.phase_xii.defects.v1",
        "open": [d for d in defects if d.get("status", "open") == "open"],
        "fixed": [d for d in defects if d.get("status") == "fixed"],
        "all": defects,
        "counts": {
            "X0": sum(1 for d in defects if d.get("severity") == "X0" and d.get("status", "open") == "open"),
            "X1": sum(1 for d in defects if d.get("severity") == "X1" and d.get("status", "open") == "open"),
            "X2": sum(1 for d in defects if d.get("severity") == "X2" and d.get("status", "open") == "open"),
        },
    }
    out = root / "artifacts" / "phase_xii" / "DEFECT_REGISTER.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    return reg
