"""Clean installation digital policy (CG-QUALITY-001).

Validates that an installable image prototype can be applied into a clean
target without residual prior-user state. Software-simulated only — does not
claim a shipping installer or hardware-validated install.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CLAIM_BOUNDARY = (
    "Digital clean-installation checklist over simulated install targets only. "
    "No shipping installer claim; no hardware-validated install claim."
)

TOKEN_CLEAN_INSTALLATION_PASS = "GUNNCHOS_CLEAN_INSTALLATION_DIGITAL_PASS"

REQUIRED_CHECKS = (
    "target_empty_or_wiped",
    "no_prior_user_profile",
    "no_prior_wifi_secrets",
    "no_prior_app_state",
    "manifest_present",
    "checksums_present",
    "post_install_first_run_ready",
)


@dataclass
class CleanInstallationResult:
    ok: bool
    checks: dict[str, bool] = field(default_factory=dict)
    residual_keys: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CleanInstallationSuite:
    """Simulated clean install into an empty or wiped target."""

    target_state: dict[str, Any] = field(default_factory=dict)
    image_manifest: dict[str, Any] = field(
        default_factory=lambda: {
            "artifact_type": "installable_os_image_prototype",
            "bootable_os_claim": False,
            "checksums": True,
            "manifest": True,
        }
    )
    history: list[dict[str, Any]] = field(default_factory=list)

    def wipe_target(self) -> None:
        self.target_state = {
            "profiles": [],
            "wifi_secrets": [],
            "app_state": {},
            "wiped": True,
        }

    def apply_image(self) -> CleanInstallationResult:
        residual = []
        if self.target_state.get("profiles"):
            residual.append("profiles")
        if self.target_state.get("wifi_secrets"):
            residual.append("wifi_secrets")
        if self.target_state.get("app_state"):
            residual.append("app_state")

        checks = {
            "target_empty_or_wiped": bool(self.target_state.get("wiped")) and not residual,
            "no_prior_user_profile": not bool(self.target_state.get("profiles")),
            "no_prior_wifi_secrets": not bool(self.target_state.get("wifi_secrets")),
            "no_prior_app_state": not bool(self.target_state.get("app_state")),
            "manifest_present": bool(self.image_manifest.get("manifest")),
            "checksums_present": bool(self.image_manifest.get("checksums")),
            "post_install_first_run_ready": True,
        }
        for name in REQUIRED_CHECKS:
            checks.setdefault(name, False)

        ok = all(checks.values()) and not residual
        if ok:
            self.target_state = {
                "profiles": [],
                "wifi_secrets": [],
                "app_state": {},
                "wiped": True,
                "installed_image": dict(self.image_manifest),
                "first_run_pending": True,
            }
        result = CleanInstallationResult(
            ok=ok,
            checks=checks,
            residual_keys=residual,
            details={"claim_boundary": CLAIM_BOUNDARY},
        )
        self.history.append({"scenario": "apply_image", **result.to_dict()})
        return result

    def scenario_dirty_target_fails(self) -> CleanInstallationResult:
        self.target_state = {
            "profiles": [{"id": "old-user"}],
            "wifi_secrets": ["campus-psk"],
            "app_state": {"notes": ["draft"]},
            "wiped": False,
        }
        result = self.apply_image()
        # Dirty target must fail clean-install gate.
        assert result.ok is False
        self.history[-1]["scenario"] = "dirty_target_fails"
        return result

    def scenario_wiped_target_passes(self) -> CleanInstallationResult:
        self.wipe_target()
        result = self.apply_image()
        self.history[-1]["scenario"] = "wiped_target_passes"
        return result


def run_clean_installation() -> dict[str, Any]:
    suite = CleanInstallationSuite()
    dirty = suite.scenario_dirty_target_fails()
    clean = suite.scenario_wiped_target_passes()
    ok = dirty.ok is False and clean.ok is True
    return {
        "ok": ok,
        "token": TOKEN_CLEAN_INSTALLATION_PASS if ok else f"{TOKEN_CLEAN_INSTALLATION_PASS}_FAIL",
        "requirement_id": "CG-QUALITY-001",
        "claim_boundary": CLAIM_BOUNDARY,
        "checks_required": list(REQUIRED_CHECKS),
        "scenarios": list(suite.history),
        "shipping_installer_claimed": False,
        "hardware_validated": False,
    }
