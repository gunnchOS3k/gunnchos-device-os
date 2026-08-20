"""Read-only supporting repo adapters (contract discovery only)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import CLAIM_BOUNDARIES

# Sibling repos under spine/repos — never embed absolute workstation paths in artifacts.
SUPPORTING = (
    ("ntn-resilience-sim", "SIMULATED", "NTN paths remain simulated; no real modem"),
    ("7gc-digital-twin", "DIGITAL_TWIN", "contract discovery only"),
    ("edge-io-measurement-node", "DEVICE_OBSERVED", "availability probe only; no Wave006 field claim"),
    ("spectrumx-ai-ran-gary", "CONFIGURED_TARGET", "no STANDARDIZED_6G claim"),
)


def adapter_inventory(spine_repos: Path | None = None) -> dict[str, Any]:
    """Discover supporting repos relative to a spine repos root if provided."""
    adapters = []
    for repo, provenance, note in SUPPORTING:
        available = False
        repo_relative_path = repo
        if spine_repos is not None:
            p = Path(spine_repos) / repo
            available = p.exists()
            repo_relative_path = repo
        else:
            # Best-effort: look for sibling of device-os without recording abs paths
            here = Path(__file__).resolve()
            # .../repos/gunnchos-device-os/...
            parts = here.parts
            if "repos" in parts:
                idx = parts.index("repos")
                candidate = Path(*parts[: idx + 1]) / repo
                available = candidate.exists()
            repo_relative_path = repo
        adapters.append({
            "repo": repo,
            "repo_relative_path": repo_relative_path,
            "provenance": provenance,
            "source_available": available,
            "usage": "contract_discovery_only",
            "used_for": "contract_discovery_only",
            "note": note,
            "REAL_NTN_MODEM_VALIDATED": False,
            "STANDARDIZED_6G": False,
            "FIELD_MEASURED_PERFORMANCE": False,
        })
    return {
        "schema": "gunnchos.engineering_wave006.research_adapters.v1",
        "adapters": adapters,
        "supporting_pr_required": False,
        "claim_boundaries": dict(CLAIM_BOUNDARIES),
    }
