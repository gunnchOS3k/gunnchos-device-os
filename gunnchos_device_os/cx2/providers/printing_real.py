"""Real CUPS/IPP digital print path; physical always pending."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RealPrintingProvider:
    root: Path
    jobs: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        (self.root / "output").mkdir(parents=True, exist_ok=True)
        (self.root / "queue").mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        return self.discover()

    def discover(self) -> dict:
        lpstat = shutil.which("lpstat")
        lp = shutil.which("lp")
        ipptool = shutil.which("ipptool")
        cups_printers: List[str] = []
        if lpstat:
            proc = subprocess.run([lpstat, "-a"], capture_output=True, text=True, timeout=10, check=False)
            if proc.returncode == 0:
                for line in (proc.stdout or "").splitlines():
                    if line.strip():
                        cups_printers.append(line.split()[0])
        # Prepare PDF backend virtual queue packet for physical SI
        si = {
            "PHYSICAL_PRINTER_VALIDATION_PENDING": True,
            "packet": {
                "usb_ipp": "pending",
                "lan_ipp": "pending",
                "duplex": "pending",
                "color": "pending",
                "paper": "pending",
                "cancel": "pending",
                "scanner_mfp": "pending",
            },
        }
        (self.root / "PHYSICAL_PRINTER_SI_PACKET.json").write_text(
            __import__("json").dumps(si, indent=2) + "\n"
        )
        if cups_printers and lp:
            evidence = "REAL_PROVIDER_CLI_PASS"
        elif lp or lpstat:
            evidence = "REAL_PROVIDER_PARTIAL"
        else:
            evidence = "EXTERNAL_PROVIDER_PENDING"
        return {
            "cups_client": bool(lpstat or lp),
            "ipptool": bool(ipptool),
            "printers": cups_printers,
            "PHYSICAL_PRINTER_VALIDATION_PENDING": True,
            "evidence_class": evidence,
            "si_packet": str(self.root / "PHYSICAL_PRINTER_SI_PACKET.json"),
        }

    def submit(self, document: Path, *, printer: Optional[str] = None) -> dict:
        document = Path(document)
        if not document.exists():
            return {"ok": False, "evidence_class": "BLOCKED", "reason": "missing_document"}
        disc = self.discover()
        lp = shutil.which("lp")
        job_id = f"job_{int(time.time()*1000)}"
        out = self.root / "output" / f"{job_id}.pdf"
        # Always retain digital integrity copy
        data = document.read_bytes()
        out.write_bytes(data)
        if lp and disc["printers"]:
            dest = printer or disc["printers"][0]
            proc = subprocess.run(
                [lp, "-d", dest, str(document)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            ok = proc.returncode == 0
            self.jobs[job_id] = {
                "job_id": job_id,
                "printer": dest,
                "document": str(document),
                "state": "submitted_cups" if ok else "error",
                "cups_stdout": (proc.stdout or "")[:200],
            }
            return {
                "ok": ok,
                "job": self.jobs[job_id],
                "output": str(out),
                "sha256": hashlib.sha256(data).hexdigest(),
                "PHYSICAL_PRINTER_VALIDATION_PENDING": True,
                "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
            }
        # No CUPS queue: fail closed for REAL print; keep integrity artifact for SI prep
        self.jobs[job_id] = {
            "job_id": job_id,
            "printer": "NONE",
            "document": str(document),
            "state": "no_cups_queue",
        }
        return {
            "ok": False,
            "job": self.jobs[job_id],
            "output": str(out),
            "sha256": hashlib.sha256(data).hexdigest(),
            "PHYSICAL_PRINTER_VALIDATION_PENDING": True,
            "evidence_class": "EXTERNAL_PROVIDER_PENDING",
            "reason": "cups_queue_absent_fail_closed_not_byte_copy_pass",
        }

    def cancel(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "reason": "missing"}
        cancel = shutil.which("cancel")
        if cancel and job.get("printer") not in (None, "NONE"):
            subprocess.run([cancel, job_id], capture_output=True, text=True, timeout=10, check=False)
        job["state"] = "cancelled"
        return {"ok": True, "job": job, "evidence_class": "REAL_PROVIDER_PARTIAL"}
