"""PRODUCT-USE-RC-001 — persona pickup-and-use on Device Lab / engineering image.

Owner curriculum stays in waike-research-ops. This package ingests signed
owner packages only; it does not re-author WAIKE course content.
"""

from __future__ import annotations

CLAIM_BOUNDARY = (
    "PRODUCT-USE-RC-001 digital Device Lab / engineering-image journeys. "
    "Persona tokens require independently reproducible guest evidence. "
    "Not human E6. REAL_TEACHER_E6=false. STANDARDIZED_6G=false. "
    "6G_CERTIFIED=false. CARRIER_ACCEPTED=false. "
    "FOUR_GAME_ACCEPTED_MAIN_RC stays false until Edmund merges Beat Link #20."
)

__all__ = ["CLAIM_BOUNDARY"]
