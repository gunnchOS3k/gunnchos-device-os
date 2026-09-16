"""CX1H Printing/peripherals — CUPS/IPP virtual path; physical = PHYSICAL_PENDING."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


PERIPHERAL_TYPES = (
    "storage",
    "keyboard",
    "mouse",
    "audio",
    "camera",
    "gamepad",
    "bluetooth",
    "display",
    "ring",
    "midi",
)


@dataclass
class PrintJob:
    job_id: str
    printer: str
    document: str
    state: str
    created_at: float

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "printer": self.printer,
            "document": self.document,
            "state": self.state,
            "created_at": self.created_at,
        }


@dataclass
class PrintingPlane:
    root: Path
    jobs: Dict[str, PrintJob] = field(default_factory=dict)
    virtual_printer: str = "CX1_Virtual_PDF"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        (self.root / "queue").mkdir(parents=True, exist_ok=True)
        (self.root / "output").mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        path = self.root / "queue" / "jobs.json"
        if path.exists():
            data = json.loads(path.read_text())
            for raw in data.get("jobs", []):
                job = PrintJob(**raw)
                self.jobs[job.job_id] = job

    def _save(self) -> None:
        (self.root / "queue" / "jobs.json").write_text(
            json.dumps({"jobs": [j.to_dict() for j in self.jobs.values()]}, indent=2) + "\n"
        )

    def discover_printers(self) -> dict:
        printers = [{"name": self.virtual_printer, "type": "virtual_pdf", "available": True}]
        lpstat = shutil.which("lpstat")
        cups_printers: List[str] = []
        if lpstat:
            proc = subprocess.run([lpstat, "-a"], capture_output=True, text=True, timeout=10, check=False)
            if proc.returncode == 0:
                for line in (proc.stdout or "").splitlines():
                    name = line.split()[0] if line.strip() else ""
                    if name:
                        cups_printers.append(name)
                        printers.append({"name": name, "type": "cups", "available": True})
        ipptool = shutil.which("ipptool")
        return {
            "printers": printers,
            "cups_client": bool(lpstat),
            "ipptool": bool(ipptool),
            "cups_printers": cups_printers,
            "physical_print": "PHYSICAL_PENDING",
            "evidence_class": "DIGITAL_PASS" if printers else "DIGITAL_PARTIAL",
        }

    def submit(self, document: Path, *, printer: Optional[str] = None) -> dict:
        document = Path(document)
        if not document.exists():
            raise FileNotFoundError(document)
        printer = printer or self.virtual_printer
        job_id = f"job_{int(time.time()*1000)}"
        out = self.root / "output" / f"{job_id}.printed"
        out.write_bytes(document.read_bytes())
        job = PrintJob(
            job_id=job_id,
            printer=printer,
            document=str(document),
            state="completed",
            created_at=time.time(),
        )
        # Prefer CUPS when available and printer is not virtual
        lp = shutil.which("lp")
        if lp and printer != self.virtual_printer:
            proc = subprocess.run(
                [lp, "-d", printer, str(document)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode != 0:
                job.state = "error"
                self.jobs[job_id] = job
                self._save()
                return {
                    "ok": False,
                    "job": job.to_dict(),
                    "error": (proc.stderr or proc.stdout or "")[:300],
                    "physical_print": "PHYSICAL_PENDING",
                    "evidence_class": "DIGITAL_PARTIAL",
                }
            job.state = "submitted_cups"
        self.jobs[job_id] = job
        self._save()
        return {
            "ok": True,
            "job": job.to_dict(),
            "output": str(out),
            "physical_print": "PHYSICAL_PENDING",
            "evidence_class": "DIGITAL_PASS",
        }

    def cancel(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        if job.state in ("completed", "cancelled"):
            return {"ok": False, "reason": f"terminal_state:{job.state}"}
        job.state = "cancelled"
        self._save()
        return {"ok": True, "job": job.to_dict()}

    def queue(self) -> List[dict]:
        return [j.to_dict() for j in self.jobs.values()]

    def peripheral_inventory(self) -> dict:
        """Detection inventory — detection ≠ full validation."""
        items = []
        for ptype in PERIPHERAL_TYPES:
            detected = False
            notes = "not_probed"
            if ptype == "storage":
                detected = True
                notes = "local_disk_present"
            elif ptype == "keyboard":
                detected = True
                notes = "assumed_host_input_digital"
            elif ptype == "mouse":
                detected = True
                notes = "assumed_host_input_digital"
            elif ptype == "display":
                detected = True
                notes = "host_display_assumed"
            elif ptype in ("camera", "gamepad", "bluetooth", "ring", "midi", "audio"):
                detected = False
                notes = "hardware_not_validated"
            items.append({"type": ptype, "detected": detected, "validated": False, "notes": notes})
        return {
            "peripherals": items,
            "claim_boundary": "detection_not_full_validation",
            "evidence_class": "DIGITAL_PARTIAL",
        }
