"""Wave 002 shell coordinator — vertical integration slice."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.shell.continuity_coordinator import ContinuityCoordinator
from gunnchos_device_os.shell.display_dock_manager import DisplayDockManager
from gunnchos_device_os.shell.hal_registry import CapabilityProvenance, HalCapabilityRegistry
from gunnchos_device_os.shell.identity_store import LocalIdentityStore
from gunnchos_device_os.shell.input_routing import InputRoutingService
from gunnchos_device_os.shell.observability import ShellObservability
from gunnchos_device_os.shell.parity_probes import device_lab_profile_labels, run_parity_probes
from gunnchos_device_os.shell.ring_service import RingInputService
from gunnchos_device_os.shell.shell_profiles import ShellProfileService


CLAIM_FLAGS = {
    "HUMAN_E6": False,
    "PHYSICAL_VALIDATION": False,
    "PHYSICAL_RING_E6": False,
    "PHYSICAL_DUAL_PANEL": False,
    "SILICON_EXACT_EMULATION": False,
}


@dataclass
class Wave002ShellCoordinator:
    root: Path
    identity: LocalIdentityStore = field(init=False)
    hal: HalCapabilityRegistry = field(default_factory=HalCapabilityRegistry)
    profiles: ShellProfileService = field(default_factory=ShellProfileService)
    ring: RingInputService = field(default_factory=RingInputService)
    input_routing: InputRoutingService = field(init=False)
    display_dock: DisplayDockManager = field(init=False)
    continuity: ContinuityCoordinator = field(init=False)
    observability: ShellObservability = field(default_factory=ShellObservability)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity = LocalIdentityStore(self.root / "identity")
        self.input_routing = InputRoutingService(store_path=self.root / "input_remaps.json")
        repo_root = Path(__file__).resolve().parents[2]
        self.display_dock = DisplayDockManager(repo_root=repo_root)
        self.continuity = ContinuityCoordinator(self.root / "continuity")

    def bootstrap(self, *, form_factor: str = "handheld") -> dict[str, Any]:
        device_class = {
            "ds_xl": "ds_xl_coder",
            "phone": "handheld_hybrid",
            "desktop": "ds_xl_coder",
            "docked": "handheld_hybrid",
        }.get(form_factor, form_factor)
        ids = self.identity.ensure_local_user(device_class=device_class, profile_id=f"profile-{form_factor}")
        profile = self.profiles.apply_form_factor(form_factor)
        self.observability.emit("bootstrap", "session_start", form_factor=form_factor, session_id=ids["session_id"])
        return {"identity": ids, "profile": profile}

    def run_vertical_slice(self, form_factor: str = "handheld") -> dict[str, Any]:
        boot = self.bootstrap(form_factor=form_factor)
        ids = boot["identity"]
        touch = self.input_routing.deliver("touch", {"kind": "tap", "confidence": 0.9}, form_factor=form_factor)
        cp = self.continuity.checkpoint(
            session_id=ids["session_id"],
            account_id=ids["account_id"],
            device_id=ids["device_id"],
            payload={"form_factor": form_factor, "app": "shell_demo", "progress": 1},
        )
        restored = self.continuity.restore(cp["checkpoint_id"], expected_device_id=ids["device_id"])
        disclosure = self.continuity.disclosure(ids["authorized_devices"])
        parity = run_parity_probes(form_factor, self.profiles.status())
        dsxl = self.display_dock.connect_dsxl_path() if form_factor == "ds_xl" else None
        return {
            "bootstrap": boot,
            "input_touch": touch,
            "checkpoint": cp,
            "restore": restored,
            "disclosure_keys": sorted(disclosure.keys()),
            "parity": parity,
            "dsxl_path": dsxl,
            "hal_status": self.hal.status(),
            "claim_flags": dict(CLAIM_FLAGS),
        }

    def status(self) -> dict[str, Any]:
        return {
            "identity": self.identity.service.status(),
            "hal": self.hal.status(),
            "profiles": self.profiles.status(),
            "ring": self.ring.status(),
            "input": self.input_routing.status(),
            "display_dock": self.display_dock.status(),
            "continuity_checkpoints": len(self.continuity.checkpoints),
            "observability": self.observability.metrics(),
            "device_lab_labels": device_lab_profile_labels(self.display_dock.repo_root or Path(".")),
            "claim_flags": dict(CLAIM_FLAGS),
        }

    def classify_requirements(self) -> dict[str, dict[str, Any]]:
        """Honest per-requirement classification for Wave 002."""
        return {
            "SYS-MISSION-006": {"status": "PARTIAL", "note": "Runtime probes for gunnchAI/WAIKE/shell; not full cross-app UI parity"},
            "OS-PLATFORM-001": {"status": "PASS", "note": "Local-first identity store with persistence + tests"},
            "OS-PLATFORM-002": {"status": "PASS", "note": "HAL registry with provenance enum"},
            "OS-PLATFORM-003": {"status": "PASS", "note": "Six form-factor shell profiles wired to stage2 shell + display manager"},
            "OS-PLATFORM-004": {"status": "PARTIAL", "note": "Ring service integrates authenticated adapter; PHYSICAL_RING_E6=false"},
            "OS-PLATFORM-005": {"status": "PASS", "note": "Normalized routing touch/controller/kbm/ring with remap persistence"},
            "OS-PLATFORM-006": {"status": "PARTIAL", "note": "Display/dock manager + DS-XL evidence link; dual compositor UX pass false"},
            "OS-PLATFORM-007": {"status": "PASS", "note": "Continuity checkpoint/restore/revoke/conflict"},
            "OS-CONTINUITY-002": {"status": "PASS", "note": "Disclosure: what is synchronized"},
            "OS-CONTINUITY-003": {"status": "PASS", "note": "Disclosure: storage location"},
            "OS-CONTINUITY-004": {"status": "PASS", "note": "Disclosure: authorized devices"},
            "OS-CONTINUITY-005": {"status": "PASS", "note": "Disclosure: local-only fields"},
            "OS-CONTINUITY-006": {"status": "PASS", "note": "Disclosure + revoke API"},
            "OS-CONTINUITY-007": {"status": "PASS", "note": "Export/delete API"},
        }
