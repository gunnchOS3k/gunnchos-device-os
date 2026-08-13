"""Canonical honest claim tokens for connectivity / 5G-A / NTN / 6G.

These are software-architecture tokens. They do not become true because a
modem SKU, dock controller, or standards tracker is present.
"""
from __future__ import annotations

from typing import Any

# Hardware truth — Quectel RM520N-GL is 5G NR Sub-6 + LTE only.
RM520N_GL_NTN = False
RM520N_GL_6G = False
RM520N_GL_TECH = ("nr5g-sub6", "lte")

# Dock truth — USB4 / Thunderbolt 4, not TB5.
DOCK_TB4 = True
DOCK_TB5 = False

# Product / regulatory claims — never implied by digital harnesses.
STANDARDIZED_6G = False
CARRIER_ACCEPTED = False
LIVE_NTN = False
LIVE_CARRIER_ATTACH = False
PHYSICAL_RF = False

# Credentials never live in this repository.
REAL_ESIM_CREDENTIALS = "EXTERNAL"
REAL_CARRIER_CREDENTIALS = "EXTERNAL"

CLAIM_BOUNDARY = (
    "Software connectivity / 5G-Advanced architecture only. "
    "Quectel RM520N-GL is terrestrial 5G NR Sub-6 + LTE — not NTN, not 6G. "
    "Dock is USB4/TB4, not TB5. STANDARDIZED_6G=false. CARRIER_ACCEPTED=false. "
    "Real eSIM/carrier credentials are EXTERNAL. No live NTN, no live carrier attach."
)


def honest_tokens() -> dict[str, Any]:
    return {
        "STANDARDIZED_6G": STANDARDIZED_6G,
        "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
        "RM520N_GL_NTN": RM520N_GL_NTN,
        "RM520N_GL_6G": RM520N_GL_6G,
        "RM520N_GL_TECH": list(RM520N_GL_TECH),
        "DOCK_TB4": DOCK_TB4,
        "DOCK_TB5": DOCK_TB5,
        "LIVE_NTN": LIVE_NTN,
        "LIVE_CARRIER_ATTACH": LIVE_CARRIER_ATTACH,
        "PHYSICAL_RF": PHYSICAL_RF,
        "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
        "REAL_CARRIER_CREDENTIALS": REAL_CARRIER_CREDENTIALS,
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
    }


def assert_honest(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge tokens into a payload and refuse forbidden claims."""
    tokens = honest_tokens()
    out = dict(payload or {})
    out.update(tokens)
    forbidden = (
        out.get("STANDARDIZED_6G") is True,
        out.get("CARRIER_ACCEPTED") is True,
        out.get("RM520N_GL_NTN") is True,
        out.get("RM520N_GL_6G") is True,
        out.get("DOCK_TB5") is True,
        out.get("LIVE_NTN") is True,
    )
    if any(forbidden):
        raise AssertionError("forbidden connectivity claim flipped true")
    return out
