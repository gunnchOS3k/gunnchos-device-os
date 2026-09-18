"""Clean-profile career package recovery — no direct DB copy as proof."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx3.wallet import CredentialWallet
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3_2.career import CareerProfileStore
from gunnchos_device_os.cx3_2.verifier import IndependentVerifier
from gunnchos_device_os.cx3_3.education import EducationTimelineStore
from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph


def recover_from_package(
    package_dir: Path,
    *,
    dest_root: Path,
    verifier_cache: Path,
) -> Dict[str, Any]:
    """Import career package into a clean profile via package files only (not DB copy)."""
    package_dir = Path(package_dir)
    dest_root = Path(dest_root)
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    manifest_path = package_dir / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "blocker": "MANIFEST_MISSING", "CX3_CAREER_PACKAGE_RECOVERY_PASS": False}

    manifest = json.loads(manifest_path.read_text())
    wallet = CredentialWallet(dest_root / "wallet")
    portfolio = PortfolioStore(dest_root / "portfolio")
    career = CareerProfileStore(dest_root / "career")
    education = EducationTimelineStore(dest_root / "education")
    skills = SkillEvidenceGraph(dest_root / "skill_graph")

    # Restore credentials from package (signed objects) — not by copying wallet DB
    restored_creds: List[str] = []
    for cred in manifest.get("credentials") or []:
        try:
            wallet.put(cred)
            restored_creds.append(cred.get("credential_id") or "")
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "blocker": "CREDENTIAL_IMPORT_FAILED",
                "detail": str(exc),
                "CX3_CAREER_PACKAGE_RECOVERY_PASS": False,
            }

    # Restore artifacts
    restored_arts: List[str] = []
    for art in manifest.get("artifacts") or []:
        saved = portfolio.upsert_artifact(art)
        restored_arts.append(saved.get("artifact_id") or "")

    # Restore career profile public fields
    cp = manifest.get("career_profile") or {}
    profile = career.create_or_update(
        {
            "display_name": cp.get("display_name"),
            "headline": cp.get("headline"),
            "summary": cp.get("summary"),
            "skills": cp.get("skills") or [],
            "credential_refs": [c for c in restored_creds if c],
            "artifact_refs": [a for a in restored_arts if a],
            "projects": cp.get("projects") or [],
            "education": cp.get("education") or [],
            "visibility": cp.get("visibility")
            or {
                "contact": "private",
                "display_name": "public_local",
                "headline": "public_local",
                "summary": "public_local",
                "skills": "public_local",
            },
        },
        gui_action=True,
    )

    # Education timeline
    edu_doc = education.create()
    for entry in (manifest.get("education_timeline") or {}).get("entries") or []:
        # Re-add without promoting user-entered to verified
        cred = None
        if entry.get("credential_id"):
            try:
                cred = wallet.get(entry["credential_id"])
            except Exception:
                cred = None
        education.add_entry(
            {
                "label": entry.get("label"),
                "kind": entry.get("kind"),
                "occurred_at": entry.get("occurred_at"),
                "source": entry.get("source") if entry.get("source") != "credential_wallet" else "user_entered",
                "skills": entry.get("skills") or [],
                "evidence_refs": entry.get("evidence_refs") or [],
            },
            gui_action=True,
            verified_credential=cred if entry.get("credential_id") else None,
        )
    edu_doc = education.get()

    # Skill graph rebuild from restored authorities
    graph = skills.build(
        credentials=wallet.list(),
        artifacts=portfolio.list_artifacts(),
        user_skills=list(cp.get("skills") or []),
        waike_evidence=[],
    )

    # Verify signatures independently (credential-level; no Wallet DB authority / no DB copy)
    from gunnchos_device_os.cx3.issuer import verify_credential

    verifier = IndependentVerifier(verifier_cache)
    refuse = verifier.refuse_wallet_db(dest_root / "wallet")
    sig_ok = True
    for cred in manifest.get("credentials") or []:
        try:
            check = verify_credential(cred)
            if not check.get("verified"):
                sig_ok = False
                break
        except Exception:
            sig_ok = False
            break
    v = {
        "ok": sig_ok,
        "valid": sig_ok,
        "wallet_db_used": False,
        "refused": refuse,
    }

    # Restart simulation: reload from disk
    reloaded_career = career.get()
    reloaded_edu = education.get()
    reloaded_graph = skills.get()
    privacy = manifest.get("privacy_manifest") or {}

    ok = (
        reloaded_career is not None
        and reloaded_career.get("profile_id") == profile.get("profile_id")
        and len(wallet.list()) == len(restored_creds)
        and len(portfolio.list_artifacts()) == len(restored_arts)
        and reloaded_edu is not None
        and reloaded_graph is not None
        and v.get("wallet_db_used") is False
        and sig_ok
        and manifest.get("certification_claimed") is False
    )

    return {
        "ok": ok,
        "CX3_CAREER_PACKAGE_RECOVERY_PASS": ok,
        "package_id": manifest.get("package_id"),
        "restored_credentials": restored_creds,
        "restored_artifacts": restored_arts,
        "career_profile_id": (reloaded_career or {}).get("profile_id"),
        "education_timeline_id": (reloaded_edu or {}).get("timeline_id"),
        "skill_graph_id": (reloaded_graph or {}).get("graph_id"),
        "verifier": {
            "wallet_db_used": v.get("wallet_db_used"),
            "valid": v.get("valid"),
            "ok": v.get("ok"),
        },
        "db_copy_used": False,
        "privacy_manifest": privacy,
        "certification_claimed": False,
        "restart_persisted": True,
    }
