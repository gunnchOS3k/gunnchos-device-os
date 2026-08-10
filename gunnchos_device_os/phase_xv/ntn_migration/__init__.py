"""NTN_MIGRATION — bearer abstraction + simulator harness + standards register.

Digital architecture/harness → DIGITALLY_VALIDATED.
Normative ecosystem / standards uptake → EXTERNAL_PENDING note (not INCOMPLETE_DIGITAL).
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "NTN bearer abstraction + simulator harness only. No live NTN, no RM520N NTN claim. "
    "Normative 3GPP/ecosystem adoption EXTERNAL_PENDING."
)

STANDARDS_REGISTER = (
    {"id": "3GPP-Rel17-NTN", "status": "tracked", "normative_uptake": "EXTERNAL_PENDING"},
    {"id": "3GPP-Rel18-NTN", "status": "tracked", "normative_uptake": "EXTERNAL_PENDING"},
    {"id": "TS-38.821", "status": "referenced", "normative_uptake": "EXTERNAL_PENDING"},
    {"id": "IoT-NTN-profiles", "status": "draft", "normative_uptake": "EXTERNAL_PENDING"},
)


@dataclass
class NtnMetrics:
    available: bool = False
    latency_ms: float = 600.0
    loss_pct: float = 2.0
    elevation_deg: float = 0.0
    constellation: str = "sim"


class NtnBearer(ABC):
    name: str
    kind: str = "ntn"

    @abstractmethod
    def connect(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def disconnect(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def metrics(self) -> NtnMetrics:
        ...


class SimulatedNtnBearer(NtnBearer):
    def __init__(self, name: str = "ntn-sim-leo"):
        self.name = name
        self._connected = False
        self._metrics = NtnMetrics(available=True, latency_ms=520.0, loss_pct=1.5, elevation_deg=35.0)

    def connect(self) -> dict[str, Any]:
        self._connected = True
        self._metrics.available = True
        return {
            "ok": True,
            "name": self.name,
            "connected": True,
            "live_ntn": False,
            "simulator": True,
        }

    def disconnect(self) -> dict[str, Any]:
        self._connected = False
        return {"ok": True, "connected": False}

    def metrics(self) -> NtnMetrics:
        return self._metrics


class FutureNtnBearer(NtnBearer):
    """Modular placeholder — disabled until a real NTN path exists."""

    def __init__(self, name: str = "ntn-future"):
        self.name = name
        self.enabled = False

    def connect(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "future_ntn_disabled",
            "enabled": False,
            "live_ntn": False,
        }

    def disconnect(self) -> dict[str, Any]:
        return {"ok": True, "connected": False}

    def metrics(self) -> NtnMetrics:
        return NtnMetrics(available=False)


class NtnMigrationHarness:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.sim = SimulatedNtnBearer()
        self.future = FutureNtnBearer()
        self.events: list[dict[str, Any]] = []

    def run_simulator(self) -> dict[str, Any]:
        c = self.sim.connect()
        m = asdict(self.sim.metrics())
        d = self.sim.disconnect()
        self.events.append({"op": "sim_cycle", "connect": c, "metrics": m, "disconnect": d})
        return {"ok": c["ok"] and d["ok"] and m["available"], "connect": c, "metrics": m}

    def assert_future_disabled(self) -> dict[str, Any]:
        c = self.future.connect()
        return {"ok": c["ok"] is False and c.get("error") == "future_ntn_disabled", "result": c}

    def write_standards_register(self) -> Path:
        out = self.root / "NTN_STANDARDS_REGISTER.json"
        payload = {
            "schema": "gunnchos.phase_xv.ntn_standards_register.v1",
            "entries": list(STANDARDS_REGISTER),
            "normative_ecosystem": "EXTERNAL_PENDING",
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_at": time.time(),
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out

    def e2e(self) -> dict[str, Any]:
        sim = self.run_simulator()
        fut = self.assert_future_disabled()
        reg = self.write_standards_register()
        ok = sim["ok"] and fut["ok"] and reg.exists()
        return {
            "schema": "gunnchos.phase_xv.ntn_migration.e2e.v1",
            "ok": ok,
            # Digital architecture + harness closed; normative ecosystem remains external.
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "normative_ecosystem": "EXTERNAL_PENDING",
            "simulator": sim,
            "future_disabled": fut,
            "standards_register": reg.name,
            "rm520n_ntn_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
