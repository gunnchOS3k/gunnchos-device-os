"""SkillEvidenceGraph v1 — evidence-backed vs self-declared skills."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class SkillEvidenceGraph:
    """Maps skill → credentials → artifacts → WAIKE evidence → user claims."""

    SCHEMA = "SkillEvidenceGraph v1"

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self.path = self.root / "skill_evidence_graph.json"

    def get(self) -> Optional[Dict[str, Any]]:
        if not self.path.is_file():
            return None
        return json.loads(self.path.read_text())

    def _save(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        self.path.write_text(json.dumps(doc, indent=2) + "\n")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return doc

    def build(
        self,
        *,
        credentials: List[Dict[str, Any]],
        artifacts: List[Dict[str, Any]],
        user_skills: List[str],
        waike_evidence: Optional[List[Dict[str, Any]]] = None,
        revoked_ids: Optional[Set[str]] = None,
        missing_evidence_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        revoked_ids = revoked_ids or set()
        missing_evidence_ids = missing_evidence_ids or set()
        waike_evidence = waike_evidence or []
        nodes: Dict[str, Dict[str, Any]] = {}

        def ensure(skill: str) -> Dict[str, Any]:
            key = skill.strip().lower()
            if key not in nodes:
                nodes[key] = {
                    "skill_id": f"skill:{uuid.uuid4().hex[:10]}",
                    "label": skill,
                    "evidence_backed": False,
                    "self_declared": False,
                    "verified": False,
                    "credential_ids": [],
                    "artifact_ids": [],
                    "waike_evidence_ids": [],
                    "user_claims": [],
                    "why": [],
                    "status": "empty",
                }
            return nodes[key]

        for cred in credentials:
            cid = cred.get("credential_id")
            if not cid:
                continue
            raw_status = cred.get("status")
            if isinstance(raw_status, dict):
                status_val = raw_status.get("state") or raw_status.get("status")
            else:
                status_val = raw_status
            revoked = cid in revoked_ids or status_val == "revoked"
            for skill in cred.get("skills") or cred.get("skill_tags") or []:
                node = ensure(str(skill))
                node["credential_ids"].append(cid)
                if revoked:
                    node["why"].append(f"credential {cid} revoked — cannot verify skill")
                    node["status"] = "revoked_dependency"
                    node["verified"] = False
                    node["evidence_backed"] = False
                else:
                    # Evidence presence check (evidence may be dict or list)
                    evid = cred.get("evidence") or []
                    if isinstance(evid, dict):
                        evid_ids = [evid.get("evidence_id")]
                    else:
                        evid_ids = [e.get("evidence_id") for e in evid if isinstance(e, dict)]
                    if any(eid in missing_evidence_ids for eid in evid_ids if eid):
                        node["why"].append(f"missing evidence for credential {cid}")
                        node["status"] = "missing_evidence"
                        node["verified"] = False
                    else:
                        node["evidence_backed"] = True
                        node["verified"] = True
                        node["status"] = "evidence_backed"
                        node["why"].append(f"backed by active credential {cid}")

        for art in artifacts:
            aid = art.get("artifact_id")
            for skill in art.get("skills") or []:
                node = ensure(str(skill))
                if aid:
                    node["artifact_ids"].append(aid)
                node["why"].append(f"linked portfolio artifact {aid}")
                if not node["verified"]:
                    node["status"] = node["status"] if node["status"] != "empty" else "artifact_linked"

        for we in waike_evidence:
            wid = we.get("evidence_id") or we.get("id")
            for skill in we.get("skills") or []:
                node = ensure(str(skill))
                if wid:
                    node["waike_evidence_ids"].append(wid)
                node["why"].append(f"WAIKE evidence {wid} (read-only)")

        for skill in user_skills:
            node = ensure(str(skill))
            node["self_declared"] = True
            node["user_claims"].append({"text": skill, "source": "user_entered", "verified": False})
            # Text entry alone cannot become verified
            if not node["evidence_backed"]:
                node["verified"] = False
                if node["status"] in ("empty", "artifact_linked"):
                    node["status"] = "self_declared"
                node["why"].append("self-declared text entry — not verified")

        doc = {
            "schema": self.SCHEMA,
            "graph_id": f"seg:{uuid.uuid4().hex[:12]}",
            "generated_at_utc": _now(),
            "skills": list(nodes.values()),
            "certification_claimed": False,
            "rules": [
                "evidence_backed_and_self_declared_visibly_distinct",
                "text_entry_alone_cannot_verify",
                "revocation_propagates",
                "missing_evidence_reflected",
            ],
        }
        return self._save(doc)

    def explain(self, skill_label: str) -> Dict[str, Any]:
        doc = self.get() or {"skills": []}
        target = skill_label.strip().lower()
        for s in doc.get("skills") or []:
            if str(s.get("label") or "").strip().lower() == target:
                return {
                    "ok": True,
                    "skill": s,
                    "why": s.get("why") or [],
                    "verified": bool(s.get("verified")),
                    "self_declared": bool(s.get("self_declared")),
                    "evidence_backed": bool(s.get("evidence_backed")),
                }
        return {"ok": False, "reason": "skill_not_found"}

    def promote_user_text_to_verified(self, skill_label: str) -> None:
        """Negative-path helper — must raise."""
        raise PermissionError("SKILL_TEXT_ENTRY_CANNOT_BECOME_VERIFIED")
