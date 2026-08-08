"""Dual-screen *runtime* workflow exercises (beyond static validators).

Drives DualScreenFramework through sequenced workflow transitions with
fault injection and cross-wiring against the runtime supervisor
(display/dock/continuity). Software role model only — not a compositor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.dual_screen import CLAIM_BOUNDARY, DualScreenFramework, ScreenId
from gunnchos_device_os.dual_screen_workflows import (
    WORKFLOW_TYPES,
    place_app_stubs,
    validate_workflow,
)
from gunnchos_device_os.runtime.supervisor import RuntimeSupervisor


TOKEN_DUAL_SCREEN_RUNTIME_PASS = "GUNNCHOS_DUAL_SCREEN_RUNTIME_WORKFLOW_DIGITAL_PASS"


@dataclass
class DualScreenRuntimeHarness:
    fw: DualScreenFramework = field(default_factory=DualScreenFramework)
    events: list[dict[str, Any]] = field(default_factory=list)
    faults: set[str] = field(default_factory=set)

    def inject_fault(self, fault: str) -> None:
        self.faults.add(fault)

    def clear_faults(self) -> None:
        self.faults.clear()

    def _event(self, kind: str, **extra: Any) -> None:
        self.events.append({"kind": kind, **extra})

    def run_workflow_sequence(self, names: list[str] | None = None) -> dict[str, Any]:
        sequence = names or list(sorted(WORKFLOW_TYPES.keys()))
        results = []
        for name in sequence:
            if "workflow_apply_fail" in self.faults and name == sequence[0]:
                self._event("fault", fault="workflow_apply_fail", workflow=name)
                results.append({"workflow": name, "ok": False, "error": "workflow_apply_fail"})
                continue
            placed = place_app_stubs(self.fw, name)
            validation = validate_workflow(self.fw, name).to_dict()
            self.fw.focus(ScreenId.BOTTOM)
            self.fw.focus(ScreenId.TOP)
            if "focus_lost" in self.faults:
                for surface in self.fw.screens.values():
                    surface.focused = False
                validation = validate_workflow(self.fw, name).to_dict()
            ok = bool(validation["ok"] and placed["apps"]["top"] and placed["apps"]["bottom"])
            self._event("workflow_runtime", workflow=name, ok=ok)
            results.append(
                {
                    "workflow": name,
                    "ok": ok,
                    "apps": placed["apps"],
                    "validation": validation,
                    "layout": self.fw.layout(),
                }
            )
        ok = all(r["ok"] for r in results) and len(results) == len(sequence)
        return {
            "ok": ok,
            "results": results,
            "event_count": len(self.events),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def run_with_runtime_services(self) -> dict[str, Any]:
        """Cross-wire display + dock + continuity while exercising workflows."""
        sup = RuntimeSupervisor()
        start = sup.start_all()
        started_ok = len(start.get("faulted") or []) == 0 and len(start.get("started") or []) >= 10
        display = sup.call("display", "current")
        dock = sup.call("dock", "capabilities")
        continuity_attach = sup.call("continuity", "attach", dock_id="sim-dsxl-runtime")
        continuity_snap = sup.call("continuity", "snapshot")
        seq = self.run_workflow_sequence()
        # Mirror docked display state for dual-screen context.
        display_docked = sup.call("display", "set_docked", docked=True)
        continuity_detach = sup.call("continuity", "detach", safe=True)
        stop = sup.stop_all()
        ok = (
            started_ok
            and seq["ok"]
            and isinstance(display, dict)
            and isinstance(dock, dict)
            and isinstance(continuity_snap, dict)
            and continuity_attach is not None
        )
        return {
            "ok": ok,
            "supervisor_start": {
                "started_count": len(start.get("started") or []),
                "faulted": start.get("faulted"),
            },
            "display": display,
            "display_docked": display_docked,
            "dock": dock,
            "continuity_attach": continuity_attach,
            "continuity_snapshot": continuity_snap,
            "continuity_detach": continuity_detach,
            "workflows": seq,
            "supervisor_stop": {"stopped_count": len(stop.get("stopped") or [])},
            "claim_boundary": CLAIM_BOUNDARY,
        }


def run_dual_screen_runtime_workflows() -> dict[str, Any]:
    harness = DualScreenRuntimeHarness()
    sequence = harness.run_workflow_sequence()

    fault_harness = DualScreenRuntimeHarness()
    fault_harness.inject_fault("focus_lost")
    faulted = fault_harness.run_workflow_sequence(["coder"])
    fault_detected = faulted["ok"] is False

    with_services = DualScreenRuntimeHarness().run_with_runtime_services()

    ok = sequence["ok"] and fault_detected and with_services["ok"]
    return {
        "schema": "gunnchos.dual_screen.runtime_workflows.v1",
        "ok": ok,
        "sequence": sequence,
        "fault_injection": {
            "fault": "focus_lost",
            "detected": fault_detected,
            "result": faulted,
        },
        "with_runtime_services": with_services,
        "token": TOKEN_DUAL_SCREEN_RUNTIME_PASS if ok else None,
        "claim_boundary": CLAIM_BOUNDARY,
        "full_operational_product_claimed": False,
    }
