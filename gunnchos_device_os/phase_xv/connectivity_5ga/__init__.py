"""CONNECTIVITY_5GA — ModemManager/QMI-style software path + Wi-Fi↔cellular handoff.

No NTN claim for RM520N. RF remains PHYSICAL/EXTERNAL pending.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "ModemManager/QMI-style software cellular path + intent orchestrator. "
    "No live carrier attach. No NTN claim for RM520N. RF PHYSICAL/EXTERNAL pending."
)


@dataclass
class ModemState:
    modem_id: str
    technology: str = "5G-A-sim"
    registered: bool = False
    attached: bool = False
    apn: str | None = None
    signal_dbm: float = -110.0
    bearer: str = "none"
    qmi_ready: bool = True
    mm_ready: bool = True


@dataclass
class LinkMetrics:
    kind: str
    available: bool
    latency_ms: float
    loss_pct: float
    bandwidth_mbps: float


class ModemManagerQmiPath:
    """Software ModemManager/QMI-style path (no live RF)."""

    def __init__(self, modem_id: str = "rm520n-sim"):
        self.state = ModemState(modem_id=modem_id)
        self.events: list[dict[str, Any]] = []

    def qmi_probe(self) -> dict[str, Any]:
        ok = self.state.qmi_ready
        self.events.append({"op": "qmi_probe", "ok": ok})
        return {"ok": ok, "modem_id": self.state.modem_id, "qmi": True, "ntn_claimed": False}

    def mm_enable(self) -> dict[str, Any]:
        self.state.mm_ready = True
        self.events.append({"op": "mm_enable"})
        return {"ok": True, "mm_ready": True}

    def register(self, plmn: str = "00101") -> dict[str, Any]:
        if not self.state.mm_ready or not self.state.qmi_ready:
            return {"ok": False, "error": "modem_not_ready"}
        self.state.registered = True
        self.state.signal_dbm = -85.0
        self.events.append({"op": "register", "plmn": plmn})
        return {"ok": True, "registered": True, "plmn": plmn, "live_rf": False}

    def attach(self, apn: str = "internet") -> dict[str, Any]:
        if not self.state.registered:
            return {"ok": False, "error": "not_registered"}
        self.state.attached = True
        self.state.apn = apn
        self.state.bearer = "cellular"
        self.events.append({"op": "attach", "apn": apn})
        return {"ok": True, "attached": True, "apn": apn, "bearer": "cellular"}

    def detach(self) -> dict[str, Any]:
        self.state.attached = False
        self.state.bearer = "none"
        self.events.append({"op": "detach"})
        return {"ok": True, "attached": False}


class IntentOrchestrator:
    """Intent-based bearer selection + Wi-Fi↔cellular handoff simulation."""

    def __init__(self):
        self.active: str | None = None
        self.history: list[dict[str, Any]] = []
        self.links: dict[str, LinkMetrics] = {
            "wifi": LinkMetrics("wifi", True, 18.0, 0.2, 200.0),
            "cellular": LinkMetrics("cellular", False, 45.0, 0.5, 80.0),
        }

    def update_link(self, kind: str, **kwargs: Any) -> None:
        link = self.links[kind]
        for k, v in kwargs.items():
            setattr(link, k, v)

    def select(self, intent: str = "balanced") -> dict[str, Any]:
        candidates = [l for l in self.links.values() if l.available]
        if not candidates:
            return {"ok": False, "error": "no_bearer", "active": None}
        if intent == "latency":
            chosen = min(candidates, key=lambda l: l.latency_ms)
        elif intent == "bandwidth":
            chosen = max(candidates, key=lambda l: l.bandwidth_mbps)
        else:
            # balanced score
            def score(l: LinkMetrics) -> float:
                return (l.bandwidth_mbps / 10.0) - (l.latency_ms / 10.0) - l.loss_pct

            chosen = max(candidates, key=score)
        prev = self.active
        self.active = chosen.kind
        evt = {"op": "select", "intent": intent, "from": prev, "to": self.active, "at": time.time()}
        self.history.append(evt)
        return {"ok": True, **evt}

    def handoff_wifi_to_cellular(self) -> dict[str, Any]:
        self.update_link("wifi", available=False, loss_pct=40.0)
        self.update_link("cellular", available=True, latency_ms=40.0, loss_pct=0.4)
        return self.select("balanced")

    def handoff_cellular_to_wifi(self) -> dict[str, Any]:
        self.update_link("wifi", available=True, latency_ms=15.0, loss_pct=0.1, bandwidth_mbps=300.0)
        self.update_link("cellular", available=True)
        return self.select("latency")


class Connectivity5GA:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.modem = ModemManagerQmiPath()
        self.orch = IntentOrchestrator()

    def e2e(self) -> dict[str, Any]:
        qmi = self.modem.qmi_probe()
        mm = self.modem.mm_enable()
        reg = self.modem.register()
        att = self.modem.attach("campus.internet")
        self.orch.update_link("cellular", available=True)
        self.orch.update_link("wifi", available=True)
        sel = self.orch.select("bandwidth")
        h1 = self.orch.handoff_wifi_to_cellular()
        h2 = self.orch.handoff_cellular_to_wifi()
        det = self.modem.detach()

        ok = all(
            [
                qmi["ok"],
                mm["ok"],
                reg["ok"],
                att["ok"],
                sel["ok"],
                h1["to"] == "cellular",
                h2["to"] == "wifi",
                det["ok"],
                qmi.get("ntn_claimed") is False,
            ]
        )
        report = {
            "schema": "gunnchos.phase_xv.connectivity_5ga.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "rf_validation": "PHYSICAL_PENDING",
            "external_carrier": "EXTERNAL_PENDING",
            "rm520n_ntn_claimed": False,
            "STANDARDIZED_6G": False,
            "CARRIER_ACCEPTED": False,
            "REAL_ESIM_CREDENTIALS": "EXTERNAL",
            "modem": asdict(self.modem.state),
            "handoffs": {"wifi_to_cellular": h1, "cellular_to_wifi": h2},
            "intent_history": self.orch.history,
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
        (self.root / "CONNECTIVITY_5GA_E2E.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
