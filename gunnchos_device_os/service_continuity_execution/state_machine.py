"""ContinuityState legal transition table (Wave006 integrity repair)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import ContinuityEvent, ContinuityState


# Canonical states (exclude enum aliases)
CANONICAL_STATES = (
    ContinuityState.HEALTHY,
    ContinuityState.DEGRADING,
    ContinuityState.TRANSITION_PREP,
    ContinuityState.TRANSITIONING,
    ContinuityState.RESUMING,
    ContinuityState.MULTIPATH,
    ContinuityState.REDUCED_SERVICE,
    ContinuityState.OFFLINE_CAPABLE,
    ContinuityState.RECOVERING,
    ContinuityState.FAILED,
)


LEGAL_TRANSITIONS: dict[ContinuityState, dict[ContinuityEvent, ContinuityState]] = {
    ContinuityState.HEALTHY: {
        ContinuityEvent.BANDWIDTH_DROP: ContinuityState.DEGRADING,
        ContinuityEvent.BEGIN_TRANSITION: ContinuityState.TRANSITION_PREP,
        ContinuityEvent.BEGIN_MULTIPATH: ContinuityState.MULTIPATH,
        ContinuityEvent.ENTER_OFFLINE: ContinuityState.OFFLINE_CAPABLE,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.DEGRADING: {
        ContinuityEvent.BANDWIDTH_DROP: ContinuityState.REDUCED_SERVICE,
        ContinuityEvent.BANDWIDTH_RECOVER: ContinuityState.HEALTHY,
        ContinuityEvent.BEGIN_TRANSITION: ContinuityState.TRANSITION_PREP,
        ContinuityEvent.ENTER_OFFLINE: ContinuityState.OFFLINE_CAPABLE,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.TRANSITION_PREP: {
        ContinuityEvent.TRANSITION_PREP_OK: ContinuityState.TRANSITIONING,
        ContinuityEvent.TRANSITION_ROLLBACK: ContinuityState.RECOVERING,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.TRANSITIONING: {
        ContinuityEvent.TRANSITION_COMMIT: ContinuityState.HEALTHY,
        ContinuityEvent.TRANSITION_ROLLBACK: ContinuityState.RECOVERING,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.RESUMING: {
        ContinuityEvent.RESUME_DONE: ContinuityState.HEALTHY,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.MULTIPATH: {
        ContinuityEvent.MULTIPATH_DONE: ContinuityState.HEALTHY,
        ContinuityEvent.BANDWIDTH_DROP: ContinuityState.REDUCED_SERVICE,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.REDUCED_SERVICE: {
        ContinuityEvent.BANDWIDTH_RECOVER: ContinuityState.RECOVERING,
        ContinuityEvent.BEGIN_RESUME: ContinuityState.RESUMING,
        ContinuityEvent.ENTER_OFFLINE: ContinuityState.OFFLINE_CAPABLE,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.OFFLINE_CAPABLE: {
        ContinuityEvent.BEGIN_RESUME: ContinuityState.RESUMING,
        ContinuityEvent.BEGIN_RECOVERY: ContinuityState.RECOVERING,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.RECOVERING: {
        ContinuityEvent.RECOVERY_DONE: ContinuityState.HEALTHY,
        ContinuityEvent.FAIL: ContinuityState.FAILED,
    },
    ContinuityState.FAILED: {
        ContinuityEvent.BEGIN_RECOVERY: ContinuityState.RECOVERING,
        ContinuityEvent.BEGIN_RESUME: ContinuityState.RESUMING,
    },
}


def normalize_state(state: ContinuityState | str) -> ContinuityState:
    if isinstance(state, str):
        # accept legacy labels
        legacy = {
            "DEGRADED": ContinuityState.REDUCED_SERVICE,
            "OFFLINE": ContinuityState.OFFLINE_CAPABLE,
        }
        if state in legacy:
            return legacy[state]
        return ContinuityState(state)
    if state is ContinuityState.DEGRADED:
        return ContinuityState.REDUCED_SERVICE
    if state is ContinuityState.OFFLINE:
        return ContinuityState.OFFLINE_CAPABLE
    return state


def transition(old_state: ContinuityState | str, event: ContinuityEvent | str) -> ContinuityState:
    """Apply a legal transition or raise ValueError if rejected."""
    old = normalize_state(old_state)
    ev = ContinuityEvent(event) if isinstance(event, str) else event
    table = LEGAL_TRANSITIONS.get(old, {})
    if ev not in table:
        raise ValueError(f"illegal transition: {old.value} + {ev.value}")
    return table[ev]


def try_transition(old_state: ContinuityState | str, event: ContinuityEvent | str) -> dict[str, Any]:
    try:
        new_state = transition(old_state, event)
        return {"ok": True, "from": normalize_state(old_state).value, "event": str(event), "to": new_state.value}
    except ValueError as exc:
        return {
            "ok": False,
            "from": normalize_state(old_state).value,
            "event": str(event),
            "rejected": True,
            "reason": str(exc),
        }


def prove_continuity_state_machine() -> dict[str, Any]:
    legal = try_transition(ContinuityState.HEALTHY, ContinuityEvent.BEGIN_TRANSITION)
    prep = try_transition(ContinuityState.TRANSITION_PREP, ContinuityEvent.TRANSITION_PREP_OK)
    commit = try_transition(ContinuityState.TRANSITIONING, ContinuityEvent.TRANSITION_COMMIT)
    invalid = try_transition(ContinuityState.HEALTHY, ContinuityEvent.RESUME_DONE)
    recovery = try_transition(ContinuityState.REDUCED_SERVICE, ContinuityEvent.BANDWIDTH_RECOVER)
    recover_done = try_transition(ContinuityState.RECOVERING, ContinuityEvent.RECOVERY_DONE)
    fail_path = try_transition(ContinuityState.TRANSITIONING, ContinuityEvent.FAIL)
    rollback = try_transition(ContinuityState.TRANSITIONING, ContinuityEvent.TRANSITION_ROLLBACK)
    ok = (
        legal["ok"]
        and prep["ok"]
        and commit["ok"]
        and invalid["ok"] is False
        and recovery["ok"]
        and recover_done["ok"]
        and fail_path["ok"]
        and rollback["ok"]
        and set(s.value for s in CANONICAL_STATES)
        >= {
            "HEALTHY",
            "DEGRADING",
            "TRANSITION_PREP",
            "TRANSITIONING",
            "RESUMING",
            "MULTIPATH",
            "REDUCED_SERVICE",
            "OFFLINE_CAPABLE",
            "RECOVERING",
            "FAILED",
        }
    )
    return {
        "schema": "gunnchos.engineering_wave006.continuity_state_machine.v1",
        "ok": ok,
        "canonical_states": [s.value for s in CANONICAL_STATES],
        "legal_path": [legal, prep, commit],
        "invalid_jump_rejected": invalid,
        "recovery_path": [recovery, recover_done],
        "failure_path": fail_path,
        "transition_rollback_path": rollback,
    }
