"""Phase XV residual OS gate E2E + security/accessibility regressions."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "phase_xv"


def test_driver_hal():
    from gunnchos_device_os.phase_xv.driver_hal import DRIVER_CLASSES, DriverHal

    result = DriverHal(ART / "test_hal").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["physical_board_validation"] == "PHYSICAL_PENDING"
    assert set(result["driver_classes"]) == set(DRIVER_CLASSES)
    assert result["frontier_parity_claimed"] is False


def test_audio_media():
    from gunnchos_device_os.phase_xv.audio_media import FORMATS, AlsaPipewireStack

    result = AlsaPipewireStack(ART / "test_audio").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["physical_quality"] == "PHYSICAL_PENDING"
    assert set(result["formats"]) == set(FORMATS)
    assert result["loopback"]["ok"] is True


def test_identity():
    from gunnchos_device_os.phase_xv.identity import IDENTITY_KINDS, UnifiedIdentityPlane

    result = UnifiedIdentityPlane(ART / "test_identity").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["biometric_hw"] == "PHYSICAL_PENDING"
    assert set(result["kinds"]) == set(IDENTITY_KINDS)
    assert result["checks"]["revoke"] is True
    assert result["checks"]["login_blocked"] is True


def test_files_storage():
    from gunnchos_device_os.phase_xv.files_storage import FilesStorage

    result = FilesStorage(ART / "test_storage").e2e(ART)
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["media_endurance"] == "PHYSICAL_PENDING"
    assert result["near_full"]["overflow_denied"] is True
    assert result["failure"]["no_tmp_leftover"] is True
    hh = result["handheld_32g_headroom"]
    assert "required_gb" in hh
    assert hh["safe"] is False  # overhead makes 32G unsafe
    assert (ART / "HANDHELD_32G_HEADROOM.json").exists()
    assert (ART / "NPI_DEFECT-STORAGE-HANDHELD-32G.json").exists()


def test_accessibility():
    from gunnchos_device_os.phase_xv.accessibility import JOURNEYS, AccessibilitySubsystem

    result = AccessibilitySubsystem(ART / "test_a11y").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["human_study"] == "EXTERNAL_PENDING"
    assert set(result["journeys"]) == set(JOURNEYS)


def test_connectivity_5ga():
    from gunnchos_device_os.phase_xv.connectivity_5ga import Connectivity5GA

    result = Connectivity5GA(ART / "test_5ga").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["rm520n_ntn_claimed"] is False
    assert result["handoffs"]["wifi_to_cellular"]["to"] == "cellular"
    assert result["handoffs"]["cellular_to_wifi"]["to"] == "wifi"


def test_ntn_migration():
    from gunnchos_device_os.phase_xv.ntn_migration import NtnMigrationHarness

    result = NtnMigrationHarness(ART / "test_ntn").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["normative_ecosystem"] == "EXTERNAL_PENDING"
    assert result["rm520n_ntn_claimed"] is False
    assert result["future_disabled"]["ok"] is True


def test_performance_power():
    from gunnchos_device_os.phase_xv.performance_power import PROFILES, PerformancePowerPolicy

    result = PerformancePowerPolicy(ART / "test_perf").e2e()
    assert result["ok"] is True
    assert result["digital_policy_complete"] is True
    assert result["exit_state"] == "PHYSICAL_PENDING"
    assert result["physical_metrics_claimed"] is False
    assert set(result["profiles"]) == set(PROFILES)


def test_support_lifecycle():
    from gunnchos_device_os.phase_xv.support_lifecycle import SupportLifecycle

    result = SupportLifecycle(ART / "test_support").e2e()
    assert result["ok"] is True
    assert result["exit_state"] == "DIGITALLY_VALIDATED"
    assert result["business_commitments"] == "EXTERNAL_PENDING"
    assert result["upgrade_skip_denied"] is True
    assert result["bundle"]["ok"] is True


def test_user_experience():
    from gunnchos_device_os.phase_xv.user_experience import JOURNEYS, UserExperience

    result = UserExperience(ART / "test_ux").e2e()
    assert result["ok"] is True
    assert result["digital_defects_closed"] is True
    assert result["exit_state"] == "EXTERNAL_PENDING"
    assert result["human_study"] == "EXTERNAL_PENDING"
    assert set(result["journeys"]["journeys"]) == set(JOURNEYS)


def test_security_regression():
    """Identity revoke + storage quota + claim firewall regression."""
    from gunnchos_device_os import phase_xv
    from gunnchos_device_os.phase_xv.files_storage import StoragePlane
    from gunnchos_device_os.phase_xv.identity import UnifiedIdentityPlane

    assert phase_xv.PHYSICAL_EXECUTION_FREEZE is True
    assert phase_xv.GUNNCHOS_FRONTIER_OS_PARITY is False
    assert phase_xv.FRONTIER_OS_PARITY_CLAIMED is False

    idp = UnifiedIdentityPlane(ART / "sec_identity")
    idp.register("u1", "user", "U", ["owner"], secret="abc")
    sess = idp.login("u1", "abc")
    idp.revoke("u1")
    assert idp.sessions[sess.session_id].state == "revoked"
    try:
        idp.login("u1", "abc")
        assert False, "revoked user must not login"
    except PermissionError:
        pass

    plane = StoragePlane(ART / "sec_storage")
    big = b"z" * (9 * 1024 * 1024)
    denied = plane.atomic_write("user", "too-big.bin", big)
    assert denied["ok"] is False
    assert denied["error"] == "quota_exceeded"


def test_accessibility_regression():
    """Keyboard/controller/Ring journeys remain green; no frontier claim."""
    from gunnchos_device_os import phase_xv
    from gunnchos_device_os.phase_xv.accessibility import AccessibilitySubsystem

    assert phase_xv.GUNNCHOS_FRONTIER_OS_PARITY is False
    result = AccessibilitySubsystem(ART / "a11y_reg").e2e()
    assert result["ok"] is True
    assert result["keyboard"]["ok"] is True
    assert result["controller"]["ok"] is True
    assert result["ring_alt"]["ok"] is True
    assert result["frontier_parity_claimed"] is False


def test_no_frontier_parity_claim():
    from gunnchos_device_os import phase_xv

    assert phase_xv.PHYSICAL_EXECUTION_FREEZE is True
    assert phase_xv.GUNNCHOS_FRONTIER_OS_PARITY is False
    assert phase_xv.FRONTIER_OS_PARITY_CLAIMED is False
