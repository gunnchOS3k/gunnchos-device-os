"""CX1 ordinary-user digital foundations tests."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx0 import file_provider as cx0_file
from gunnchos_device_os.cx1.app_center import AppCenter
from gunnchos_device_os.cx1.device_profiles import matrix_document
from gunnchos_device_os.cx1.evidence import write_evidence
from gunnchos_device_os.cx1.home import GunnchHome
from gunnchos_device_os.cx1.identity import IdentityPlane
from gunnchos_device_os.cx1.journeys import JourneyRunner
from gunnchos_device_os.cx1.permissions import PermissionsPlane
from gunnchos_device_os.cx1.vault import Vault
from gunnchos_device_os.cx1 import FULL_COMPLETE_EXPERIENCE_COMPLETE


def test_identity_first_run_session_conformance(tmp_path: Path):
    plane = IdentityPlane(tmp_path / "id")
    result = plane.first_run("Alex", policy_input="School", password="s3cret-pass")
    assert result["cloud_required"] is False
    state = (tmp_path / "id" / "identity_state.json").read_text()
    assert "s3cret-pass" not in state
    session = result["session"]
    for key in ("session_id", "profile_id", "auth_method", "issued_at", "expires_at", "state"):
        assert key in session
    ev = plane.conformance_evidence()
    assert ev["IdentitySession_v1"] is True
    assert ev["UserProfile_v1"] is True
    assert ev["no_plaintext_passwords"] is True

    guest = plane.start_guest()
    assert guest.auth_method == "guest"
    owner_id = result["profile"]["profile_id"]
    switched = plane.switch_profile(owner_id, password="s3cret-pass")
    assert switched.profile_id == owner_id
    plane.lock()
    assert plane.active_session().state == "locked"
    plane.unlock(password="s3cret-pass")
    assert plane.active_session().state == "active"
    # work/school/personal separation
    school = plane.create_profile("School Work", "school", policy_input="School")
    personal = plane.create_profile("Personal", "personal")
    assert "school" in school.data_root
    assert "personal" in personal.data_root
    assert school.data_root != personal.data_root


def test_vault_crud_backup_sync_restart(tmp_path: Path):
    vault = Vault(tmp_path / "vault", removable_root=tmp_path / "usb")
    (tmp_path / "usb").mkdir()
    (tmp_path / "usb" / "stick.txt").write_text("removable")
    vault.write("notes/a.txt", b"hello")
    assert vault.read("notes/a.txt") == b"hello"
    assert "a.txt" in vault.list("notes")
    assert vault.search("a.txt")
    vault.delete("notes/a.txt")
    vault.restore_from_trash("notes/a.txt")
    assert vault.metadata("notes/a.txt")["size"] == 5
    assert vault.free_space()["free"] > 0
    status = vault.provider_status()
    assert status["local"]["available"] is True
    assert status["removable"]["available"] is True
    assert status["cloud"]["available"] is False
    backup = vault.create_backup("b1")
    assert backup["integrity_manifest"] is True
    vault.write("notes/a.txt", b"changed")
    restored = vault.restore_backup("b1", overwrite="replace")
    assert restored["restore_verified"] is True
    assert vault.read("notes/a.txt") == b"hello"
    # sync survives restart
    pending = vault.sync.pending_count()
    assert pending >= 1
    reloaded = Vault(tmp_path / "vault")
    assert reloaded.sync.reload() >= 1
    assert reloaded.sync.reconcile()["reconciled"] >= 1


def test_app_center_lifecycle_and_flatpak_fail_closed(tmp_path: Path):
    apps = AppCenter(tmp_path / "apps")
    assert apps.discover("Test")
    installed = apps.install("org.gunnchos.cx1.testapp")
    assert installed["installed"] is True
    assert apps.launch("org.gunnchos.cx1.testapp")["launched"] is True
    assert apps.update("org.gunnchos.cx1.testapp", "1.2.0")["rollback_available"] is True
    assert apps.uninstall("org.gunnchos.cx1.testapp")["uninstalled"] is True
    health = apps.flatpak_health()
    if not health["available"]:
        assert health["evidence_class"] == "DIGITAL_PARTIAL"


def test_permissions_fail_closed(tmp_path: Path):
    perms = PermissionsPlane(tmp_path / "perms")
    assert perms.file_chooser()["ok"] is True
    # camera grant must fail closed when portal unavailable
    cam = perms.portal_probe["camera"]
    if not cam["available"]:
        try:
            perms.set_permission("app", "camera", "grant")
            raised = False
        except PermissionError:
            raised = True
        assert raised is True
    perms.set_permission("app", "notifications", "grant")
    assert perms.check("app", "notifications") == "grant"
    perms.revoke("app", "notifications")
    assert perms.check("app", "notifications") == "deny"


def test_journeys_1_to_6(tmp_path: Path):
    home = GunnchHome(tmp_path / "home")
    results = JourneyRunner(home).run_all()
    for key, result in results.items():
        assert "evidence_class" in result
        assert result["ok"] is True, f"{key} failed: {result}"
    assert results["journey_6"]["human_verification"] == "HUMAN_A11Y_PENDING"
    assert results["journey_1"]["steps"]["physical_print"] == "PHYSICAL_PENDING"


def test_evidence_and_matrix(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    report = write_evidence(repo, tmp_path / "home")
    assert report["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert (repo / "artifacts" / "complete_experience" / "cx1" / "CX1_EVIDENCE_REPORT.json").exists()
    matrix = matrix_document()
    assert "student_14_5" in matrix["matrix"]
    assert matrix["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False


def test_cx0_scaffolds_still_importable():
    # CX0 remains green / intact
    p = cx0_file.LocalPathFileProvider(root=Path("/tmp"))
    assert p.provider_id.startswith("gunnchos.cx0")
