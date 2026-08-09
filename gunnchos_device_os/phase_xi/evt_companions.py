from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def map_physical_followups(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    journeys_dir = root / "user_journeys" / "journeys"
    companions: list[dict[str, Any]] = []
    for path in sorted(journeys_dir.glob("J-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        followups = data.get("physical_followups") or []
        if not followups:
            continue
        companions.append(
            {
                "journey": data["id"],
                "digital_status": (data.get("result") or {}).get("status", "PENDING"),
                "evt_assertions": followups,
                "not_in_digital_backlog": True,
            }
        )
    payload = {
        "schema": "gunnchos.phase_xi_evt_companions.v1",
        "count": len(companions),
        "companions": companions,
        "note": "Physical assertions belong in EVT books, not digital defect backlog.",
    }
    out = root / "artifacts" / "phase_xi" / "EVT_COMPANIONS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")
    (root / "user_journeys" / "reports" / "EVT_COMPANIONS.json").write_text(
        json.dumps(payload, indent=2) + chr(10), encoding="utf-8"
    )
    return payload
