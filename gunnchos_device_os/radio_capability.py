"""Device radio capability profiles — profile-driven, no fictional modems.

Derives bearer capability from hardware_compat device manifests. Cellular and
NTN entries are *capability classes* (generic / simulated), never named carrier
modems or marketing SKUs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from gunnchos_device_os.hardware_manifest_loader import list_device_ids, load_device_profile


CLAIM_BOUNDARY = (
    "Radio capability profiles are software descriptors derived from device "
    "manifests. No live modem control, no SIM/eSIM provisioning, no carrier "
    "attach, no NTN certification, no named commercial modem SKU."
)

# Known Wi-Fi class tags used in manifests — capability tags, not chip vendors.
WIFI_CLASS_TAGS = frozenset({"wifi_4", "wifi_5", "wifi_6", "wifi_6e", "wifi_7", "unknown"})


class CellularClass(str, Enum):
    """Generic cellular capability class — not a modem product name."""

    NONE = "none"
    SIMULATED_GENERIC = "simulated_generic"  # software path only
    PROFILE_DECLARED = "profile_declared"  # manifest says cellular_capable


class NtnClass(str, Enum):
    NONE = "none"
    SIMULATED = "simulated"  # research/sim path only


@dataclass(frozen=True)
class BearerCapability:
    """What a device claims it can expose as a bearer path."""

    bearer: str
    supported: bool
    class_tag: str = ""
    requires_dock: bool = False
    simulated_only: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RadioCapabilityProfile:
    """Per-device radio/path capability surface for the connectivity orchestrator."""

    device_id: str
    wifi_class: str = "unknown"
    ethernet_dock: bool = False
    offline_capable: bool = True
    cellular_class: CellularClass = CellularClass.NONE
    ntn_class: NtnClass = NtnClass.NONE
    # Relative defaults used when metrics are not yet observed (not live RF).
    default_cost_hints: dict[str, float] = field(default_factory=dict)
    default_energy_hints_mw: dict[str, float] = field(default_factory=dict)
    claim_boundary: str = CLAIM_BOUNDARY

    def bearers(self) -> list[BearerCapability]:
        out = [
            BearerCapability(
                bearer="wifi",
                supported=bool(self.wifi_class and self.wifi_class != "none"),
                class_tag=self.wifi_class or "unknown",
            ),
            BearerCapability(
                bearer="ethernet",
                supported=self.ethernet_dock,
                class_tag="dock_ethernet",
                requires_dock=True,
                notes="Ethernet only when dock path is present in profile",
            ),
            BearerCapability(
                bearer="cellular",
                supported=self.cellular_class != CellularClass.NONE,
                class_tag=self.cellular_class.value,
                simulated_only=self.cellular_class == CellularClass.SIMULATED_GENERIC,
                notes="Generic cellular class — not a named modem",
            ),
            BearerCapability(
                bearer="ntn_simulated",
                supported=self.ntn_class == NtnClass.SIMULATED,
                class_tag=self.ntn_class.value,
                simulated_only=True,
                notes="NTN is simulated research path only",
            ),
            BearerCapability(
                bearer="offline",
                supported=self.offline_capable,
                class_tag="store_and_forward",
            ),
        ]
        return out

    def supported_bearer_names(self) -> list[str]:
        return [b.bearer for b in self.bearers() if b.supported]

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "wifi_class": self.wifi_class,
            "ethernet_dock": self.ethernet_dock,
            "offline_capable": self.offline_capable,
            "cellular_class": self.cellular_class.value,
            "ntn_class": self.ntn_class.value,
            "bearers": [b.to_dict() for b in self.bearers()],
            "supported_bearers": self.supported_bearer_names(),
            "default_cost_hints": dict(self.default_cost_hints),
            "default_energy_hints_mw": dict(self.default_energy_hints_mw),
            "claim_boundary": self.claim_boundary,
            "mock": False,
        }


def _default_cost_hints(cellular: CellularClass, ntn: NtnClass) -> dict[str, float]:
    hints = {
        "wifi": 0.0,
        "ethernet": 0.0,
        "offline": 0.0,
    }
    if cellular != CellularClass.NONE:
        hints["cellular"] = 0.45
    if ntn == NtnClass.SIMULATED:
        hints["ntn_simulated"] = 0.85
    return hints


def _default_energy_hints(cellular: CellularClass, ntn: NtnClass) -> dict[str, float]:
    hints = {
        "wifi": 400.0,
        "ethernet": 150.0,
        "offline": 1.0,
    }
    if cellular != CellularClass.NONE:
        hints["cellular"] = 900.0
    if ntn == NtnClass.SIMULATED:
        hints["ntn_simulated"] = 1200.0
    return hints


def _parse_cellular(raw_network: dict[str, Any]) -> CellularClass:
    """Parse cellular capability without inventing a modem brand."""
    if not raw_network.get("cellular_capable", False) and not raw_network.get("cellular"):
        return CellularClass.NONE
    value = raw_network.get("cellular", "simulated_generic")
    if value in (True, "true", "yes"):
        return CellularClass.SIMULATED_GENERIC
    if isinstance(value, str):
        lowered = value.lower().strip()
        # Reject accidental brand/SKU injection in manifests.
        banned = ("qualcomm", "mediatek", "sierra", "telit", "quectel", "verizon", "t-mobile")
        if any(b in lowered for b in banned):
            raise ValueError(
                f"cellular class must be generic (got {value!r}); "
                "do not encode commercial modem/carrier brands"
            )
        if lowered in ("none", "false", "no", ""):
            return CellularClass.NONE
        if lowered in ("simulated_generic", "generic", "simulated"):
            return CellularClass.SIMULATED_GENERIC
        if lowered == "profile_declared":
            return CellularClass.PROFILE_DECLARED
    if raw_network.get("cellular_capable"):
        return CellularClass.SIMULATED_GENERIC
    return CellularClass.NONE


def _parse_ntn(raw_network: dict[str, Any]) -> NtnClass:
    value = raw_network.get("ntn", raw_network.get("ntn_class", "none"))
    if value in (True, "true", "simulated", "sim"):
        return NtnClass.SIMULATED
    if isinstance(value, str) and value.lower() in ("simulated", "sim"):
        return NtnClass.SIMULATED
    if raw_network.get("ntn_simulated"):
        return NtnClass.SIMULATED
    return NtnClass.NONE


def radio_profile_from_device(device_id: str) -> RadioCapabilityProfile:
    """Build radio capability profile from a hardware_compat device manifest."""
    profile = load_device_profile(device_id)
    raw_net = dict(profile.raw.get("network") or {})
    wifi = (raw_net.get("wifi") or profile.network.wifi or "unknown").lower()
    if wifi not in WIFI_CLASS_TAGS and wifi != "none":
        # Allow forward-compatible tags but keep them non-branded.
        if any(x in wifi for x in ("qualcomm", "broadcom", "intel", "mediatek")):
            raise ValueError(f"wifi class must be a standard tag, not a chip brand: {wifi}")
    ethernet_dock = bool(
        raw_net.get("ethernet_dock_optional")
        or raw_net.get("ethernet_dock")
        or (profile.dock.supported and raw_net.get("ethernet", False))
    )
    # Dock-supported student/dev devices historically imply optional dock ethernet
    # when ethernet_dock_optional is set in YAML; also honor dock.supported + flag.
    if profile.dock.supported and raw_net.get("ethernet_dock_optional"):
        ethernet_dock = True

    cellular = _parse_cellular(raw_net)
    ntn = _parse_ntn(raw_net)
    offline = bool(raw_net.get("offline_capable", profile.network.offline_capable))

    return RadioCapabilityProfile(
        device_id=device_id,
        wifi_class=wifi if wifi else "unknown",
        ethernet_dock=ethernet_dock,
        offline_capable=offline,
        cellular_class=cellular,
        ntn_class=ntn,
        default_cost_hints=_default_cost_hints(cellular, ntn),
        default_energy_hints_mw=_default_energy_hints(cellular, ntn),
    )


def list_radio_profiles() -> dict[str, RadioCapabilityProfile]:
    return {did: radio_profile_from_device(did) for did in list_device_ids()}


def radio_capability_matrix() -> dict[str, Any]:
    """Matrix for NET-ORCH bearer capability tests / reports."""
    profiles = list_radio_profiles()
    return {
        "devices": {did: p.to_dict() for did, p in profiles.items()},
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
    }
