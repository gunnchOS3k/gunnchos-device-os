from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx0.app_provider import discover_portal_capabilities
from gunnchos_device_os.cx0.capability_export import export_capability_registry
from gunnchos_device_os.cx0.continuity_provider import create_continuity_state
from gunnchos_device_os.cx0.file_provider import LocalPathFileProvider
from gunnchos_device_os.cx0.firmware_fwupd import detect_fwupd
from gunnchos_device_os.cx0.peripheral_ipp import detect_print_capabilities
from gunnchos_device_os.cx0.accessibility_inventory import export_accessibility_inventory
from gunnchos_device_os.cx0.support_bundle import SupportBundleBuilder, redact_text
from gunnchos_device_os.cx0.sync_backup import BackupProviderScaffold, SyncProviderScaffold


def test_app_provider_does_not_claim_portal():
    inv = discover_portal_capabilities()
    data = inv.to_dict()
    assert data["xdg_desktop_portal_implemented"] is False
    assert data["claim_boundary"] == "scaffold_only_not_product_store"


def test_file_provider_roundtrip(tmp_path: Path):
    provider = LocalPathFileProvider(root=tmp_path)
    provider.write_bytes("notes/a.txt", b"hello")
    assert provider.read_bytes("notes/a.txt") == b"hello"
    assert "a.txt" in provider.list("notes")


def test_sync_and_backup_roundtrip(tmp_path: Path):
    sync = SyncProviderScaffold()
    sync.enqueue("user_files", {"op": "put", "path": "a.txt"})
    assert sync.pending_count() == 1

    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("payload")
    backup_dir = tmp_path / "backup"
    restore_dir = tmp_path / "restore"
    backup = BackupProviderScaffold()
    meta = backup.backup_tree(src, backup_dir)
    assert meta["restore_verified"] is False
    restored = backup.restore_tree(backup_dir, restore_dir)
    assert restored["restore_verified"] is True
    assert (restore_dir / "a.txt").read_text() == "payload"


def test_ipp_and_fwupd_detection_honest():
    peri = detect_print_capabilities("office_dock").to_dict()
    assert peri["scanner_detect"] is False
    assert "sane_scanner_not_implemented" in peri["notes"]
    fw = detect_fwupd().to_dict()
    assert fw["lvfs_configured"] is False
    assert fw["claim_boundary"].startswith("detection_only")


def test_accessibility_continuity_support_export(tmp_path: Path):
    a11y = export_accessibility_inventory("ds_xl").to_dict()
    assert a11y["atspi_available"] is False
    assert a11y["evidence_tier"] == "digital"

    cont = create_continuity_state("sess-1").to_dict()
    assert cont["tier"] == "digital_sim"

    assert "[REDACTED_EMAIL]" in redact_text("contact me@example.com please")
    builder = SupportBundleBuilder()
    builder.add_text_artifact("journal.txt", "user me@example.com token Bearer abc.def")
    meta = builder.build(tmp_path / "bundle")
    assert meta["contains_pii"] is False
    text = (tmp_path / "bundle" / "journal.txt").read_text()
    assert "me@example.com" not in text
    assert "[REDACTED_EMAIL]" in text

    export = export_capability_registry("handheld_student")
    assert export["schema"].endswith("capability_export.v1")
    assert export["profile_features"]["live_host_probing"] is False
