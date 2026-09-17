"""Export Validation Center sessions: JSON, CSV, HTML, printable, ZIP."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from gunnchos_device_os.cx4_validation_center.library import get_task
from gunnchos_device_os.cx4_validation_center.security import escape_html, safe_join


def _public_evidence(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    privacy = session.get("privacy_state") or {}
    exclude_private = privacy.get("export_excludes_private", True)
    out = []
    for e in session.get("evidence") or []:
        if exclude_private and e.get("privacy_classification") == "private":
            continue
        out.append(e)
    return out


def export_json(session: Dict[str, Any], submission: Dict[str, Any] | None = None) -> str:
    payload = {
        "evidence_eligibility": session.get("evidence_eligibility"),
        "is_rehearsal": bool(session.get("is_rehearsal")),
        "provenance": {
            "branch": session.get("branch"),
            "commit": session.get("commit"),
            "build_version": session.get("build_version"),
            "device_sku": session.get("device_sku"),
            "evidence_eligibility": session.get("evidence_eligibility"),
        },
        "task_definitions": [],
        "responses": session.get("task_results"),
        "ratings": [tr.get("participant_rating") for tr in session.get("task_results") or []],
        "reviewer_notes": [
            {"task_id": tr.get("task_id"), "notes": tr.get("reviewer_notes"), "signoff": tr.get("reviewer_signoff")}
            for tr in session.get("task_results") or []
        ],
        "evidence_manifest": _public_evidence(session),
        "gate_mapping": [],
        "unresolved_issues": [i for i in session.get("issues") or [] if i.get("status") == "open"],
        "submission": submission,
        "consent_state": session.get("consent_state"),
    }
    for tid in session.get("task_ids") or []:
        t = get_task(tid)
        if t:
            payload["task_definitions"].append(t.to_dict())
            payload["gate_mapping"].append({"task_id": tid, "gate_unlocked": t.gate_unlocked})
    return json.dumps(payload, indent=2, sort_keys=True)


def export_csv(session: Dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "evidence_eligibility",
            "task_id",
            "completion",
            "ease",
            "confidence",
            "satisfaction",
            "accessibility_impact",
            "reviewer_signoff",
            "state",
        ]
    )
    elig = session.get("evidence_eligibility") or ""
    for tr in session.get("task_results") or []:
        r = tr.get("participant_rating") or {}
        w.writerow(
            [
                elig,
                tr.get("task_id"),
                r.get("completion") or tr.get("participant_completion"),
                r.get("ease"),
                r.get("confidence"),
                r.get("satisfaction"),
                r.get("accessibility_impact"),
                tr.get("reviewer_signoff"),
                tr.get("state"),
            ]
        )
    return buf.getvalue()


def export_html(session: Dict[str, Any], submission: Dict[str, Any] | None = None) -> str:
    rows = []
    for tr in session.get("task_results") or []:
        r = tr.get("participant_rating") or {}
        rows.append(
            "<tr>"
            f"<td>{escape_html(str(tr.get('task_id')))}</td>"
            f"<td>{escape_html(str(r.get('completion') or tr.get('participant_completion') or ''))}</td>"
            f"<td>{escape_html(str(r.get('ease') or ''))}</td>"
            f"<td>{escape_html(str(r.get('accessibility_impact') or ''))}</td>"
            f"<td>{escape_html(str(tr.get('reviewer_signoff')))}</td>"
            "</tr>"
        )
    sub_hash = escape_html(str((submission or {}).get("submission_hash") or session.get("latest_submission_hash") or ""))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Validation Center Report</title>
<style>
body{{font-family: system-ui, sans-serif; margin: 2rem; color:#111; background:#f7f4ef;}}
h1{{font-size:1.6rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #444;padding:.5rem;text-align:left}}
@media print {{ body{{background:white}} }}
</style></head><body>
<header><h1>gunnchOS Validation Center — Session Report</h1>
<p>Session {escape_html(session.get('session_id',''))} · Alias {escape_html(session.get('participant_alias',''))} · SKU {escape_html(session.get('device_sku',''))}</p>
<p>Submission hash: {sub_hash}</p></header>
<main><h2>Tasks</h2><table><thead><tr><th>Task</th><th>Completion</th><th>Ease</th><th>A11y impact</th><th>Reviewer signoff</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<h2>Unresolved issues</h2>
<ul>{''.join(f"<li>{escape_html(i.get('description',''))} (sev {escape_html(str(i.get('severity')))})</li>" for i in session.get('issues') or [] if i.get('status')=='open') or '<li>None</li>'}</ul>
</main></body></html>"""


def export_bundle_zip(store_root: Path, session: Dict[str, Any], submission: Dict[str, Any] | None, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.json", export_json(session, submission))
        zf.writestr("report.csv", export_csv(session))
        zf.writestr("report.html", export_html(session, submission))
        zf.writestr("printable.html", export_html(session, submission))
        for e in _public_evidence(session):
            rel = e.get("relative_path") or ""
            if not rel:
                continue
            try:
                src = safe_join(store_root / "evidence", rel)
            except PermissionError:
                continue
            if src.is_file():
                zf.write(src, arcname=f"evidence/{e.get('file_name')}")
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "evidence": [
                        {"evidence_id": e.get("evidence_id"), "sha256": e.get("sha256"), "source": e.get("source")}
                        for e in _public_evidence(session)
                    ],
                    "private_excluded": True,
                },
                indent=2,
            ),
        )
    return dest
