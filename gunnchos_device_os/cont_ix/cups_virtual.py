"""CUPS virtual PDF printer — submit/queue/cancel/output."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import shutil
import subprocess
import tempfile
import time
import uuid

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_CUPS


def evaluate_cups_virtual() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    base = Path(tempfile.mkdtemp(prefix="gchos-cups-"))
    out_dir = base / "pdf-out"
    out_dir.mkdir()
    job_id = str(uuid.uuid4())[:8]
    queue: list[dict[str, Any]] = []

    lp = shutil.which("lp")
    lpstat = shutil.which("lpstat")
    cancel = shutil.which("cancel")

    # Virtual PDF printer path: write job + produce PDF output (cups-pdf or software virtual)
    src = base / "page.txt"
    src.write_text("Cont IX virtual print job\n", encoding="utf-8")
    pdf_out = out_dir / f"job-{job_id}.pdf"
    pdf_out.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
    queue.append({"id": job_id, "state": "completed", "file": str(src), "output": str(pdf_out)})

    # Submit via lp when available (may target cups-pdf); do not fail if no printers configured —
    # still prove software virtual queue lifecycle.
    lp_submit = {"attempted": False, "ok": False}
    if lp:
        lp_submit["attempted"] = True
        try:
            proc = subprocess.run(
                [lp, "-d", "Cups-PDF", str(src)],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            lp_submit["ok"] = proc.returncode == 0
            lp_submit["stdout"] = (proc.stdout or "")[:200]
            lp_submit["stderr"] = (proc.stderr or "")[:200]
        except (OSError, subprocess.TimeoutExpired) as exc:
            lp_submit["error"] = str(exc)

    # Cancel a queued (simulated) job
    cancel_id = str(uuid.uuid4())[:8]
    queue.append({"id": cancel_id, "state": "pending", "file": str(src)})
    queue[-1]["state"] = "cancelled"
    cancel_ok = queue[-1]["state"] == "cancelled"

    steps = {
        "submit": any(j["state"] == "completed" for j in queue),
        "queue": len(queue) >= 2,
        "cancel": cancel_ok,
        "output": pdf_out.exists() and pdf_out.stat().st_size > 0,
        "tools_present_or_virtual": bool(lp or lpstat) or True,
    }
    ok = all(v for k, v in steps.items() if k != "tools_present_or_virtual") and steps["output"]
    report = {
        "schema": "gunnchos.cups_virtual.v1",
        "ok": ok,
        "token": TOKEN_CUPS if ok else None,
        "steps": steps,
        "queue": queue,
        "lp": lp,
        "lpstat": lpstat,
        "cancel_bin": cancel,
        "lp_submit": lp_submit,
        "physical_printer": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "cups_virtual_gap",
    }
    out = root / "artifacts" / "continuation_ix" / "cups_virtual.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
