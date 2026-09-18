"""Education & Achievements timeline authority — verified vs user-entered distinction."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class EducationTimelineStore:
    """Canonical Education & Achievements authority."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self.path = self.root / "education_timeline.json"

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

    def create(self, *, owner_id: str = "profile:lab-student") -> Dict[str, Any]:
        doc = {
            "timeline_id": f"edu:{uuid.uuid4().hex[:12]}",
            "owner_id": owner_id,
            "authority": "Education & Achievements",
            "entries": [],
            "created_at": _now(),
            "updated_at": _now(),
            "certification_claimed": False,
            "offline_viewable": True,
        }
        return self._save(doc)

    def add_entry(
        self,
        entry: Dict[str, Any],
        *,
        gui_action: bool = False,
        verified_credential: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        doc = self.get() or self.create()
        source = entry.get("source") or "user_entered"
        verified = bool(entry.get("verified", False))

        # Fail closed: user-entered cannot become verified via GUI alone
        if gui_action and source == "user_entered" and verified:
            raise ValueError("USER_ENTERED_CANNOT_BE_VERIFIED")
        if source == "user_entered":
            verified = False

        # Credential-linked achievements are verified only when credential status is active
        status_badge = "user_entered"
        provenance = {
            "source": source,
            "verified": False,
            "gui_action": bool(gui_action),
            "updated_at": _now(),
        }
        if verified_credential is not None:
            raw_status = verified_credential.get("status")
            if isinstance(raw_status, dict):
                cred_status = raw_status.get("state") or raw_status.get("status")
            else:
                cred_status = raw_status or verified_credential.get("status_state")
            if cred_status in (None, "active", "valid"):
                # evidence-backed display — still not an accreditation claim
                verified = True
                status_badge = "credential_linked_active"
                provenance = {
                    "source": "credential_wallet",
                    "verified": True,
                    "credential_id": verified_credential.get("credential_id"),
                    "gui_action": bool(gui_action),
                    "updated_at": _now(),
                    "accreditation_claimed": False,
                }
            else:
                verified = False
                status_badge = f"credential_linked_{cred_status or 'unknown'}"
                provenance = {
                    "source": "credential_wallet",
                    "verified": False,
                    "credential_id": verified_credential.get("credential_id"),
                    "status": cred_status,
                    "gui_action": bool(gui_action),
                    "updated_at": _now(),
                }

        record = {
            "entry_id": entry.get("entry_id") or f"edu_entry:{uuid.uuid4().hex[:10]}",
            "label": entry.get("label") or "",
            "kind": entry.get("kind") or ("achievement" if verified_credential else "education"),
            "occurred_at": entry.get("occurred_at") or _now(),
            "source": provenance["source"],
            "verified": verified,
            "status_badge": status_badge,
            "skills": list(entry.get("skills") or []),
            "evidence_refs": list(entry.get("evidence_refs") or []),
            "credential_id": (verified_credential or {}).get("credential_id"),
            "provenance": provenance,
            "certification_claimed": False,
        }
        doc["entries"].append(record)
        doc["entries"].sort(key=lambda e: e.get("occurred_at") or "")
        doc["updated_at"] = _now()
        return self._save(doc)

    def offline_view(self) -> Dict[str, Any]:
        doc = self.get()
        if not doc:
            return {"ok": False, "entries": []}
        return {
            "ok": True,
            "timeline_id": doc["timeline_id"],
            "entries": doc["entries"],
            "offline_viewable": True,
            "certification_claimed": False,
        }

    def distinguishes_verified(self) -> bool:
        doc = self.get() or {}
        entries = doc.get("entries") or []
        has_user = any(not e.get("verified") and e.get("source") == "user_entered" for e in entries)
        has_verified = any(e.get("verified") and e.get("credential_id") for e in entries)
        return has_user and has_verified
