"""No silent destructive uncertain gestures (RING-RELIAB-016).

Blocks destructive OS actions when gesture confidence is uncertain or when
explicit confirmation is missing. Software-simulated policy only — does not
claim a physical ring prototype.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CLAIM_BOUNDARY = (
    "Digital OS-side guard against silent destructive uncertain gestures. "
    "No physical ring prototype claim; no production biometric claim."
)

TOKEN_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_PASS = (
    "GUNNCHOS_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_DIGITAL_PASS"
)

# Destructive action classes from normative RING-RELIAB-016 text.
DESTRUCTIVE_ACTIONS = frozenset(
    {
        "delete_files",
        "approve_payments",
        "submit_assignments",
        "send_messages",
        "change_security_settings",
        "delete",
        "factory_reset",
        "revoke_device",
    }
)

DESTRUCTIVE_EVENT_TYPES = frozenset(
    {
        "destructive_confirm",
        "confirm_destructive",
    }
)

# Below this confidence, destructive intents are uncertain and must not apply.
UNCERTAIN_CONFIDENCE_THRESHOLD = 0.85


@dataclass
class GestureGuardDecision:
    allowed: bool
    reason: str
    requires_explicit_confirm: bool
    silent_accept: bool
    action: str | None = None
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SilentDestructiveUncertainGesturesGuard:
    """Policy gate: never silently apply uncertain destructive gestures."""

    threshold: float = UNCERTAIN_CONFIDENCE_THRESHOLD
    decisions: list[dict[str, Any]] = field(default_factory=list)

    def is_destructive(
        self,
        *,
        event_type: str | None = None,
        action: str | None = None,
        destructive_flag: bool = False,
    ) -> bool:
        if destructive_flag:
            return True
        if event_type and event_type in DESTRUCTIVE_EVENT_TYPES:
            return True
        if action and action in DESTRUCTIVE_ACTIONS:
            return True
        return False

    def evaluate(
        self,
        *,
        event_type: str,
        confidence: float,
        action: str | None = None,
        explicit_confirm: bool = False,
        destructive_flag: bool = False,
    ) -> GestureGuardDecision:
        destructive = self.is_destructive(
            event_type=event_type,
            action=action,
            destructive_flag=destructive_flag,
        )
        if not destructive:
            decision = GestureGuardDecision(
                allowed=True,
                reason="non_destructive",
                requires_explicit_confirm=False,
                silent_accept=False,
                action=action,
                confidence=confidence,
            )
            self.decisions.append(decision.to_dict())
            return decision

        uncertain = confidence < self.threshold
        if uncertain and not explicit_confirm:
            decision = GestureGuardDecision(
                allowed=False,
                reason="uncertain_destructive_without_confirm",
                requires_explicit_confirm=True,
                silent_accept=False,
                action=action,
                confidence=confidence,
                details={
                    "threshold": self.threshold,
                    "normative": "RING-RELIAB-016",
                },
            )
            self.decisions.append(decision.to_dict())
            return decision

        if not explicit_confirm:
            # High confidence still requires explicit confirm — never silent.
            decision = GestureGuardDecision(
                allowed=False,
                reason="destructive_requires_explicit_confirm",
                requires_explicit_confirm=True,
                silent_accept=False,
                action=action,
                confidence=confidence,
            )
            self.decisions.append(decision.to_dict())
            return decision

        if uncertain:
            decision = GestureGuardDecision(
                allowed=False,
                reason="uncertain_even_with_confirm_token_insufficient",
                requires_explicit_confirm=True,
                silent_accept=False,
                action=action,
                confidence=confidence,
                details={"note": "uncertain gestures never apply destructively"},
            )
            self.decisions.append(decision.to_dict())
            return decision

        decision = GestureGuardDecision(
            allowed=True,
            reason="explicit_confirm_high_confidence",
            requires_explicit_confirm=True,
            silent_accept=False,
            action=action,
            confidence=confidence,
        )
        self.decisions.append(decision.to_dict())
        return decision


def run_silent_destructive_uncertain_gestures() -> dict[str, Any]:
    guard = SilentDestructiveUncertainGesturesGuard()
    scenarios = [
        ("pointer_move", 0.4, None, False, True),
        ("destructive_confirm", 0.3, "delete_files", False, False),
        ("destructive_confirm", 0.3, "delete_files", True, False),
        ("destructive_confirm", 0.95, "delete_files", False, False),
        ("destructive_confirm", 0.95, "approve_payments", True, True),
        ("confirm_destructive", 0.5, "change_security_settings", False, False),
        ("key_press", 0.99, None, False, True),
    ]
    results = []
    for event_type, conf, action, explicit, expect_allowed in scenarios:
        decision = guard.evaluate(
            event_type=event_type,
            confidence=conf,
            action=action,
            explicit_confirm=explicit,
        )
        results.append(
            {
                "event_type": event_type,
                "confidence": conf,
                "action": action,
                "explicit_confirm": explicit,
                "expect_allowed": expect_allowed,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "silent_accept": decision.silent_accept,
                "ok": decision.allowed == expect_allowed and decision.silent_accept is False,
            }
        )
    ok = all(r["ok"] for r in results) and all(not d.get("silent_accept") for d in guard.decisions)
    return {
        "ok": ok,
        "token": (
            TOKEN_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_PASS
            if ok
            else f"{TOKEN_SILENT_DESTRUCTIVE_UNCERTAIN_GESTURES_PASS}_FAIL"
        ),
        "requirement_id": "RING-RELIAB-016",
        "claim_boundary": CLAIM_BOUNDARY,
        "threshold": UNCERTAIN_CONFIDENCE_THRESHOLD,
        "scenarios": results,
        "physical_ring_claimed": False,
    }
