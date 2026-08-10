"""CUPS virtual PDF print backend — wraps accepted Cont IX path."""
from __future__ import annotations

from typing import Any


class PrintBackend:
    def start(self) -> dict[str, Any]:
        from gunnchos_device_os.cont_ix.cups_virtual import evaluate_cups_virtual

        report = evaluate_cups_virtual()
        return {
            "ok": bool(report.get("ok")),
            "cups": report,
            "physical_printer": False,
            "backend": "cups_virtual_pdf",
        }
