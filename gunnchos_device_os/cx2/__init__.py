"""CX2 Real User Surface + Provider Productization.

Stacked on CX1. Prefer real providers/processes; never inflate PASS.
FULL_COMPLETE_EXPERIENCE_COMPLETE remains False.
"""

from __future__ import annotations

FULL_COMPLETE_EXPERIENCE_COMPLETE = False
CLAIM_BOUNDARY = (
    "CX2 real-surface productization. HUMAN_VALIDATION_PENDING / "
    "PHYSICAL_VALIDATION_PENDING / EXTERNAL_PROVIDER_PENDING where not earned. "
    "Does not mutate Device Lab #134, Portal #14/#15, or WAIKE/gunnchAI PRs."
)

__all__ = [
    "evidence_taxonomy",
    "shell",
    "providers",
    "protocols",
    "journeys",
    "profiles",
    "evidence",
    "cli",
]
