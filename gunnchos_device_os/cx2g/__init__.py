"""CX2G — Chromium shell launch repair on proven CX2F DRM/Weston stack.

Stacked on CX2F. Evidence under artifacts/complete_experience/cx2g/ only.
FULL_COMPLETE_EXPERIENCE_COMPLETE remains False. Fail closed.
Forbidden: pkill -f chromium (self-kills SSH remote shell).
"""

from __future__ import annotations

FULL_COMPLETE_EXPERIENCE_COMPLETE = False
CX2G_SINGLE_PRODUCTION_SHELL_AUTHORITY = True
CLAIM_BOUNDARY = (
    "CX2G Chromium Wayland shell launch repair + render/capture proof. "
    "Stacked on CX2F DRM/Weston. Does not mutate Device Lab #134, Portal #14/#15, "
    "or CX2F history. No headless-Weston success substitution. No pkill -f chromium."
)

__all__ = [
    "FULL_COMPLETE_EXPERIENCE_COMPLETE",
    "CX2G_SINGLE_PRODUCTION_SHELL_AUTHORITY",
    "CLAIM_BOUNDARY",
]
