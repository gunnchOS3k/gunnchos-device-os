"""OS-facing adapter over authenticated ring input receiver."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .fallback_input import OsSafeFallback

try:
    from gunnchos_device_os.silent_destructive_uncertain_gestures import (
        SilentDestructiveUncertainGesturesGuard,
    )
except ImportError:  # pragma: no cover - package path variants in CI
    SilentDestructiveUncertainGesturesGuard = None  # type: ignore[misc, assignment]


def _load_ari():
    candidates = [
        Path(__file__).resolve().parents[2]
        / "gunnchos-hardware-industrial-design"
        / "ring_input"
        / "python",
        Path(
            "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
            "gunnchos-hardware-industrial-design/ring_input/python"
        ),
    ]
    for root in candidates:
        if (root / "authenticated_ring_input" / "__init__.py").exists():
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            return importlib.import_module("authenticated_ring_input")
    raise ImportError("authenticated_ring_input reference package not found")


EVENT_TO_OS = {
    "pointer_move": "pointer_delta",
    "click": "pointer_button",
    "key_press": "key_down",
    "key_release": "key_up",
    "scroll": "scroll_delta",
    "text_select": "select_range",
    "destructive_confirm": "confirm_destructive",
    "heartbeat": "noop",
    "calibration_ping": "noop",
}


@dataclass
class OsInputAction:
    kind: str
    event_type: str
    confidence: float
    payload: dict[str, Any]
    device_id: str
    session_id: str
    authenticated: bool = True


@dataclass
class RingInputAdapter:
    """Bridges verified protocol events into gunnchOS input actions."""

    host_id: str = "host-dsxl-01"
    fallback: OsSafeFallback = field(default_factory=OsSafeFallback)
    _receiver: Any = None
    _ari: Any = None
    actions: list[OsInputAction] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._ari = _load_ari()
        self._receiver = self._ari.AuthenticatedReceiver(
            host_id=self.host_id, known_devices=set()
        )
        self._destructive_guard = (
            SilentDestructiveUncertainGesturesGuard()
            if SilentDestructiveUncertainGesturesGuard is not None
            else None
        )

    @property
    def receiver(self):
        return self._receiver

    def attach_session(
        self,
        session_material: dict[str, Any],
        calibration_registry: Any,
    ) -> None:
        self._receiver.calibration = calibration_registry
        self._receiver.register_session(session_material)

    def ingest(self, event: dict[str, Any], *, now_ms: int | None = None) -> OsInputAction | None:
        if now_ms is not None:
            self._receiver.now_ms = now_ms
        ok, reason, verified = self._receiver.receive(event)
        if not ok or verified is None:
            self.fallback.engage(reason.value if reason else "auth_fail")
            return None
        event_type = str(verified["event_type"])
        confidence = float(verified["confidence"])
        payload = dict(verified.get("payload") or {})
        # RING-RELIAB-016: never silently apply uncertain destructive gestures.
        if self._destructive_guard is not None:
            action_name = payload.get("action")
            # Authenticated high-confidence destructive_confirm *is* the confirm token.
            explicit = bool(payload.get("explicit_confirm")) or (
                event_type in {"destructive_confirm", "confirm_destructive"}
                and confidence >= self._destructive_guard.threshold
            )
            decision = self._destructive_guard.evaluate(
                event_type=event_type,
                confidence=confidence,
                action=str(action_name) if action_name else None,
                explicit_confirm=explicit,
                destructive_flag=bool(payload.get("destructive")),
            )
            if not decision.allowed:
                self.fallback.engage(decision.reason)
                return None
        kind = EVENT_TO_OS.get(event_type, "unknown")
        action = OsInputAction(
            kind=kind,
            event_type=event_type,
            confidence=confidence,
            payload=payload,
            device_id=str(verified["device_id"]),
            session_id=str(verified["session_id"]),
            authenticated=True,
        )
        self.actions.append(action)
        return action

    def status(self) -> dict[str, Any]:
        return {
            "adapter": "gunnchos-device-os/ring_input",
            "physical_ring_claimed": False,
            "statuses": {
                "AUTHENTICATED_INPUT_PROTOCOL_PASS": True,
                "RING_PHYSICAL_PROTOTYPE_PENDING": True,
            },
            "fallback": {
                "active": self.fallback.active,
                "available": self.fallback.available(),
                "reason": self.fallback.reason,
            },
            "accepted_actions": len(self.actions),
            "evidence_class": "SOFTWARE_SIMULATED",
        }
