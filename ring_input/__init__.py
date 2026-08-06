"""gunnchOS authenticated ring input adapter.

Statuses: AUTHENTICATED_INPUT_PROTOCOL_PASS · RING_PHYSICAL_PROTOTYPE_PENDING
No physical ring is claimed. Consumes authenticated events from the protocol
reference (hardware-industrial-design) and maps them to OS input actions with
safe fallback.
"""

from .adapter import RingInputAdapter, OsInputAction
from .fallback_input import OsSafeFallback

__all__ = [
    "OsInputAction",
    "OsSafeFallback",
    "RingInputAdapter",
]

STATUSES = {
    "AUTHENTICATED_INPUT_PROTOCOL_PASS": True,
    "RING_PHYSICAL_PROTOTYPE_PENDING": True,
}
PHYSICAL_RING_CLAIMED = False
