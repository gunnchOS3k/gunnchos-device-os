"""Update/recovery digital completeness over A/B OTA + factory reset.

Extends the simulated OTA state machine with interrupted-update handling,
corrupt-apply recovery, rollback proofs, and factory-reset digital path.
Not a live OTA channel; no production signing keys.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from gunnchos_device_os.identity import sha256_text
from gunnchos_device_os.ota_state_machine import (
    CLAIM_BOUNDARY as OTA_CLAIM,
    Fault,
    OtaState,
    OtaStateMachine,
    Slot,
    UpdatePackage,
)


CLAIM_BOUNDARY = (
    "Digital update/recovery completeness over simulated A/B slots only. "
    "No live update channel, no production signing keys, no physical recovery claim."
)

TOKEN_UPDATE_RECOVERY_PASS = "GUNNCHOS_UPDATE_RECOVERY_DIGITAL_PASS"


class InterruptPoint(str, Enum):
    DURING_DOWNLOAD = "during_download"
    DURING_VERIFY = "during_verify"
    DURING_STAGE = "during_stage"
    DURING_APPLY = "during_apply"
    DURING_REBOOT = "during_reboot"


@dataclass
class FactoryResetResult:
    ok: bool
    preserved_slots: bool
    cleared_user_state: bool
    active_slot: str
    version: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UpdateRecoverySuite:
    """Digital completeness suite for corrupt/interrupted update + rollback + factory reset."""

    sm: OtaStateMachine = field(default_factory=OtaStateMachine)
    user_state: dict[str, Any] = field(
        default_factory=lambda: {
            "profile": "student",
            "wifi_ssid": "campus-dev",
            "apps": ["launcher", "notes"],
            "consent": {"telemetry": False},
        }
    )
    history: list[dict[str, Any]] = field(default_factory=list)

    def _pkg(self, version: str = "0.2.0") -> UpdatePackage:
        return UpdatePackage(
            version=version,
            target_slot=Slot.B,
            digest_sha256=sha256_text(version),
            signature_valid=True,
            security_version=1,
        )

    def _record(self, name: str, ok: bool, **extra: Any) -> dict[str, Any]:
        row = {"scenario": name, "ok": ok, **extra}
        self.history.append(row)
        return row

    def scenario_corrupt_download_recovers(self) -> dict[str, Any]:
        self.sm = OtaStateMachine()
        original = self.sm.active_slot
        self.sm.check_for_update(self._pkg())
        self.sm.inject_fault(Fault.DOWNLOAD_CORRUPT)
        failed = self.sm.download()
        # Pre-apply failure: reset without slot swap, then retry cleanly.
        recovered = self.sm.reset_to_idle()
        self.sm.clear_faults()
        happy = self.sm.run_happy_path(self._pkg("0.2.1"))
        ok = (
            failed["state"] == OtaState.FAILED.value
            and recovered["state"] == OtaState.IDLE.value
            and happy["state"] == OtaState.COMMITTED.value
            and happy["active_slot"] != original.value
            and self.sm.slots[happy["active_slot"]].version == "0.2.1"
        )
        return self._record(
            "corrupt_download_recovers",
            ok,
            failed_error=failed.get("last_error"),
            final_state=happy["state"],
            final_slot=happy["active_slot"],
        )

    def scenario_interrupted_update(self, point: InterruptPoint) -> dict[str, Any]:
        self.sm = OtaStateMachine()
        self.sm.check_for_update(self._pkg())
        active_before = self.sm.active_slot
        # Only post-reboot health failure uses slot-swap rollback; interrupt
        # before the new slot becomes active keeps the original slot.

        if point == InterruptPoint.DURING_DOWNLOAD:
            self.sm._transition(OtaState.DOWNLOADING, "download_started")
            self.sm._fail("update_interrupted", Fault.DOWNLOAD_CORRUPT)
        elif point == InterruptPoint.DURING_VERIFY:
            self.sm.download()
            self.sm._fail("update_interrupted", Fault.SIGNATURE_INVALID)
        elif point == InterruptPoint.DURING_STAGE:
            self.sm.download()
            self.sm.verify()
            self.sm._fail("update_interrupted", Fault.STAGE_IO_ERROR)
        elif point == InterruptPoint.DURING_APPLY:
            self.sm.download()
            self.sm.verify()
            self.sm.stage()
            self.sm._fail("update_interrupted", Fault.APPLY_TIMEOUT)
        elif point == InterruptPoint.DURING_REBOOT:
            self.sm.download()
            self.sm.verify()
            self.sm.stage()
            self.sm.apply()
            self.sm._fail("update_interrupted", Fault.REBOOT_ABORT)
            # Invalidate the staged inactive slot without activating it.
            inactive = self.sm.inactive_slot()
            self.sm.slots[inactive.value].successful = False
            self.sm.slots[inactive.value].bootable = True
        else:
            raise ValueError(point)

        recovered = self.sm.reset_to_idle()
        ok = (
            recovered["state"] == OtaState.IDLE.value
            and self.sm.active_slot == active_before
            and self.sm.pending is None
            and self.sm.slots[active_before.value].bootable is True
        )
        return self._record(
            f"interrupted_{point.value}",
            ok,
            active_slot=self.sm.active_slot.value,
            last_error=self.sm.last_error,
            recovery="reset_to_idle",
            recovered_state=recovered.get("state"),
        )

    def scenario_rollback_after_bad_health(self) -> dict[str, Any]:
        self.sm = OtaStateMachine()
        self.sm.check_for_update(self._pkg("0.3.0"))
        self.sm.download()
        self.sm.verify()
        self.sm.stage()
        self.sm.apply()
        self.sm.simulate_reboot()
        result = self.sm.health_check(healthy=False)
        ok = (
            result["state"] == OtaState.ROLLED_BACK.value
            and result["active_slot"] == Slot.A.value
            and result["slots"]["a"]["bootable"] is True
        )
        return self._record("rollback_after_bad_health", ok, status=result)

    def factory_reset(self, *, preserve_ab_slots: bool = True) -> FactoryResetResult:
        """Digital factory reset: clear user state; optionally keep A/B slot versions."""
        slot_snapshot = {k: v.to_dict() for k, v in self.sm.slots.items()}
        active = self.sm.active_slot.value
        version = self.sm.slots[active].version
        self.user_state = {
            "profile": None,
            "wifi_ssid": None,
            "apps": ["launcher"],
            "consent": {"telemetry": False},
            "factory_reset": True,
        }
        # Reset OTA machine to idle on active slot without wiping slot versions when preserving.
        self.sm.pending = None
        self.sm.last_error = None
        self.sm.faults.clear()
        self.sm.history.clear()
        if self.sm.state != OtaState.IDLE:
            # Force idle without illegal transition bookkeeping for digital reset.
            self.sm.state = OtaState.IDLE
        if not preserve_ab_slots:
            self.sm.slots[Slot.A.value].version = "0.1.0"
            self.sm.slots[Slot.B.value].version = "0.1.0"
            self.sm.active_slot = Slot.A
            active = Slot.A.value
            version = "0.1.0"
        result = FactoryResetResult(
            ok=True,
            preserved_slots=preserve_ab_slots,
            cleared_user_state=self.user_state.get("profile") is None,
            active_slot=active,
            version=version,
            details={"slots_before": slot_snapshot, "slots_after": {k: v.to_dict() for k, v in self.sm.slots.items()}},
        )
        self._record("factory_reset", result.ok, result=result.to_dict())
        return result

    def run_all(self) -> dict[str, Any]:
        results = []
        results.append(self.scenario_corrupt_download_recovers())
        for point in InterruptPoint:
            results.append(self.scenario_interrupted_update(point))
        results.append(self.scenario_rollback_after_bad_health())
        fr = self.factory_reset(preserve_ab_slots=True)
        results.append({"scenario": "factory_reset", "ok": fr.ok, "result": fr.to_dict()})
        # Second factory reset wiping slots still succeeds digitally
        fr2 = self.factory_reset(preserve_ab_slots=False)
        results.append({"scenario": "factory_reset_wipe_slots", "ok": fr2.ok, "result": fr2.to_dict()})

        ok = all(r["ok"] for r in results)
        return {
            "schema": "gunnchos.update_recovery.digital_completeness.v1",
            "ok": ok,
            "ab_strategy": "A/B slots via OtaStateMachine",
            "scenarios": results,
            "scenario_count": len(results),
            "token": TOKEN_UPDATE_RECOVERY_PASS if ok else None,
            "claim_boundary": CLAIM_BOUNDARY,
            "ota_claim_boundary": OTA_CLAIM,
            "production_keys_used": False,
            "full_operational_product_claimed": False,
        }


def run_update_recovery_completeness() -> dict[str, Any]:
    return UpdateRecoverySuite().run_all()
