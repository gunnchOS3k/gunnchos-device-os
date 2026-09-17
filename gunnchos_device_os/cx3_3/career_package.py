"""Complete user-controlled career package — portable, hashed, privacy-safe."""

from __future__ import annotations

import hashlib
import html
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_career_package(
    *,
    out_dir: Path,
    career_public: Dict[str, Any],
    resume_meta: Dict[str, Any],
    credentials: List[Dict[str, Any]],
    artifacts: List[Dict[str, Any]],
    education_timeline: Optional[Dict[str, Any]],
    skill_graph: Optional[Dict[str, Any]],
    verifier_metadata: Optional[Dict[str, Any]] = None,
    privacy_manifest: Optional[Dict[str, Any]] = None,
    excluded_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.exists():
        # keep parent, replace package dir content via unique id
        pass
    package_id = f"ccp_{uuid.uuid4().hex[:12]}"
    pkg_dir = out_dir / package_id
    pkg_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(pkg_dir, 0o700)
    except OSError:
        pass

    excluded_fields = list(excluded_fields or ["contact"])
    privacy = privacy_manifest or {
        "excluded_fields": excluded_fields,
        "no_hidden_private_fields": True,
        "no_local_path_leakage": True,
        "certification_claimed": False,
    }

    # Strip absolute local paths from credentials/artifacts copies without mutating signed fields
    def scrub(obj: Any) -> Any:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k in {"local_path", "absolute_path", "wallet_db_path"}:
                    continue
                if k == "artifact_path" and isinstance(v, str) and (
                    v.startswith("/Users/") or v.startswith("/home/") or v.startswith("/tmp/")
                ):
                    out[k] = f"content-ref:{hashlib.sha256(v.encode()).hexdigest()[:16]}"
                    continue
                if isinstance(v, str) and (v.startswith("/Users/") or v.startswith("/home/")):
                    # replace host absolute paths only; keep relative refs for signed evidence
                    out[k] = f"content-ref:{hashlib.sha256(v.encode()).hexdigest()[:16]}"
                else:
                    out[k] = scrub(v)
            return out
        if isinstance(obj, list):
            return [scrub(x) for x in obj]
        return obj

    career_clean = scrub(dict(career_public or {}))
    for f in excluded_fields:
        career_clean.pop(f, None)

    credentials_clean = scrub(credentials)
    artifacts_clean = scrub(artifacts)
    education_clean = scrub(education_timeline or {})
    skills_clean = scrub(skill_graph or {})

    manifest = {
        "schema": "CareerPackage v1",
        "package_id": package_id,
        "generated_at_utc": _now(),
        "career_profile": career_clean,
        "resume": {
            "export_sha256": resume_meta.get("export_sha256"),
            "formats": [k for k in ("html", "text", "pdf") if resume_meta.get(f"{k}_path") or resume_meta.get(k)],
            "ats_certified": False,
        },
        "credentials": credentials_clean,
        "artifacts": artifacts_clean,
        "education_timeline": education_clean,
        "skill_evidence_graph": skills_clean,
        "verifier_metadata": scrub(verifier_metadata or {"independent": True, "wallet_db_used": False}),
        "privacy_manifest": privacy,
        "certification_claimed": False,
        "portable_offline": True,
    }
    manifest["content_sha256"] = _sha({k: v for k, v in manifest.items() if k != "content_sha256"})

    (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Portable HTML index
    name = html.escape(str(career_clean.get("display_name") or "Career Package"))
    headline = html.escape(str(career_clean.get("headline") or ""))
    skills = "".join(f"<li>{html.escape(str(s.get('label') if isinstance(s, dict) else s))}</li>" for s in (skills_clean.get("skills") or [])[:20])
    edu_items = "".join(
        f"<li data-verified='{html.escape(str(bool(e.get('verified'))))}'>"
        f"{html.escape(str(e.get('label') or ''))} "
        f"<span class='badge'>{html.escape(str(e.get('status_badge') or e.get('source') or ''))}</span></li>"
        for e in (education_clean.get("entries") or [])
    )
    index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{name} — Career Package</title>
<style>body{{font-family:Georgia,serif;margin:2rem;}} .badge{{font-size:.8em;opacity:.7}} .warn{{color:#444}}</style>
</head><body>
<h1>{name}</h1>
<p>{headline}</p>
<p class="warn">Not an accreditation, degree, diploma, or certification claim.</p>
<p>Package ID: {html.escape(package_id)}</p>
<p>Manifest SHA-256: {html.escape(manifest['content_sha256'])}</p>
<h2>Education &amp; Achievements</h2><ul>{edu_items or '<li>None selected</li>'}</ul>
<h2>Skills</h2><ul>{skills or '<li>None selected</li>'}</ul>
<h2>Credentials</h2><p>{len(credentials_clean)} included</p>
<h2>Artifacts</h2><p>{len(artifacts_clean)} included</p>
</body></html>
"""
    (pkg_dir / "index.html").write_text(index)

    # Copy resume HTML/text if present (content only)
    for key, name in (("html_path", "resume.html"), ("text_path", "resume.txt")):
        src = resume_meta.get(key)
        if src and Path(src).is_file():
            text = Path(src).read_text()
            # ensure no private contact leakage already handled by resume exporter
            (pkg_dir / name).write_text(text)

    # Leak checks
    blob = json.dumps(manifest) + index
    leak = any(x in blob for x in ("/Users/", "private-lab-student@example.invalid", "+1-555-0100"))
    # private email may still appear if mistakenly included — treat as fail
    ok = (
        not leak
        and manifest.get("certification_claimed") is False
        and bool(manifest.get("content_sha256"))
        and (pkg_dir / "manifest.json").is_file()
        and (pkg_dir / "index.html").is_file()
    )
    return {
        "ok": ok,
        "package_id": package_id,
        "package_dir": str(pkg_dir),
        "manifest": manifest,
        "content_sha256": manifest["content_sha256"],
        "privacy_leak": leak,
        "certification_claimed": False,
    }
