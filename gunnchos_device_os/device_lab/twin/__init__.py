"""Pre-EVT twin package — schemas + handoff docs (PHYSICAL_PENDING for VF4/5/6)."""
from __future__ import annotations

from pathlib import Path

TWIN_DIR = Path(__file__).resolve().parent
HANDOFF_DOC = TWIN_DIR / "PRE_EVT_TWIN_HANDOFF.md"
HANDOFF_SCHEMA = TWIN_DIR / "pre_evt_twin_handoff.schema.json"

__all__ = ["TWIN_DIR", "HANDOFF_DOC", "HANDOFF_SCHEMA"]
