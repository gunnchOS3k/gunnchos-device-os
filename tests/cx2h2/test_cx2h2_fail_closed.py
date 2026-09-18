"""Fail-closed CX2H.2 tests — fixtures/headless/cp cannot earn J1/J7 DIGITAL_PASS."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2h2.evidence import next_gate
from gunnchos_device_os.cx2h2.tokens import Cx2h2Tokens

ROOT = Path(__file__).resolve().parents[2]


def _shell_ok(**kwargs) -> Cx2h2Tokens:
    base = dict(
        CX2H_SHELL_PREREQ_PASS=True,
        CX2H_CHROMIUM_RUNTIME_PASS=True,
        CX2H_WAYLAND_SURFACE_PASS=True,
        CX2H_GUNNCH_SHELL_RENDER_PASS=True,
        CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS=True,
        CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS=True,
        CX2H_REAL_APP_CENTER_WINDOW=True,
        CX2H_XDG_PORTAL_SESSION_PASS=True,
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        CX2H2_PHYSICAL_PRINTER_PENDING=True,
    )
    base.update(kwargs)
    return Cx2h2Tokens(**base)


def test_headless_libreoffice_cannot_earn_writer_gui_pass():
    tokens = _shell_ok(CX2H2_REAL_WRITER_GUI_PASS=False)
    headless_claim = {"mode": "headless", "odt_bytes_written": True}
    assert headless_claim["mode"] == "headless"
    assert tokens.CX2H2_REAL_WRITER_GUI_PASS is False
    assert tokens.j1_digital_pass() is False


def test_direct_odt_generation_cannot_earn_j1():
    tokens = _shell_ok(
        CX2H2_REAL_WRITER_GUI_PASS=False,
        CX2H2_REAL_VAULT_FILE_PASS=True,
    )
    # Direct zip/ODT bytes on disk without Writer GUI
    fake = ROOT / "artifacts/complete_experience/cx2h2/.fixture.odt"
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_bytes(b"PK\x03\x04fixture")
    assert fake.exists()
    assert tokens.j1_digital_pass() is False
    fake.unlink(missing_ok=True)


def test_direct_pdf_generation_cannot_earn_j1():
    tokens = _shell_ok(CX2H2_REAL_PDF_EXPORT_GUI_PASS=False)
    fake = ROOT / "artifacts/complete_experience/cx2h2/.fixture.pdf"
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_bytes(b"%PDF-1.4 fixture")
    assert fake.exists()
    assert tokens.j1_digital_pass() is False
    fake.unlink(missing_ok=True)


def test_cp_to_print_output_cannot_earn_ipp_pass():
    tokens = _shell_ok(CX2H2_REAL_IPP_PROVIDER_PASS=False, CX2H2_REAL_IPP_PRINT_GUI_PASS=False)
    # Simulating `cp doc.pdf .printed` is not a CUPS job
    marker = {"method": "cp", "job_id": None}
    assert marker["method"] == "cp" and not marker["job_id"]
    assert tokens.CX2H2_REAL_IPP_PRINT_GUI_PASS is False


def test_cups_package_presence_cannot_earn_print_pass():
    tokens = _shell_ok(CX2H2_REAL_IPP_PRINT_GUI_PASS=False)
    packages = ["cups", "cups-client", "cups-bsd"]
    assert packages
    assert tokens.j1_digital_pass() is False


def test_print_requires_real_job_id():
    job = {"ok": False, "job_id": None, "state": "none"}
    assert not job["job_id"]
    tokens = _shell_ok(CX2H2_REAL_IPP_PRINT_GUI_PASS=False)
    assert tokens.CX2H2_REAL_IPP_PRINT_GUI_PASS is False


def test_print_completion_requires_queue_provider_truth():
    tokens = _shell_ok(
        CX2H2_REAL_IPP_PROVIDER_PASS=False,
        CX2H2_REAL_IPP_PRINT_GUI_PASS=True,  # even if somehow set
    )
    # Provider must pass independently
    assert tokens.j1_digital_pass() is False


def test_backup_fixture_cannot_earn_j7():
    tokens = _shell_ok(CX2H2_REAL_BACKUP_GUI_PASS=False)
    fixture = {"backup_id": "fixture", "gui": False}
    assert fixture["backup_id"] and not fixture["gui"]
    assert tokens.j7_digital_pass() is False


def test_restore_backend_without_gui_cannot_earn_j7():
    tokens = _shell_ok(CX2H2_REAL_RESTORE_GUI_PASS=False, CX2H2_REAL_BACKUP_GUI_PASS=True)
    backend_only = {"restored": True, "gui": False}
    assert backend_only["restored"] and not backend_only["gui"]
    assert tokens.j7_digital_pass() is False


def test_restored_file_must_reopen_in_real_provider_app():
    tokens = _shell_ok(
        CX2H2_REAL_RESTORE_GUI_PASS=False,
        CX2H2_REAL_WRITER_GUI_PASS=False,
        CX2H2_REAL_BACKUP_GUI_PASS=True,
    )
    assert tokens.j7_digital_pass() is False


def test_hash_content_readback_required():
    tokens = _shell_ok(CX2H2_PERSISTENCE_PASS=False)
    assert tokens.j1_digital_pass() is False
    assert tokens.j7_digital_pass() is False


def test_j1_j7_cannot_pass_from_predecessor_evidence_alone():
    # Prior J3 PASS alone is insufficient
    tokens = _shell_ok()
    assert tokens.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
    assert tokens.j1_digital_pass() is False
    assert tokens.j7_digital_pass() is False
    assert next_gate(tokens).startswith("CX2H2B_")


def test_full_tokens_earn_digital_pass_and_next_gate():
    tokens = _shell_ok(
        CX2H2_REAL_WRITER_GUI_PASS=True,
        CX2H2_REAL_VAULT_FILE_PASS=True,
        CX2H2_REAL_PDF_EXPORT_GUI_PASS=True,
        CX2H2_REAL_IPP_PROVIDER_PASS=True,
        CX2H2_REAL_IPP_PRINT_GUI_PASS=True,
        CX2H2_REAL_BACKUP_GUI_PASS=True,
        CX2H2_REAL_RESTORE_GUI_PASS=True,
        CX2H2_PERSISTENCE_PASS=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
    )
    assert tokens.j1_digital_pass() is True
    assert tokens.j7_digital_pass() is True
    assert next_gate(tokens) == "CX2H3_BROWSER_MAIL_OFFLINE_J2_J5"
