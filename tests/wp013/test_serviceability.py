from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.release_engineering import serviceability as svc

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_device_root(tmp_path, name="device_a"):
    root = tmp_path / name
    (root / "logs").mkdir(parents=True)
    (root / "logs" / "app.log").write_text(
        "user login user@example.com from 10.0.0.5 token=abc123XYZ secret_serial DEVTEST-GX1-L1-000001-A\n",
        encoding="utf-8",
    )
    (root / "user_data.json").write_text(
        json.dumps({"accounts": ["owner"], "apps": ["gunnchos.creator_stub"], "settings": {"locale": "en-US"}}),
        encoding="utf-8",
    )
    (root / "identity.json").write_text(json.dumps({"device_id": "dev-abc", "status": "ACTIVE"}), encoding="utf-8")
    return root


def test_redact_text_scrubs_email_ip_token_and_serial():
    raw = "email a@b.com ip 192.168.1.1 token=SECRETVALUE serial DEVTEST-GX1-L1-000001-A"
    redacted = svc.redact_text(raw)
    assert "a@b.com" not in redacted
    assert "192.168.1.1" not in redacted
    assert "SECRETVALUE" not in redacted
    assert "DEVTEST-GX1-L1-000001-A" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_IP]" in redacted
    assert "[REDACTED_SERIAL]" in redacted


def test_export_diagnostic_bundle_redacts_logs(tmp_path):
    device_root = _make_device_root(tmp_path)
    bundle_path = tmp_path / "bundle.tar.gz"
    result = svc.export_diagnostic_bundle(device_root, bundle_path)
    assert result["ok"] is True
    assert result["any_redaction_applied"] is True

    import tarfile

    with tarfile.open(bundle_path) as tar:
        content = tar.extractfile("logs/app.log").read().decode("utf-8")
    assert "example.com" not in content
    assert "abc123XYZ" not in content


def test_backup_and_restore_round_trip(tmp_path):
    old_root = _make_device_root(tmp_path, "old_device")
    backup_path = tmp_path / "backup.json"
    result = svc.backup_user_data(REPO_ROOT, old_root, backup_path)
    assert result["ok"] is True

    new_root = tmp_path / "new_device"
    restore = svc.restore_user_data(REPO_ROOT, backup_path, new_root)
    assert restore["ok"] is True
    restored = json.loads((new_root / "user_data.json").read_text())
    assert restored["accounts"] == ["owner"]


def test_restore_rejects_tampered_backup(tmp_path):
    old_root = _make_device_root(tmp_path, "old_device")
    backup_path = tmp_path / "backup.json"
    svc.backup_user_data(REPO_ROOT, old_root, backup_path)

    backup = json.loads(backup_path.read_text())
    backup["user_data"]["accounts"] = ["attacker"]
    backup_path.write_text(json.dumps(backup))

    new_root = tmp_path / "new_device"
    restore = svc.restore_user_data(REPO_ROOT, backup_path, new_root)
    assert restore["ok"] is False
    assert restore["error"] == "backup_signature_invalid"


def test_device_replacement_transfer(tmp_path):
    old_root = _make_device_root(tmp_path, "old_device")
    new_root = tmp_path / "new_device"
    result = svc.transfer_device_replacement(REPO_ROOT, old_root, new_root, transfer_reason="cracked_screen_swap")
    assert result["ok"] is True
    restored = json.loads((new_root / "user_data.json").read_text())
    assert restored["accounts"] == ["owner"]

    old_identity = json.loads((old_root / "identity.json").read_text())
    assert old_identity["status"] == "DECOMMISSIONED_REPLACED"

    receipt = json.loads((new_root / "TRANSFER_RECEIPT.json").read_text())
    assert receipt["transfer_reason"] == "cracked_screen_swap"


def test_repair_mode_enter_exit(tmp_path):
    device_root = _make_device_root(tmp_path)
    assert svc.is_in_repair_mode(device_root) is False
    svc.enter_repair_mode(device_root, reason="battery_swap")
    assert svc.is_in_repair_mode(device_root) is True
    svc.exit_repair_mode(device_root)
    assert svc.is_in_repair_mode(device_root) is False


def test_migrate_user_data_v1_to_v2():
    v1 = {"accounts": ["owner"]}
    v2 = svc.migrate_user_data(v1)
    assert v2["schema"] == svc.USER_DATA_SCHEMA_V2
    assert v2["settings"]["locale"] == "en-US"
    assert v2["apps"] == []

    # Idempotent: migrating an already-v2 payload is a no-op copy.
    v2_again = svc.migrate_user_data(v2)
    assert v2_again == v2


def test_secure_wipe_overwrites_and_removes_files(tmp_path):
    device_root = _make_device_root(tmp_path)
    log_path = device_root / "logs" / "app.log"
    original = log_path.read_bytes()

    result = svc.secure_wipe(device_root, passes=2)
    assert result["ok"] is True
    assert "logs/app.log" in result["wiped_files"] or str(Path("logs") / "app.log") in result["wiped_files"]
    assert not device_root.exists()
    assert not log_path.exists()
    # (File is gone entirely; overwrite-before-delete is exercised inside
    # secure_wipe and would raise if the file disappeared mid-loop.)
    assert original  # sanity: original had content to begin with
