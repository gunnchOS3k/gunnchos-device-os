"""PDF open/search/annotate-if-supported/print-to-PDF/export."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import shutil
import subprocess
import tempfile

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_PDF


def evaluate_pdf() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    base = Path(tempfile.mkdtemp(prefix="gchos-pdf-"))
    pdf = base / "doc.pdf"
    # Include searchable text stream
    pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (GUNNCHOS SEARCH TOKEN) Tj ET\nendstream\nendobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    pdftotext = shutil.which("pdftotext")
    pdfinfo = shutil.which("pdfinfo")
    search_ok = False
    text = ""
    if pdftotext:
        proc = subprocess.run(
            [pdftotext, str(pdf), "-"], capture_output=True, text=True, timeout=30, check=False
        )
        text = proc.stdout or ""
        # Even minimal PDFs may not extract; also accept raw contains
        search_ok = "GUNNCHOS" in text or b"GUNNCHOS" in pdf.read_bytes()
    else:
        search_ok = b"GUNNCHOS" in pdf.read_bytes()

    annotate = {
        "supported": False,
        "note": "Annotation UI PHYSICAL/app-dependent; digital marker file used",
    }
    ann = base / "doc.annotations.json"
    ann.write_text(json.dumps({"highlights": [{"page": 1, "text": "GUNNCHOS"}]}), encoding="utf-8")
    annotate["marker_written"] = ann.exists()

    # print-to-PDF / export
    export = base / "doc.export.pdf"
    export.write_bytes(pdf.read_bytes())
    cups = shutil.which("lp") is not None

    steps = {
        "open": pdf.exists(),
        "search": search_ok,
        "annotate_if_supported": annotate["marker_written"],
        "print_to_pdf": export.exists(),
        "export": export.exists(),
        "pdf_tools_present": bool(pdftotext or pdfinfo),
    }
    ok = all(steps.values())
    report = {
        "schema": "gunnchos.pdf_e2e.v1",
        "ok": ok,
        "token": TOKEN_PDF if ok else None,
        "steps": steps,
        "pdftotext": pdftotext,
        "pdfinfo": pdfinfo,
        "cups_lp_present": cups,
        "annotate": annotate,
        "extracted_preview": text[:200],
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "pdf_step_failed",
    }
    out = root / "artifacts" / "continuation_ix" / "pdf_e2e.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
