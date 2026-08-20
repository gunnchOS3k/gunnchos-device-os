"""Research metrics with provenance labels (no universal-optimality claims)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.e2e_scenarios import run_e2e_scenarios_a_through_j
from gunnchos_device_os.service_continuity_execution.models import CLAIM_BOUNDARIES


def compute_research_metrics(e2e: dict[str, Any] | None = None) -> dict[str, Any]:
    e2e = e2e if e2e is not None else run_e2e_scenarios_a_through_j()
    scenarios = e2e.get("scenarios") or {}
    per = {k: bool(v.get("ok")) for k, v in scenarios.items()}
    return {
        "schema": "gunnchos.engineering_wave006.research_metrics.v1",
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "provenance": "DIGITAL_SYNTHETIC_EVIDENCE",
        "scenario_pass_rate": (e2e.get("passed") or 0) / max(1, e2e.get("total") or 1),
        "scenarios_passed": e2e.get("passed"),
        "scenarios_total": e2e.get("total"),
        "per_scenario": per,
        "UNIVERSAL_OPTIMALITY": False,
        "PRODUCTION_NETWORK_OPTIMALITY": False,
        "FIELD_MEASURED_PERFORMANCE": False,
        "claim_boundaries": dict(CLAIM_BOUNDARIES),
        "ok": e2e.get("ok") is True,
    }
