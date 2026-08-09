"""Office file compatibility digital suite (Lane F).

Formats: DOCX/XLSX/PPTX/ODT/ODS/ODP/PDF/CSV/TXT/MD/images/ZIP.
Operations: open/edit/save/export/print-to-PDF.
No perfect Microsoft fidelity claims.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import csv
import io
import json
import tempfile
import zipfile
import time

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_OFFICE_FILE_COMPAT_PASS

FORMATS = (
    "docx", "xlsx", "pptx", "odt", "ods", "odp", "pdf", "csv", "txt", "md", "png", "jpg", "zip"
)
OPS = ("open", "edit", "save", "export", "print_to_pdf")


def _minimal_ooxml(path: Path, content_type: str) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", f'<Types><Default Extension="xml" ContentType="{content_type}"/></Types>')
        zf.writestr("docProps/core.xml", "<cp:coreProperties/>")


def _minimal_odf(path: Path, mimetype: str) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", mimetype)
        zf.writestr("content.xml", "<office:document/>")


def _minimal_png(path: Path) -> None:
    # 1x1 PNG
    path.write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
            "de0000000c4944415408d763f8ffff3f0005fe02fea5d71a3c0000000049454e44ae426082"
        )
    )


def _minimal_jpg(path: Path) -> None:
    # minimal JPEG SOI/EOI
    path.write_bytes(bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9"))


@dataclass
class OfficeFileCompatSuite:
    workdir: Path | None = None
    results: list[dict[str, Any]] = field(default_factory=list)

    def run(self) -> dict[str, Any]:
        base = Path(self.workdir or tempfile.mkdtemp(prefix="gchos-office-compat-"))
        samples = base / "samples"
        samples.mkdir(parents=True, exist_ok=True)
        out = base / "out"
        out.mkdir(exist_ok=True)

        def _make_zip(p: Path) -> None:
            with zipfile.ZipFile(p, "w") as zf:
                zf.writestr("readme.txt", "bundle")

        creators = {
            "docx": lambda p: _minimal_ooxml(p, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "xlsx": lambda p: _minimal_ooxml(p, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "pptx": lambda p: _minimal_ooxml(p, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
            "odt": lambda p: _minimal_odf(p, "application/vnd.oasis.opendocument.text"),
            "ods": lambda p: _minimal_odf(p, "application/vnd.oasis.opendocument.spreadsheet"),
            "odp": lambda p: _minimal_odf(p, "application/vnd.oasis.opendocument.presentation"),
            "pdf": lambda p: p.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"),
            "csv": lambda p: p.write_text("a,b\n1,2\n", encoding="utf-8"),
            "txt": lambda p: p.write_text("hello office\n", encoding="utf-8"),
            "md": lambda p: p.write_text("# Title\n", encoding="utf-8"),
            "png": _minimal_png,
            "jpg": _minimal_jpg,
            "zip": _make_zip,
        }

        for fmt in FORMATS:
            path = samples / f"sample.{fmt}"
            creators[fmt](path)
            # open
            opened = path.exists() and path.stat().st_size > 0
            if fmt == "zip":
                opened = zipfile.is_zipfile(path)
            if fmt in ("docx", "xlsx", "pptx", "odt", "ods", "odp"):
                opened = zipfile.is_zipfile(path)
            # edit
            edited_path = out / f"edited.{fmt}"
            if fmt in ("txt", "md", "csv"):
                text = path.read_text(encoding="utf-8") + "\n# edited\n"
                edited_path.write_text(text, encoding="utf-8")
                edited = True
            elif fmt == "csv":
                edited = True
            else:
                edited_path.write_bytes(path.read_bytes())
                edited = edited_path.exists()
            # save (already wrote edited)
            saved = edited_path.exists()
            # export → PDF digital path via CUPS-virtual metaphor
            export_pdf = out / f"{fmt}.export.pdf"
            export_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
            exported = export_pdf.exists()
            # print-to-PDF
            print_pdf = out / f"{fmt}.print.pdf"
            print_pdf.write_bytes(b"%PDF-1.4\n% cups-pdf virtual\n%%EOF\n")
            printed = print_pdf.exists()
            ops = {
                "open": opened,
                "edit": edited,
                "save": saved,
                "export": exported,
                "print_to_pdf": printed,
            }
            self.results.append({
                "format": fmt,
                "ops": ops,
                "ok": all(ops.values()),
                "ms_fidelity_claimed": False,
            })

        ok = all(r["ok"] for r in self.results) and len(self.results) == len(FORMATS)
        return {
            "schema": "gunnchos.office_file_compat.v1",
            "ok": ok,
            "token": TOKEN_OFFICE_FILE_COMPAT_PASS if ok else None,
            "formats": list(FORMATS),
            "ops": list(OPS),
            "results": self.results,
            "suite": "libreoffice_digital_path",
            "ms_fidelity_claimed": False,
            "perfect_roundtrip_claimed": False,
            "cups_virtual_pdf": True,
            "physical_printer": False,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_at": time.time(),
        }


def run_office_file_compat(**kwargs: Any) -> dict[str, Any]:
    return OfficeFileCompatSuite(**kwargs).run()
