"""RMA + support case state machine — DEV/TEST digital records only.

Commercial warranty adjudication is EXTERNAL. Physical depot receive/ship
is recorded as a digital state, not a claim that a parcel moved.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from gunnchos_device_os.ops.claim import CLAIM_BOUNDARY, COMMERCIAL_WARRANTY, PRODUCTION_RELEASE_CLAIMED
from gunnchos_device_os.ops.fault_codes import lookup as lookup_fault
from gunnchos_device_os.ops.spares import map_spares
from gunnchos_device_os.release_engineering import serviceability as svc

STORE_SCHEMA = "gunnchos.ops.rma_store.v1"

STATES = (
    "OPEN",
    "DIAGNOSED",
    "AUTHORIZED",
    "RECEIVED",
    "IN_REPAIR",
    "RETEST",
    "READY_TO_SHIP",
    "SHIPPED",
    "CLOSED",
    "REJECTED",
    "WARRANTY_EXTERNAL",
)

TRANSITIONS: dict[str, tuple[str, ...]] = {
    "OPEN": ("DIAGNOSED", "REJECTED", "WARRANTY_EXTERNAL"),
    "DIAGNOSED": ("AUTHORIZED", "REJECTED", "WARRANTY_EXTERNAL"),
    "AUTHORIZED": ("RECEIVED", "REJECTED", "WARRANTY_EXTERNAL"),
    "RECEIVED": ("IN_REPAIR", "REJECTED"),
    "IN_REPAIR": ("RETEST", "REJECTED"),
    "RETEST": ("READY_TO_SHIP", "IN_REPAIR"),
    "READY_TO_SHIP": ("SHIPPED",),
    "SHIPPED": ("CLOSED",),
    "CLOSED": (),
    "REJECTED": (),
    "WARRANTY_EXTERNAL": (),
}


class RmaSupportDesk:
    def __init__(self, store_path: Path) -> None:
        self.store_path = Path(store_path)
        if not self.store_path.exists():
            self._write(
                {
                    "schema": STORE_SCHEMA,
                    "cases": {},
                    "PRODUCTION_RELEASE_CLAIMED": False,
                    "commercial_warranty": COMMERCIAL_WARRANTY,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    def _read(self) -> dict[str, Any]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> dict[str, Any]:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data["PRODUCTION_RELEASE_CLAIMED"] = PRODUCTION_RELEASE_CLAIMED
        data["commercial_warranty"] = COMMERCIAL_WARRANTY
        self.store_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data

    def open_case(
        self,
        *,
        device_id: str,
        serial: str,
        sku: str,
        fault_code: str,
        symptom: str,
    ) -> dict[str, Any]:
        fault = lookup_fault(fault_code)
        if not fault.get("ok"):
            return fault
        case_id = f"RMA-DEV-{uuid.uuid4().hex[:10]}"
        case = {
            "case_id": case_id,
            "device_id": device_id,
            "serial": serial,
            "sku": sku,
            "fault_code": fault_code,
            "symptom": symptom,
            "state": "OPEN",
            "service_history": [],
            "spares": map_spares(fault_code, sku=sku),
            "commercial_warranty": COMMERCIAL_WARRANTY,
            "physical_parcel": "EXTERNAL",
            "opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._append_history(case, "OPEN", note="case_opened")
        data = self._read()
        data["cases"][case_id] = case
        self._write(data)
        return {"ok": True, "case": case}

    def _append_history(self, case: dict[str, Any], state: str, *, note: str) -> None:
        case["service_history"].append(
            {
                "state": state,
                "note": note,
                "ts": time.time(),
            }
        )

    def transition(self, case_id: str, new_state: str, *, note: str = "") -> dict[str, Any]:
        if new_state not in STATES:
            return {"ok": False, "error": "unknown_state", "state": new_state}
        data = self._read()
        case = data["cases"].get(case_id)
        if case is None:
            return {"ok": False, "error": "case_not_found"}
        current = case["state"]
        allowed = TRANSITIONS.get(current, ())
        if new_state not in allowed:
            return {
                "ok": False,
                "error": "illegal_transition",
                "from": current,
                "to": new_state,
                "allowed": list(allowed),
            }
        case["state"] = new_state
        self._append_history(case, new_state, note=note or f"transition:{current}->{new_state}")
        self._write(data)
        return {"ok": True, "case_id": case_id, "state": new_state}

    def service_history(self, case_id: str) -> dict[str, Any]:
        data = self._read()
        case = data["cases"].get(case_id)
        if case is None:
            return {"ok": False, "error": "case_not_found"}
        return {"ok": True, "case_id": case_id, "history": list(case["service_history"]), "state": case["state"]}

    def attach_diagnostic_bundle(self, case_id: str, device_root: Path, out_path: Path) -> dict[str, Any]:
        data = self._read()
        if case_id not in data["cases"]:
            return {"ok": False, "error": "case_not_found"}
        result = svc.export_diagnostic_bundle(device_root, out_path)
        if result.get("ok"):
            self._append_history(data["cases"][case_id], data["cases"][case_id]["state"], note="diagnostic_bundle")
            data["cases"][case_id]["diagnostic_bundle_sha256"] = result.get("sha256")
            self._write(data)
        return result

    def enter_repair_mode(self, case_id: str, device_root: Path) -> dict[str, Any]:
        data = self._read()
        case = data["cases"].get(case_id)
        if case is None:
            return {"ok": False, "error": "case_not_found"}
        if case["state"] not in ("RECEIVED", "IN_REPAIR"):
            return {"ok": False, "error": "repair_mode_requires_received_or_in_repair", "state": case["state"]}
        result = svc.enter_repair_mode(device_root, reason=f"rma:{case_id}")
        if case["state"] == "RECEIVED":
            case["state"] = "IN_REPAIR"
            self._append_history(case, "IN_REPAIR", note="repair_mode_entered")
            self._write(data)
        return result

    def replacement_transfer(
        self, case_id: str, repo_root: Path, old_root: Path, new_root: Path
    ) -> dict[str, Any]:
        data = self._read()
        case = data["cases"].get(case_id)
        if case is None:
            return {"ok": False, "error": "case_not_found"}
        result = svc.transfer_device_replacement(
            repo_root, old_root, new_root, transfer_reason=f"rma:{case_id}"
        )
        if result.get("ok"):
            self._append_history(case, case["state"], note="replacement_transfer")
            self._write(data)
        return result

    def wipe_for_return(self, case_id: str, device_root: Path) -> dict[str, Any]:
        data = self._read()
        case = data["cases"].get(case_id)
        if case is None:
            return {"ok": False, "error": "case_not_found"}
        result = svc.secure_wipe(device_root, passes=2)
        if result.get("ok"):
            self._append_history(case, case["state"], note="secure_wipe_digital")
            case["wipe"] = {"ok": True, "physical_media_sanitize": "EXTERNAL"}
            self._write(data)
        return {**result, "physical_media_sanitize": "EXTERNAL"}

    def support_window(self, component: str, version: str) -> dict[str, Any]:
        """Digital update-support / EOL metadata. Business-year commitments EXTERNAL."""
        from gunnchos_device_os.phase_xv.support_lifecycle import SupportLifecycle

        tmp = self.store_path.parent / "eol_scratch"
        life = SupportLifecycle(tmp)
        eol = life.write_eol_metadata()
        upgrade = life.validate_upgrade_path("0.xiv", "0.xv")
        return {
            "ok": True,
            "component": component,
            "version": version,
            "eol": eol,
            "upgrade_path_example": upgrade,
            "business_year_commitments": "EXTERNAL_PENDING",
            "claim_boundary": CLAIM_BOUNDARY,
        }
