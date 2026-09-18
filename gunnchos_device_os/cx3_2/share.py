"""PortfolioSharePackage v1 — portable selective share without Wallet DB dependency for verify."""

from __future__ import annotations

import hashlib
import html
import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from gunnchos_device_os.cx3_2.contracts import validate_record


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def build_share_package(
    career_public: Dict[str, Any],
    credentials: Sequence[Dict[str, Any]],
    artifacts: Sequence[Dict[str, Any]],
    collections: Optional[Sequence[Dict[str, Any]]] = None,
    *,
    out_dir: Path,
    excluded_credential_ids: Optional[Sequence[str]] = None,
    excluded_artifact_ids: Optional[Sequence[str]] = None,
    excluded_fields: Optional[Sequence[str]] = None,
    status_map: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    excl_c = set(excluded_credential_ids or [])
    excl_a = set(excluded_artifact_ids or [])
    excl_f = set(excluded_fields or [])

    # Strip excluded fields from career view
    career = {k: v for k, v in career_public.items() if k not in excl_f}
    if "contact" in excl_f:
        career.pop("contact", None)

    creds = [dict(c) for c in credentials if c.get("credential_id") not in excl_c]
    arts = [dict(a) for a in artifacts if a.get("artifact_id") not in excl_a]
    for c in creds:
        c["certification_claimed"] = False
    for a in arts:
        a["certification_claimed"] = False

    issuer_meta = []
    for c in creds:
        sig = c.get("signature") or {}
        issuer_meta.append(
            {
                "issuer_id": c.get("issuer_id"),
                "public_key_b64": sig.get("public_key_b64"),
                "algorithm": sig.get("algorithm") or "Ed25519",
                "certification_claimed": False,
            }
        )

    status_snapshot = {}
    for c in creds:
        cid = c.get("credential_id")
        if status_map and cid in status_map:
            raw = status_map[cid]
            if isinstance(raw, str):
                status_snapshot[cid] = {
                    "credential_id": cid,
                    "status": raw,
                    "updated_at": _now(),
                    "certification_claimed": False,
                }
            else:
                status_snapshot[cid] = dict(raw)
                status_snapshot[cid].setdefault("certification_claimed", False)
        else:
            status_snapshot[cid] = {
                "credential_id": cid,
                "status": c.get("status") or "active",
                "updated_at": _now(),
                "certification_claimed": False,
            }

    package_id = f"psp:{uuid.uuid4().hex[:12]}"
    created = _now()
    package = {
        "package_id": package_id,
        "format": "gunnchos.portfolio_share_package.v1",
        "created_at": created,
        "selected": {
            "credential_ids": [c.get("credential_id") for c in creds],
            "artifact_ids": [a.get("artifact_id") for a in arts],
            "excluded_credential_ids": sorted(excl_c),
            "excluded_artifact_ids": sorted(excl_a),
            "excluded_fields": sorted(excl_f),
        },
        "career_public": career,
        "credentials": creds,
        "artifacts": arts,
        "collections": list(collections or []),
        "verification": {
            "schema": "gunnchos.cx3_2.share_verification_meta.v1",
            "requires_wallet_db": False,
            "independent_verifier": True,
            "certification_claimed": False,
        },
        "privacy_manifest": {
            "excluded_fields": sorted(excl_f),
            "excluded_credential_ids": sorted(excl_c),
            "excluded_artifact_ids": sorted(excl_a),
            "private_contact_excluded": "contact" in excl_f or "contact" not in career,
            "certification_claimed": False,
        },
        "hashes": {},
        "issuer_public_metadata": issuer_meta,
        "status_snapshot": status_snapshot,
        "status_snapshot_at": created,
        "certification_claimed": False,
        "share_token": secrets.token_urlsafe(24),
    }
    package["hashes"] = {
        "career_sha256": _sha(career),
        "credentials_sha256": _sha(creds),
        "artifacts_sha256": _sha(arts),
        "package_body_sha256": None,
    }
    # Hash without the self-hash field
    body = {k: v for k, v in package.items() if k != "hashes"}
    package["hashes"]["package_body_sha256"] = _sha(body)

    ok, errs = validate_record("PortfolioSharePackage", package)
    if not ok:
        raise ValueError(f"share_invalid:{errs}")

    pkg_dir = out_dir / package_id.replace(":", "_")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = pkg_dir / "manifest.json"
    manifest_path.write_text(json.dumps(package, indent=2) + "\n")

    # Static HTML view — escape everything
    rows = []
    for k, v in career.items():
        if k in ("certification_claimed",):
            continue
        rows.append(f"<li><strong>{html.escape(str(k))}</strong>: {html.escape(str(v)[:500])}</li>")
    for c in creds:
        rows.append(
            f"<li>Credential {html.escape(str(c.get('credential_id')))}: "
            f"{html.escape(str(c.get('name') or ''))} status={html.escape(str(c.get('status')))}</li>"
        )
    for a in arts:
        rows.append(f"<li>Artifact {html.escape(str(a.get('artifact_id')))}: {html.escape(str(a.get('title') or ''))}</li>")
    index = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Share package</title></head><body>"
        f"<h1>Portfolio Share Package</h1><p>package_id={html.escape(package_id)}</p>"
        "<p>certification_claimed=false — no accreditation claims.</p>"
        f"<ul>{''.join(rows)}</ul></body></html>\n"
    )
    (pkg_dir / "index.html").write_text(index)

    # Prove exclusions absent from payload content (privacy_manifest may list excluded IDs)
    included_cred_ids = {c.get("credential_id") for c in creds}
    included_art_ids = {a.get("artifact_id") for a in arts}
    for cid in excl_c:
        if cid and cid in included_cred_ids:
            raise ValueError(f"excluded_credential_leaked:{cid}")
        # Must not appear as an included credential row in HTML
        if cid and f"Credential {cid}" in index:
            raise ValueError(f"excluded_credential_leaked_html:{cid}")
    for aid in excl_a:
        if aid and aid in included_art_ids:
            raise ValueError(f"excluded_artifact_leaked:{aid}")
        if aid and f"Artifact {aid}" in index:
            raise ValueError(f"excluded_artifact_leaked_html:{aid}")
    blob = index + json.dumps(career) + json.dumps(creds) + json.dumps(arts)
    if "contact" in excl_f or "contact" not in career:
        orig_contact = (career_public.get("contact") or {}) if isinstance(career_public.get("contact"), dict) else {}
        for v in orig_contact.values():
            if v and str(v) in blob:
                raise ValueError("private_contact_leaked_into_share")

    return {
        "ok": True,
        "package": package,
        "package_dir": str(pkg_dir),
        "manifest_path": str(manifest_path),
        "share_token": package["share_token"],
        "certification_claimed": False,
    }


def package_contains(blob: str, needle: str) -> bool:
    return bool(needle) and needle in blob
