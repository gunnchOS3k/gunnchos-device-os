"""Resume export from Career Profile — HTML + text (+ optional PDF)."""

from __future__ import annotations

import hashlib
import html
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def export_resume(
    profile: Dict[str, Any],
    *,
    out_dir: Path,
    include_fields: Sequence[str],
    credentials: Optional[List[Dict[str, Any]]] = None,
    artifacts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """User-controlled resume. Hidden/private fields excluded. No ATS claims."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    include = set(include_fields)
    vis = profile.get("visibility") or {}

    def allowed(field: str) -> bool:
        if field not in include:
            return False
        if vis.get(field) == "private" and field not in ("credential_refs", "artifact_refs", "projects", "skills", "headline", "summary", "display_name"):
            # private contact etc. still blocked unless explicitly public
            if field == "contact":
                return False
        if field == "contact" and vis.get("contact", "private") == "private":
            return False
        return True

    # Fail closed: never include private contact
    if vis.get("contact", "private") == "private":
        include.discard("contact")

    blocks: List[str] = []
    text_blocks: List[str] = []
    name = profile.get("display_name") if allowed("display_name") else None
    if name:
        blocks.append(f"<h1>{html.escape(str(name))}</h1>")
        text_blocks.append(str(name))
    if allowed("headline") and profile.get("headline"):
        blocks.append(f"<p class='headline'>{html.escape(str(profile['headline']))}</p>")
        text_blocks.append(str(profile["headline"]))
    if allowed("summary") and profile.get("summary"):
        blocks.append(f"<section><h2>Summary</h2><p>{html.escape(str(profile['summary']))}</p></section>")
        text_blocks.append("Summary: " + str(profile["summary"]))
    if allowed("skills") and profile.get("skills"):
        skills = [html.escape(str(s)) for s in profile["skills"]]
        blocks.append("<section><h2>Skills</h2><ul>" + "".join(f"<li>{s}</li>" for s in skills) + "</ul></section>")
        text_blocks.append("Skills: " + ", ".join(str(s) for s in profile["skills"]))
    if allowed("projects"):
        for p in profile.get("projects") or []:
            blocks.append(
                "<section><h2>Project</h2><p>"
                + html.escape(str(p.get("title") or ""))
                + " — "
                + html.escape(str(p.get("summary") or ""))
                + "</p></section>"
            )
            text_blocks.append(f"Project: {p.get('title')} — {p.get('summary')}")
    creds_out = []
    if "credential_refs" in include:
        wanted = set(profile.get("credential_refs") or [])
        for c in credentials or []:
            if c.get("credential_id") in wanted:
                creds_out.append(
                    {
                        "credential_id": c.get("credential_id"),
                        "name": c.get("name"),
                        "status": c.get("status"),
                        "certification_claimed": False,
                    }
                )
                blocks.append(
                    "<section><h2>Credential</h2><p>"
                    + html.escape(str(c.get("name") or c.get("credential_id")))
                    + " (assertion only; certification_claimed=false)</p></section>"
                )
    arts_out = []
    if "artifact_refs" in include:
        wanted = set(profile.get("artifact_refs") or [])
        for a in artifacts or []:
            if a.get("artifact_id") in wanted:
                arts_out.append({"artifact_id": a.get("artifact_id"), "title": a.get("title"), "certification_claimed": False})
                blocks.append(
                    "<section><h2>Artifact</h2><p>"
                    + html.escape(str(a.get("title") or a.get("artifact_id")))
                    + "</p></section>"
                )

    disclaimer = (
        "This resume is a user-controlled export of learning evidence assertions. "
        "It does not claim accreditation, ATS certification, recruiter approval, "
        "degrees, diplomas, or board certification. certification_claimed=false."
    )
    html_doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Resume export</title></head><body>"
        + "".join(blocks)
        + f"<footer><p>{html.escape(disclaimer)}</p></footer></body></html>\n"
    )
    text_doc = "\n".join(text_blocks) + "\n\n" + disclaimer + "\n"
    # Fail closed: private contact must not appear
    contact = (profile.get("contact") or {}).get("email") or (profile.get("contact") or {}).get("phone")
    if contact and str(contact) in html_doc:
        if not allowed("contact"):
            raise ValueError("private_contact_leak")

    export_id = f"resume:{hashlib.sha256(html_doc.encode()).hexdigest()[:12]}"
    html_path = out_dir / f"{export_id}.html"
    text_path = out_dir / f"{export_id}.txt"
    html_path.write_text(html_doc)
    text_path.write_text(text_doc)
    export_hash = hashlib.sha256(html_doc.encode()).hexdigest()

    pdf_path = None
    pdf_ok = False
    # Legitimate PDF path: reportlab if installed; otherwise skip without fabricating
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore

        pdf_path = out_dir / f"{export_id}.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        y = 750
        for line in text_doc.splitlines()[:40]:
            c.drawString(40, y, line[:100])
            y -= 14
            if y < 40:
                break
        c.save()
        pdf_ok = pdf_path.is_file()
    except Exception:
        pdf_ok = False

    meta = {
        "export_id": export_id,
        "exported_at": _now(),
        "include_fields": sorted(include),
        "export_sha256": export_hash,
        "html_path": str(html_path),
        "text_path": str(text_path),
        "pdf_path": str(pdf_path) if pdf_ok else None,
        "pdf_produced": pdf_ok,
        "credentials": creds_out,
        "artifacts": arts_out,
        "certification_claimed": False,
        "ats_certified": False,
        "recruiter_approved": False,
        "usable_without_runtime": True,
    }
    (out_dir / f"{export_id}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
