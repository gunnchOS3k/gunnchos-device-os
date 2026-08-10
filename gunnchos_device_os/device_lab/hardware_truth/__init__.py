"""Accepted hardware truth snapshot for Device Lab profile sync."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRUTH_PATH = Path(__file__).resolve().parent / "accepted_hardware_truth.json"


def load_accepted_hardware_truth() -> dict[str, Any]:
    data = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    if data.get("SILICON_EXACT_EMULATION") is not False:
        raise ValueError("accepted hardware truth must keep SILICON_EXACT_EMULATION=false")
    return data
