"""LearningEvidenceProvider v1 seam — WAIKE integration boundary.

WAIKE_INTEGRATION_SEAM_PASS=true when this provider contract exists and is callable.
WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS=true only when a genuine read-only
accepted-main WAIKE earned credential is proven — never fabricated.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


PROVIDER_SCHEMA = "gunnchos.cx3.LearningEvidenceProvider.v1"


class LearningEvidenceProvider:
    """v1 seam: list/read learning evidence; optional WAIKE earned credential probe."""

    def __init__(
        self,
        *,
        vault_evidence: Optional[Dict[str, Any]] = None,
        waike_accepted_main_probe: Optional[Path] = None,
    ):
        self.vault_evidence = vault_evidence or {}
        self.waike_accepted_main_probe = waike_accepted_main_probe

    def describe(self) -> Dict[str, Any]:
        return {
            "schema": PROVIDER_SCHEMA,
            "version": 1,
            "certification_claimed": False,
            "capabilities": [
                "list_local_evidence",
                "bind_vault_artifact",
                "probe_waike_earned_readonly",
            ],
            "waike_release_mutation": False,
            "notes": "Seam only — does not claim WAIKE earned credential integration.",
        }

    def list_local_evidence(self) -> List[Dict[str, Any]]:
        items = []
        if self.vault_evidence:
            items.append(self.vault_evidence)
        return items

    def probe_waike_earned_credential(self) -> Dict[str, Any]:
        """Fail closed unless a genuine accepted-main read-only artifact is present.

        This CX3.1 wave does not mutate WAIKE release repos. Without a proven
        accepted-main earned credential document discovered read-only, return false.
        """
        result = {
            "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False,
            "certification_claimed": False,
            "probe": "readonly_accepted_main",
            "found": False,
            "reason": "no_genuine_accepted_main_earned_credential_proven",
        }
        probe = self.waike_accepted_main_probe
        if probe and probe.is_file():
            try:
                data = json.loads(probe.read_text())
            except Exception as exc:  # noqa: BLE001
                result["reason"] = f"probe_unreadable:{type(exc).__name__}"
                return result
            # Require explicit honest markers — never invent PASS
            if (
                data.get("accepted_main") is True
                and data.get("earned_credential") is True
                and data.get("readonly_verified") is True
                and data.get("certification_claimed") is False
                and data.get("source") == "waike_accepted_main"
            ):
                result["found"] = True
                result["WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = True
                result["reason"] = "genuine_readonly_accepted_main"
                result["artifact"] = str(probe)
            else:
                result["reason"] = "probe_file_lacks_required_honest_markers"
        return result

    def seam_status(self) -> Dict[str, Any]:
        earned = self.probe_waike_earned_credential()
        return {
            "schema": PROVIDER_SCHEMA,
            "WAIKE_INTEGRATION_SEAM_PASS": True,
            "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": bool(
                earned.get("WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS")
            ),
            "certification_claimed": False,
            "earned_probe": earned,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
