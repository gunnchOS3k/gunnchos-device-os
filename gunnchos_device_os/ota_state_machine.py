"""OTA update / rollback state machine with fault injection (simulation).

Simulates A/B slot updates, apply, verify, commit, and rollback. Not a live
OTA channel, not fleet delivery, and not production signing.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable


CLAIM_BOUNDARY = (
    "Simulated OTA/rollback state machine only. No live update channel, "
    "no fleet delivery, no production signing claim."
)


class OtaState(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOAD_PENDING = "download_pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    STAGING = "staging"
    APPLYING = "applying"
    REBOOT_PENDING = "reboot_pending"
    HEALTH_CHECK = "health_check"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class Slot(str, Enum):
    A = "a"
    B = "b"


class Fault(str, Enum):
    DOWNLOAD_CORRUPT = "download_corrupt"
    SIGNATURE_INVALID = "signature_invalid"
    STAGE_IO_ERROR = "stage_io_error"
    APPLY_TIMEOUT = "apply_timeout"
    HEALTH_CHECK_FAIL = "health_check_fail"
    REBOOT_ABORT = "reboot_abort"


ALLOWED_TRANSITIONS: dict[OtaState, set[OtaState]] = {
    OtaState.IDLE: {OtaState.CHECKING},
    OtaState.CHECKING: {OtaState.DOWNLOAD_PENDING, OtaState.IDLE, OtaState.FAILED},
    OtaState.DOWNLOAD_PENDING: {OtaState.DOWNLOADING, OtaState.IDLE, OtaState.FAILED},
    OtaState.DOWNLOADING: {OtaState.VERIFYING, OtaState.FAILED},
    OtaState.VERIFYING: {OtaState.STAGING, OtaState.FAILED},
    OtaState.STAGING: {OtaState.APPLYING, OtaState.FAILED},
    OtaState.APPLYING: {OtaState.REBOOT_PENDING, OtaState.FAILED},
    OtaState.REBOOT_PENDING: {OtaState.HEALTH_CHECK, OtaState.FAILED},
    OtaState.HEALTH_CHECK: {OtaState.COMMITTED, OtaState.ROLLING_BACK, OtaState.FAILED},
    OtaState.COMMITTED: {OtaState.IDLE},
    OtaState.ROLLING_BACK: {OtaState.ROLLED_BACK, OtaState.FAILED},
    OtaState.ROLLED_BACK: {OtaState.IDLE},
    OtaState.FAILED: {OtaState.ROLLING_BACK, OtaState.IDLE},
}


@dataclass
class SlotInfo:
    slot: Slot
    version: str
    bootable: bool = True
    successful: bool = True
    security_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["slot"] = self.slot.value
        return d


@dataclass
class UpdatePackage:
    version: str
    target_slot: Slot
    digest_sha256: str
    signature_valid: bool = True
    security_version: int = 1
    size_bytes: int = 1024

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["target_slot"] = self.target_slot.value
        return d


@dataclass
class TransitionEvent:
    from_state: str
    to_state: str
    reason: str
    fault: str | None = None


@dataclass
class OtaStateMachine:
    """A/B OTA apply + rollback simulator with injectable faults."""

    active_slot: Slot = Slot.A
    slots: dict[str, SlotInfo] = field(default_factory=dict)
    state: OtaState = OtaState.IDLE
    pending: UpdatePackage | None = None
    faults: set[Fault] = field(default_factory=set)
    history: list[TransitionEvent] = field(default_factory=list)
    last_error: str | None = None
    _listeners: list[Callable[[TransitionEvent], None]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.slots:
            self.slots = {
                Slot.A.value: SlotInfo(slot=Slot.A, version="0.1.0", successful=True),
                Slot.B.value: SlotInfo(slot=Slot.B, version="0.0.9", successful=True),
            }

    def on_transition(self, cb: Callable[[TransitionEvent], None]) -> None:
        self._listeners.append(cb)

    def inject_fault(self, fault: Fault | str) -> None:
        f = fault if isinstance(fault, Fault) else Fault(fault)
        self.faults.add(f)

    def clear_faults(self) -> None:
        self.faults.clear()

    def _transition(self, to: OtaState, reason: str, fault: Fault | None = None) -> TransitionEvent:
        if to not in ALLOWED_TRANSITIONS.get(self.state, set()):
            raise RuntimeError(f"illegal transition {self.state.value} -> {to.value}")
        event = TransitionEvent(
            from_state=self.state.value,
            to_state=to.value,
            reason=reason,
            fault=fault.value if fault else None,
        )
        self.state = to
        self.history.append(event)
        for cb in self._listeners:
            cb(event)
        return event

    def _fail(self, reason: str, fault: Fault | None = None) -> dict[str, Any]:
        self.last_error = reason
        self._transition(OtaState.FAILED, reason, fault=fault)
        return self.status()

    def inactive_slot(self) -> Slot:
        return Slot.B if self.active_slot == Slot.A else Slot.A

    def check_for_update(self, package: UpdatePackage) -> dict[str, Any]:
        self._transition(OtaState.CHECKING, "check_started")
        active = self.slots[self.active_slot.value]
        if package.version == active.version:
            self._transition(OtaState.IDLE, "already_current")
            return {**self.status(), "update_available": False}
        if package.security_version < active.security_version:
            return self._fail("anti_rollback_security_version")
        # Target must be inactive slot
        if package.target_slot == self.active_slot:
            package = UpdatePackage(
                version=package.version,
                target_slot=self.inactive_slot(),
                digest_sha256=package.digest_sha256,
                signature_valid=package.signature_valid,
                security_version=package.security_version,
                size_bytes=package.size_bytes,
            )
        self.pending = package
        self._transition(OtaState.DOWNLOAD_PENDING, "update_available")
        return {**self.status(), "update_available": True, "package": package.to_dict()}

    def download(self) -> dict[str, Any]:
        if self.state != OtaState.DOWNLOAD_PENDING:
            raise RuntimeError("download only from download_pending")
        self._transition(OtaState.DOWNLOADING, "download_started")
        if Fault.DOWNLOAD_CORRUPT in self.faults:
            return self._fail("download_corrupt", Fault.DOWNLOAD_CORRUPT)
        self._transition(OtaState.VERIFYING, "download_complete")
        return self.status()

    def verify(self) -> dict[str, Any]:
        if self.state != OtaState.VERIFYING:
            raise RuntimeError("verify only from verifying")
        pkg = self.pending
        if pkg is None:
            return self._fail("missing_package")
        if Fault.SIGNATURE_INVALID in self.faults or not pkg.signature_valid:
            return self._fail("signature_invalid", Fault.SIGNATURE_INVALID)
        if len(pkg.digest_sha256) != 64:
            return self._fail("bad_digest")
        self._transition(OtaState.STAGING, "verified")
        return self.status()

    def stage(self) -> dict[str, Any]:
        if self.state != OtaState.STAGING:
            raise RuntimeError("stage only from staging")
        if Fault.STAGE_IO_ERROR in self.faults:
            return self._fail("stage_io_error", Fault.STAGE_IO_ERROR)
        self._transition(OtaState.APPLYING, "staged")
        return self.status()

    def apply(self) -> dict[str, Any]:
        if self.state != OtaState.APPLYING:
            raise RuntimeError("apply only from applying")
        if Fault.APPLY_TIMEOUT in self.faults:
            return self._fail("apply_timeout", Fault.APPLY_TIMEOUT)
        pkg = self.pending
        assert pkg is not None
        target = self.slots[pkg.target_slot.value]
        target.version = pkg.version
        target.security_version = pkg.security_version
        target.bootable = True
        target.successful = False  # not yet health-checked
        self._transition(OtaState.REBOOT_PENDING, "applied_to_inactive_slot")
        return self.status()

    def simulate_reboot(self) -> dict[str, Any]:
        if self.state != OtaState.REBOOT_PENDING:
            raise RuntimeError("reboot only from reboot_pending")
        if Fault.REBOOT_ABORT in self.faults:
            return self._fail("reboot_abort", Fault.REBOOT_ABORT)
        pkg = self.pending
        assert pkg is not None
        # Swap active to updated slot
        self.active_slot = pkg.target_slot
        self._transition(OtaState.HEALTH_CHECK, "rebooted_into_new_slot")
        return self.status()

    def health_check(self, *, healthy: bool = True) -> dict[str, Any]:
        if self.state != OtaState.HEALTH_CHECK:
            raise RuntimeError("health_check only from health_check")
        if Fault.HEALTH_CHECK_FAIL in self.faults or not healthy:
            self._transition(OtaState.ROLLING_BACK, "health_check_failed", Fault.HEALTH_CHECK_FAIL)
            return self.rollback()
        slot = self.slots[self.active_slot.value]
        slot.successful = True
        self._transition(OtaState.COMMITTED, "health_ok_committed")
        return self.status()

    def rollback(self) -> dict[str, Any]:
        if self.state not in (OtaState.ROLLING_BACK, OtaState.FAILED, OtaState.HEALTH_CHECK):
            raise RuntimeError(f"cannot rollback from {self.state.value}")
        if self.state != OtaState.ROLLING_BACK:
            self._transition(OtaState.ROLLING_BACK, "rollback_started")
        # Prefer the other slot if it was previously successful
        other = self.inactive_slot()
        other_info = self.slots[other.value]
        if not other_info.bootable:
            return self._fail("no_bootable_rollback_slot")
        # Mark current unsuccessful
        self.slots[self.active_slot.value].successful = False
        self.active_slot = other
        self.pending = None
        self.last_error = self.last_error or "rolled_back"
        self._transition(OtaState.ROLLED_BACK, "rollback_complete")
        return self.status()

    def reset_to_idle(self) -> dict[str, Any]:
        if self.state not in (OtaState.COMMITTED, OtaState.ROLLED_BACK, OtaState.FAILED, OtaState.IDLE):
            raise RuntimeError(f"cannot reset from {self.state.value}")
        if self.state != OtaState.IDLE:
            self._transition(OtaState.IDLE, "reset")
        self.pending = None
        self.last_error = None
        return self.status()

    def run_happy_path(self, package: UpdatePackage) -> dict[str, Any]:
        """Convenience: full successful update without faults."""
        self.clear_faults()
        self.check_for_update(package)
        self.download()
        self.verify()
        self.stage()
        self.apply()
        self.simulate_reboot()
        return self.health_check(healthy=True)

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "active_slot": self.active_slot.value,
            "slots": {k: v.to_dict() for k, v in self.slots.items()},
            "pending": self.pending.to_dict() if self.pending else None,
            "faults": sorted(f.value for f in self.faults),
            "last_error": self.last_error,
            "history": [asdict(e) for e in self.history],
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
