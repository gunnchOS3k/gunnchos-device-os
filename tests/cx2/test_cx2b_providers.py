"""CX2B — real provider integrations (fail closed, no marker PASS)."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2.shell.product_shell import ProductShell


def test_app_center_real_package_lifecycle(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Apps")
    apps = shell.provider_registry().app_center
    inst = apps.install("org.gunnchos.cx2.testapp", "1.0.0")
    assert inst["installed"] is True
    assert "run.py" in inst["app"]["files_deployed"]
    assert inst.get("deploy_class") == "REAL_PROVIDER_CLI_PASS"
    # No INSTALLED.json marker-as-PASS
    assert not (Path(inst["app"]["storage_path"]) / "INSTALLED.json").exists()
    launch = apps.launch("org.gunnchos.cx2.testapp")
    assert launch["launched"] is True
    assert launch.get("pid")
    assert launch["evidence_class"] == "REAL_PROVIDER_CLI_PASS"
    upd = apps.update("org.gunnchos.cx2.testapp", "2.0.0")
    assert upd["updated"] is True
    rb = apps.rollback("org.gunnchos.cx2.testapp")
    assert rb["rolled_back"] is True
    un = apps.uninstall("org.gunnchos.cx2.testapp")
    assert un["uninstalled"] is True
    assert un["cleanup_complete"] is True


def test_browser_qualification_honest(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Browser")
    report = shell.provider_registry().browser.qualify(allow_gui=False)
    assert report["standardized_default"] is False
    assert report["evidence_class"] in {
        "REAL_PROVIDER_CLI_PASS",
        "REAL_PROVIDER_GUI_PASS",
        "EXTERNAL_PROVIDER_PENDING",
        "REAL_PROVIDER_PARTIAL",
    }
    # Must not claim HTTPS PASS via Python ssl alone without browser
    https = report["checks"]["https_local_tls"]
    assert https.get("notes") != "ssl_context_available"


def test_libreoffice_odf_aware(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Docs")
    prod = shell.provider_registry().productivity
    if not prod.soffice:
        result = prod.create_document("x", "writer")
        assert result["evidence_class"] == "EXTERNAL_PROVIDER_PENDING"
        return
    doc = prod.create_document("essay", "writer", body="CX2 hello world")
    assert doc["ok"] is True
    assert doc["odf_valid_zip"] is True
    assert doc["evidence_class"] == "REAL_PROVIDER_CLI_PASS"
    edited = prod.edit_via_libreoffice("essay", "writer", append=" edited")
    assert edited["ok"] is True
    pdf = prod.export_pdf("essay", "writer")
    assert pdf["ok"] is True
    assert Path(pdf["path"]).read_bytes().startswith(b"%PDF")


def test_mail_caldav_carddav_real_protocols(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Connect")
    connect = shell.provider_registry().connect
    connect.start_local_stack()
    try:
        mail = connect.compose_send_receive(subject="hi", body="body")
        assert mail["ok"] is True
        assert mail["evidence_class"] == "REAL_PROVIDER_CLI_PASS"
        cal = connect.calendar_crud()
        assert cal["ok"] is True
        contacts = connect.contacts_crud()
        assert contacts["ok"] is True
        chat = connect.status_chat_video()
        assert chat["HUMAN_AV_QUALITY_PENDING"] is True
        assert chat["evidence_class"] == "EXTERNAL_PROVIDER_PENDING"
    finally:
        connect.stop()


def test_capture_and_printing_honesty(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Capture")
    cap = shell.provider_registry().capture.screenshot_to_vault("t")
    assert cap["evidence_class"] in {
        "REAL_PROVIDER_GUI_PASS",
        "HUMAN_VALIDATION_PENDING",
        "EXTERNAL_PROVIDER_PENDING",
    }
    # Never claim fixture PNG as PASS
    assert cap.get("mode") != "digital_fixture_capture"
    printing = shell.provider_registry().printing.discover()
    assert printing["PHYSICAL_PRINTER_VALIDATION_PENDING"] is True
    portals = shell.provider_registry().portals.probe()
    assert portals["evidence_class"] in {"REAL_PROVIDER_PARTIAL", "NOT_APPLICABLE"}
