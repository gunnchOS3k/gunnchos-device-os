"""Career Profile authority — composes Portfolio + Wallet without fabricating claims."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx3_2.contracts import validate_record


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


class CareerProfileStore:
    """Canonical Career Profile v1 authority."""

    def __init__(self, root: Path, *, owner_id: str = "profile:lab-student"):
        self.root = Path(root)
        self.owner_id = owner_id
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        self.path = self.root / "career_profile.json"

    def get(self) -> Optional[Dict[str, Any]]:
        if not self.path.is_file():
            return None
        return json.loads(self.path.read_text())

    def create_or_update(self, patch: Dict[str, Any], *, gui_action: bool = False) -> Dict[str, Any]:
        """Update profile. Verified claims cannot be created by UI alone."""
        existing = self.get() or {}
        now = _now()
        profile: Dict[str, Any] = {
            "profile_id": existing.get("profile_id") or f"career:{uuid.uuid4().hex[:12]}",
            "owner_id": self.owner_id,
            "display_name": patch.get("display_name", existing.get("display_name", "Lab Student")),
            "headline": patch.get("headline", existing.get("headline", "")),
            "summary": patch.get("summary", existing.get("summary", "")),
            "skills": list(patch.get("skills", existing.get("skills", []))),
            "credential_refs": list(patch.get("credential_refs", existing.get("credential_refs", []))),
            "portfolio_collection_refs": list(
                patch.get("portfolio_collection_refs", existing.get("portfolio_collection_refs", []))
            ),
            "artifact_refs": list(patch.get("artifact_refs", existing.get("artifact_refs", []))),
            "projects": list(patch.get("projects", existing.get("projects", []))),
            "education": list(patch.get("education", existing.get("education", []))),
            "experience": list(patch.get("experience", existing.get("experience", []))),
            "contact": dict(patch.get("contact", existing.get("contact", {}))),
            "links": dict(patch.get("links", existing.get("links", {}))),
            "visibility": dict(
                patch.get(
                    "visibility",
                    existing.get(
                        "visibility",
                        {
                            "display_name": "public_local",
                            "headline": "public_local",
                            "summary": "public_local",
                            "skills": "public_local",
                            "contact": "private",
                            "links": "selective",
                            "credentials": "selective",
                            "artifacts": "selective",
                            "projects": "selective",
                        },
                    ),
                )
            ),
            "provenance": dict(existing.get("provenance") or {}),
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
            "certification_claimed": False,
        }
        # Provenance: mark fields as user-entered; never upgrade to verified via GUI alone
        for field in ("display_name", "headline", "summary", "skills", "projects", "education", "experience"):
            if field in patch or field not in profile["provenance"]:
                profile["provenance"][field] = {
                    "source": "user_entered",
                    "verified": False,
                    "gui_action": bool(gui_action),
                    "updated_at": now,
                }
        # Credential/artifact refs remain references — verification lives with Wallet/issuer
        for field in ("credential_refs", "artifact_refs", "portfolio_collection_refs"):
            profile["provenance"][field] = {
                "source": "composed_refs",
                "verified": False,
                "note": "refs only; independent verifier checks signatures",
                "updated_at": now,
            }
        # Reject silent upgrade of unverified claims
        for edu in profile["education"]:
            if edu.get("verified") is True and edu.get("source") != "verified_source":
                raise ValueError("education_verified_upgrade_forbidden")
            edu["certification_claimed"] = False
        ok, errs = validate_record("CareerProfile", profile)
        if not ok:
            raise ValueError(f"career_invalid:{errs}")
        _write_json(self.path, profile)
        return profile

    def public_view(self, *, include_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        profile = self.get()
        if not profile:
            return {"ok": False, "blocker": "no_profile"}
        vis = profile.get("visibility") or {}
        include = set(include_fields or [])
        out: Dict[str, Any] = {
            "profile_id": profile["profile_id"],
            "owner_id": profile["owner_id"],
            "certification_claimed": False,
        }
        for field in ("display_name", "headline", "summary", "skills", "projects"):
            mode = vis.get(field, "private")
            if mode == "private" and field not in include:
                continue
            if mode == "selective" and field not in include and not include_fields:
                # selective requires explicit include when caller passes list; if None include public_local+selective defaults for export builder
                if include_fields is not None:
                    continue
            out[field] = profile.get(field)
        # contact always excluded unless explicitly public and selected
        if vis.get("contact") != "private" and ("contact" in include or include_fields is None and vis.get("contact") == "public_local"):
            out["contact"] = profile.get("contact")
        if "credential_refs" in include or (include_fields is None and vis.get("credentials") != "private"):
            out["credential_refs"] = profile.get("credential_refs")
        if "artifact_refs" in include or (include_fields is None and vis.get("artifacts") != "private"):
            out["artifact_refs"] = profile.get("artifact_refs")
        return out
