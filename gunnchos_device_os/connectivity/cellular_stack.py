"""Open/free Linux cellular software stack abstraction (Cont VII §44).

Integrates ModemManager / libmbim / libqmi / NetworkManager-equivalent surfaces
against the RM520N-GL simulated fixture. Physical attach remains pending.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from gunnchos_device_os.connectivity.modem_rm520n import ModemManagerFacade, SimulatedRM520NGL

CLAIM_BOUNDARY = (
    "Digital cellular software stack abstraction only. No physical modem attach, "
    "no carrier acceptance, no NTN claim on terrestrial RM520N-GL."
)

STACK_COMPONENTS = (
    {"id": "modemmanager", "role": "modem_lifecycle", "required": True},
    {"id": "libmbim", "role": "mbim_transport", "required": True},
    {"id": "libqmi", "role": "qmi_transport", "required": False},
    {"id": "networkd_or_nm", "role": "ip_bearer_bringup", "required": True},
)


@dataclass
class CellularSoftwareStack:
    modem: SimulatedRM520NGL = field(default_factory=SimulatedRM520NGL)
    facade: ModemManagerFacade = field(init=False)
    nm_connected: bool = False

    def __post_init__(self) -> None:
        self.facade = ModemManagerFacade(modem=self.modem)

    def probe_components(self) -> dict[str, Any]:
        return {
            "components": list(STACK_COMPONENTS),
            "selected_transport": self.modem.state.transport,
            "redundant_skipped": ["duplicate_nm_and_networkd_both"],
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

    def enumerate_and_attach(self) -> dict[str, Any]:
        enum = self.modem.enumerate()
        # Prefer MBIM path; QMI remains available
        self.modem.state.transport = "mbim"
        attach = self.facade.full_attach()
        self.nm_connected = bool(attach.get("ok"))
        return {
            "ok": bool(attach.get("ok")),
            "enumerate": enum,
            "attach": attach,
            "ip_bringup": {"via": "networkd_or_nm", "connected": self.nm_connected},
            "ntn_claimed": False,
            "physical_attach": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
            "simulated": True,
        }

    def handover_matrix(self) -> dict[str, Any]:
        """Wi-Fi → terrestrial cellular → Ethernet → simulated NTN handoff path."""
        path = ["wifi", "terrestrial", "ethernet", "ntn_simulated"]
        return {
            "ok": True,
            "path": path,
            "future_ntn_separate": True,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe_components(),
            "modem": asdict(self.modem.state),
            "nm_connected": self.nm_connected,
        }
