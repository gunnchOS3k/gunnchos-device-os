"""Research-repo adapters with provenance labels (read-only contracts)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.models import CostClass, TrustLevel

SPINE = Path(__file__).resolve().parents[4]  # repos/
# When installed, parents differ; resolve robustly.
def _repos_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here.parents[i] for i in range(2, min(8, len(here.parents)))]:
        if (p / "7gc-digital-twin").exists() or (p / "ntn-resilience-sim").exists():
            return p
        if p.name == "repos":
            return p
    return here.parents[4]


def _try_read_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def load_digital_twin_hint() -> dict[str, Any]:
    root = _repos_root()
    # Prefer small machine-readable contracts if present; never claim field RF.
    candidates = [
        ("contracts/network_path.schema.json", root / "7gc-digital-twin" / "contracts" / "network_path.schema.json"),
        ("README.md", root / "7gc-digital-twin" / "README.md"),
    ]
    found_rel = None
    available = False
    for rel, c in candidates:
        if c.exists():
            found_rel = rel
            available = True
            break
    return {
        "repo": "7gc-digital-twin",
        "repo_relative_path": found_rel,
        "source_available": available,
        "provenance": TelemetryProvenance.DIGITAL_TWIN.value,
        "usage": "contract_discovery_only",
        "used_for": "contract_discovery_only",
        "FIELD_MEASURED_PERFORMANCE": False,
    }


def load_ntn_sim_hint() -> dict[str, Any]:
    root = _repos_root()
    path = root / "ntn-resilience-sim"
    return {
        "repo": "ntn-resilience-sim",
        "provenance": TelemetryProvenance.SIMULATED.value,
        "available": path.exists(),
        "REAL_NTN_MODEM_VALIDATED": False,
        "note": "NTN paths remain ntn_simulated only in Wave005",
    }


def load_spectrumx_hint() -> dict[str, Any]:
    root = _repos_root()
    path = root / "spectrumx-ai-ran-gary"
    return {
        "repo": "spectrumx-ai-ran-gary",
        "provenance": TelemetryProvenance.CONFIGURED_TARGET.value,
        "available": path.exists(),
        "STANDARDIZED_6G": False,
    }


def load_edge_io_hint() -> dict[str, Any]:
    root = _repos_root()
    path = root / "edge-io-measurement-node"
    return {
        "repo": "edge-io-measurement-node",
        "provenance": TelemetryProvenance.DEVICE_OBSERVED.value,
        "available": path.exists(),
        "note": "adapter reads availability only; no Wave005 field measurement claim",
    }


def synthetic_candidate_from_sim(bearer: str = "ntn_simulated", *, now_ts: float) -> CandidatePath:
    """Explicit simulated candidate — not a real NTN modem."""
    return CandidatePath(
        candidate_id=f"sim-{bearer}",
        bearer_class=bearer,
        availability=True,
        signal_quality=0.4,
        latency_ms=600.0,
        jitter_ms=40.0,
        packet_loss_ratio=0.05,
        monetary_cost=0.2,
        cost_class=CostClass.METERED,
        energy_cost=1100.0,
        security_trust=TrustLevel.LIMITED,
        data_metered=True,
        data_remaining_fraction=0.5,
        application_compatibility=True,
        telemetry_timestamp=now_ts - 2.0,
        telemetry_source=TelemetryProvenance.SIMULATED,
        confidence=0.6,
        extra={"REAL_NTN_MODEM_VALIDATED": False},
    )


def adapter_inventory() -> dict[str, Any]:
    return {
        "schema": "gunnchos.engineering_wave005.research_adapters.v1",
        "adapters": [
            load_digital_twin_hint(),
            load_ntn_sim_hint(),
            load_spectrumx_hint(),
            load_edge_io_hint(),
        ],
        "claim_boundaries": {
            "STANDARDIZED_6G": False,
            "CARRIER_ACCEPTED": False,
            "REAL_NTN_MODEM_VALIDATED": False,
            "FIELD_MEASURED_PERFORMANCE": False,
        },
    }
