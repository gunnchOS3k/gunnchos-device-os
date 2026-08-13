"""Spares mapping — part IDs only. Stock and price stay UNKNOWN.

Does not invent inventory, quotes, or lead times. Commercial spare logistics
are EXTERNAL.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.ops.claim import CLAIM_BOUNDARY

UNKNOWN = "UNKNOWN"

# Digital mapping from fault code → spare part *identity* (MPN/class).
# Quantity-on-hand and unit price are never filled here.
SPARES_MAP: dict[str, list[dict[str, Any]]] = {
    "FC-BATT-001": [
        {"sku": "handheld_hybrid", "mpn": "6000mAh_1S2P_or_2S", "role": "battery_pack"},
        {"sku": "student_14_5", "mpn": "UNKNOWN", "role": "battery_pack"},
    ],
    "FC-DISP-001": [
        {"sku": "handheld_hybrid", "mpn": "7in_1080p_120Hz_IPS", "role": "display"},
        {"sku": "ds_xl_coder", "mpn": "UNKNOWN", "role": "display_panel", "note": "AVL_PENDING"},
    ],
    "FC-RING-001": [
        {"sku": "edge_io_rings", "mpn": "nRF52840-QIAA-R", "role": "ring_mcu"},
    ],
    "FC-DOCK-001": [
        {"sku": "dock", "mpn": "JHL8440", "role": "usb4_controller"},
    ],
    "FC-STOR-001": [
        {"sku": "handheld_hybrid", "mpn": "UNKNOWN", "role": "storage", "note": "AVL_PENDING"},
    ],
}


def map_spares(fault_code: str, *, sku: str | None = None) -> dict[str, Any]:
    rows = SPARES_MAP.get(fault_code, [])
    if sku:
        rows = [r for r in rows if r.get("sku") == sku]
    parts = []
    for row in rows:
        parts.append(
            {
                **row,
                "stock_qty": UNKNOWN,
                "unit_price": UNKNOWN,
                "lead_time_weeks": UNKNOWN,
                "moq": UNKNOWN,
            }
        )
    return {
        "ok": True,
        "fault_code": fault_code,
        "sku": sku,
        "parts": parts,
        "stock_qty": UNKNOWN,
        "unit_price": UNKNOWN,
        "logistics": "EXTERNAL",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def load_overlay_if_present(path: Path) -> dict[str, Any] | None:
    """Optional hardware-repo overlay. Missing file is not a failure."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
