#!/usr/bin/env python3
"""Edge-IO contract demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.edge_io_contract import export_session, get_contract, start_field_session, stop_session


def main() -> int:
    blocked = start_field_session("u1", "ds_xl_coder", consent=False)
    started = start_field_session("u1", "ds_xl_coder", consent=True, research_operator=True)
    out = {
        "contract": get_contract().get("integration"),
        "blocked_no_consent": blocked,
        "started": started,
        "export": export_session("session-demo", "json"),
        "stopped": stop_session("session-demo"),
        "claim_boundary": "Edge-IO integration contract alpha",
        "mock": True,
    }
    dest = ROOT / "results/edge_io_contract_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
