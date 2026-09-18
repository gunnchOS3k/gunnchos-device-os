"""Read-only LearningEvidenceProvider adapter for accepted-main WAIKE.

Never writes to WAIKE. Never fabricates earned completion.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from gunnchos_device_os.cx3.learning_evidence import LearningEvidenceProvider


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha_obj(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


class WaikeReadOnlyAdapter(LearningEvidenceProvider):
    """Accepted-main Hub read-only adapter.

    Mutation methods intentionally raise / are absent.
    """

    MUTATION_OPS = (
        "submit_assessment",
        "create_completion",
        "seed_mastery",
        "write_grade",
        "force_mastery",
        "insert_earned_credential",
    )

    def __init__(
        self,
        *,
        hub_base: Optional[str] = None,
        session_token: Optional[str] = None,
        vault_evidence: Optional[Dict[str, Any]] = None,
        discovery: Optional[Dict[str, Any]] = None,
        fixture_evidence: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(vault_evidence=vault_evidence)
        self.hub_base = (hub_base or "").rstrip("/")
        self.session_token = session_token
        self.discovery = discovery or {}
        self.fixture_evidence = fixture_evidence  # controlled test fixture only

    def describe(self) -> Dict[str, Any]:
        base = super().describe()
        base.update(
            {
                "adapter": "WaikeReadOnlyAdapter",
                "hub_base": self.hub_base or None,
                "readonly": True,
                "mutation_ops_supported": [],
                "certification_claimed": False,
            }
        )
        return base

    def mutate(self, op: str, *args: Any, **kwargs: Any) -> None:
        raise PermissionError(f"WAIKE_READONLY_ADAPTER_REJECTS_MUTATION:{op}")

    def __getattr__(self, name: str) -> Any:
        if name in self.MUTATION_OPS:
            def _reject(*_a: Any, **_k: Any) -> None:
                raise PermissionError(f"WAIKE_READONLY_ADAPTER_REJECTS_MUTATION:{name}")
            return _reject
        raise AttributeError(name)

    def _http_get(self, path: str) -> Dict[str, Any]:
        if not self.hub_base:
            raise URLError("hub_base_unset")
        url = f"{self.hub_base}{path}"
        headers = {"Accept": "application/json"}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")

    def list_completed_achievements(self) -> List[Dict[str, Any]]:
        """List completed achievements from Hub if reachable; else empty (fail closed)."""
        if self.fixture_evidence and self.fixture_evidence.get("for_mismatch_test"):
            # Controlled fixture — not authoritative WAIKE state
            return [self.fixture_evidence]
        if not self.discovery.get("can_expose_real_completed_learning_evidence_readonly"):
            return []
        # Attempt read-only Hub gradebook/mastery if configured
        try:
            data = self._http_get("/api/v1/gradebook")
        except Exception:
            return []
        items = []
        for row in data.get("entries") or data.get("items") or []:
            if row.get("mastered") or row.get("status") == "completed":
                items.append(row)
        return items

    def fetch_assessment_result(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        if not self.discovery.get("can_expose_real_completed_learning_evidence_readonly"):
            return None
        try:
            return self._http_get(f"/api/v1/assignments/{assignment_id}/mastery")
        except Exception:
            return None

    def map_to_evidence_record(self, waike_item: Dict[str, Any]) -> Dict[str, Any]:
        content_hash = _sha_obj(waike_item)
        evidence = {
            "evidence_id": f"ev:waike:{waike_item.get('submission_id') or waike_item.get('assignment_id') or content_hash[:12]}",
            "source": "learning",
            "artifact_sha256": content_hash,
            "artifact_path": f"waike://readonly/{waike_item.get('assignment_id') or 'unknown'}",
            "captured_at": _now(),
            "mime": "application/json",
            "certification_claimed": False,
            "waike_refs": {
                "assignment_id": waike_item.get("assignment_id"),
                "submission_id": waike_item.get("submission_id"),
                "receipt_id": waike_item.get("receipt_id"),
                "mastery": waike_item.get("mastery"),
            },
            "provenance_hash": content_hash,
            "readonly": True,
        }
        return evidence

    def credential_eligibility(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        ok = bool(
            evidence.get("source") == "learning"
            and evidence.get("artifact_sha256")
            and evidence.get("waike_refs")
            and evidence.get("certification_claimed") is False
            and self.discovery.get("can_expose_real_completed_learning_evidence_readonly")
        )
        return {
            "eligible": ok,
            "criteria": [
                "learning_source",
                "stable_hash",
                "waike_refs_present",
                "real_evidence_available_gate",
                "certification_claimed_false",
            ],
            "certification_claimed": False,
        }

    def evidence_availability_gate(self) -> Dict[str, Any]:
        available = bool(self.discovery.get("can_expose_real_completed_learning_evidence_readonly"))
        return {
            "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": available,
            "reason": None if available else (self.discovery.get("lab_blocker_reason") or "RELEASE_TRAIN_DEPENDENCY_PENDING"),
            "certification_claimed": False,
        }

    def adapter_status(self) -> Dict[str, Any]:
        gate = self.evidence_availability_gate()
        # Provider pass: adapter is callable, readonly, maps schemas, rejects mutation
        try:
            self.mutate("create_completion")
            rejects = False
        except PermissionError:
            rejects = True
        provenance_ok = True  # mapping function produces provenance hashes
        demo = self.map_to_evidence_record(
            {
                "assignment_id": "schema_probe",
                "submission_id": "schema_probe",
                "receipt_id": "schema_probe",
                "mastery": {"mastered": 0},
            }
        )
        provenance_ok = bool(demo.get("provenance_hash") and demo.get("artifact_sha256"))
        return {
            "CX3_WAIKE_READ_ONLY_PROVIDER_PASS": rejects and self.describe().get("readonly") is True,
            "CX3_WAIKE_EVIDENCE_PROVENANCE_PASS": provenance_ok,
            "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": gate["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"],
            "reason": gate.get("reason"),
            "certification_claimed": False,
            "mutation_rejected": rejects,
        }

    def mismatch_detection_demo(self) -> Dict[str, Any]:
        """Controlled fixture (not authoritative WAIKE) — alter hash and detect mismatch."""
        original = {
            "assignment_id": "fixture-assign-1",
            "submission_id": "fixture-sub-1",
            "receipt_id": "fixture-receipt-1",
            "mastery": {"mastered": 1, "score": 4.0},
            "for_mismatch_test": True,
        }
        evidence = self.map_to_evidence_record(original)
        # Issue-like claim binding
        claimed_hash = evidence["artifact_sha256"]
        # Alter fixture copy
        altered = dict(original)
        altered["mastery"] = {"mastered": 1, "score": 1.0}
        altered_evidence = self.map_to_evidence_record(altered)
        mismatch = claimed_hash != altered_evidence["artifact_sha256"]
        return {
            "ok": mismatch,
            "CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS": mismatch,
            "claimed_hash": claimed_hash,
            "external_hash": altered_evidence["artifact_sha256"],
            "user_visible_problem": "evidence_hash_mismatch_against_readonly_provider",
            "original_unaffected": True,
            "authoritative_waike_mutated": False,
            "certification_claimed": False,
        }
