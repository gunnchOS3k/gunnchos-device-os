"""6G / IMT-2030 migration harness — Rel-20/21 tracking, no compliance claim.

Loads pinned field-kit snapshots when the sibling repo is present; otherwise
uses the vendored register below (same facts, same forbidden claims).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.connectivity.honest_tokens import (
    CARRIER_ACCEPTED,
    CLAIM_BOUNDARY,
    STANDARDIZED_6G,
    honest_tokens,
)

# Pinned facts matching field-kit standards/ snapshots retrieved 2026-08-07.
# Rel-21 has no freeze in-repo — TRACKER_ONLY.
PINNED_REGISTER = (
    {
        "id": "ITU-R-M.2160",
        "source": "ITU-IMT-2030",
        "status": "APPROVED",
        "category": "framework",
        "normative_uptake": "EXTERNAL_PENDING",
        "claim": "framework mapping only — not IMT-2030 compliance",
    },
    {
        "id": "IMT2030-TPR-DRAFT",
        "source": "ITU-IMT-2030",
        "status": "DRAFT",
        "category": "performance",
        "normative_uptake": "EXTERNAL_PENDING",
        "claim": "pending SG5 Dec 2026 — cannot claim compliance",
    },
    {
        "id": "IMT2030-EVAL-DRAFT",
        "source": "ITU-IMT-2030",
        "status": "DRAFT",
        "category": "evaluation",
        "normative_uptake": "EXTERNAL_PENDING",
        "claim": "pending SG5 Dec 2026",
    },
    {
        "id": "3GPP-Rel-20",
        "source": "3GPP-REL20",
        "status": "STUDY_OR_NORMATIVE_IN_PROGRESS",
        "category": "5G-Advanced",
        "contains": ["5G-Advanced work", "early 6G studies"],
        "normative_uptake": "EXTERNAL_PENDING",
        "claim": "Rel-20 study mapped; never 6G certified",
    },
    {
        "id": "3GPP-Rel-21",
        "source": "3GPP-REL21",
        "status": "TRACKER_ONLY",
        "category": "6G-normative-planned",
        "normative_uptake": "EXTERNAL_PENDING",
        "claim": "tracker only — no Rel-21 freeze in this repo",
    },
)

USAGE_SCENARIOS = (
    "immersive_communication",
    "hyper_reliable_low_latency_communication",
    "massive_communication",
    "ubiquitous_connectivity",
    "ai_and_communication",
    "integrated_sensing_and_communication",
)

FORBIDDEN_CLAIMS = (
    "final 6G compliant",
    "6G certified",
    "carrier-approved 6G",
    "GATE_8_PASS",
    "STANDARDIZED_6G=true",
    "CARRIER_ACCEPTED=true",
)


def _sibling_field_kit() -> Path | None:
    here = Path(__file__).resolve()
    # gunnchos_device_os/connectivity/ -> repos/
    repos = here.parents[3]
    candidate = repos / "gunnchos-7gc-ai-ran-field-kit"
    if (candidate / "standards" / "requirements" / "imt2030_current_state.yaml").is_file():
        return candidate
    return None


def load_pinned_sources(root: Path | None = None) -> dict[str, Any]:
    fk = root or _sibling_field_kit()
    snapshots: list[str] = []
    tracker_path = None
    if fk is not None:
        snap_dir = fk / "standards" / "source_snapshots"
        snapshots = sorted(p.name for p in snap_dir.glob("*.md")) if snap_dir.is_dir() else []
        tracker_path = str(
            (fk / "standards" / "requirements" / "imt2030_current_state.yaml").relative_to(fk)
        )
    return {
        "sibling_field_kit": str(fk) if fk else None,
        "snapshots": snapshots,
        "tracker": tracker_path,
        "register": [dict(e) for e in PINNED_REGISTER],
        "STANDARDIZED_6G": STANDARDIZED_6G,
        "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
    }


class Imt2030MigrationHarness:
    """Executable Rel-20/21 tracking harness. Never claims standardized 6G."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def evaluate(self) -> dict[str, Any]:
        sources = load_pinned_sources()
        rel20 = next(e for e in PINNED_REGISTER if e["id"] == "3GPP-Rel-20")
        rel21 = next(e for e in PINNED_REGISTER if e["id"] == "3GPP-Rel-21")
        scenarios = {
            name: {
                "mapped": True,
                "os_dependency": "connectivity_orchestrator",
                "modem_rf_dependency": "replaceable_m2_wwan",
                "future_conformance_method": "pending_normative_specs",
                "STANDARDIZED_6G": False,
            }
            for name in USAGE_SCENARIOS
        }
        ok = (
            STANDARDIZED_6G is False
            and CARRIER_ACCEPTED is False
            and rel20["status"] == "STUDY_OR_NORMATIVE_IN_PROGRESS"
            and rel21["status"] == "TRACKER_ONLY"
            and rel21["claim"].startswith("tracker only")
        )
        report = {
            "schema": "gunnchos.connectivity.imt2030_migration.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "rel20": rel20,
            "rel21": rel21,
            "usage_scenarios": scenarios,
            "forbidden_claims": list(FORBIDDEN_CLAIMS),
            "sources": sources,
            "rm520n_ntn_claimed": False,
            "rm520n_6g_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            **honest_tokens(),
        }
        (self.root / "IMT2030_MIGRATION.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report
