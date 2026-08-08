"""RM520N-GL terrestrial modem software path with simulated CI fixture.

Physical modem attach remains pending. This module models ModemManager /
MBIM / QMI enumeration surfaces for digital tests only.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import time


CLAIM_BOUNDARY = (
    "Simulated RM520N-GL software path only. No physical modem, no carrier "
    "attach, no NTN claim. Quectel RM520N-GL is terrestrial 5G sub-6."
)

RM520N_GL_SKUS = ("RM520N-GL",)


@dataclass
class SimState:
    enumerated: bool = False
    powered: bool = False
    sim_present: bool = True
    sim_ready: bool = False
    registered: bool = False
    bearer_active: bool = False
    signal_dbm: float = -95.0
    tech: str = "nr5g-sa"
    band: str = "n78"
    firmware_version: str = "RM520NGLAAR01A01M4G_SIM"
    gnss_enabled: bool = False
    gnss_fix: dict[str, Any] = field(default_factory=dict)
    reconnect_count: int = 0
    last_error: str | None = None
    transport: str = "mbim"  # mbim | qmi | modemmanager


@dataclass
class SimulatedRM520NGL:
    """Deterministic modem fixture for CI / digital validation."""

    device_path: str = "/dev/cdc-wdm0"
    sku: str = "RM520N-GL"
    state: SimState = field(default_factory=SimState)
    ntn_supported: bool = False

    def enumerate(self) -> dict[str, Any]:
        self.state.enumerated = True
        return {
            "ok": True,
            "sku": self.sku,
            "device_path": self.device_path,
            "transports": ["mbim", "qmi", "modemmanager"],
            "ntn_supported": False,
            "ntn_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
            "simulated": True,
        }

    def power_on(self) -> dict[str, Any]:
        if not self.state.enumerated:
            self.enumerate()
        self.state.powered = True
        return {"ok": True, "powered": True, "sku": self.sku}

    def power_off(self) -> dict[str, Any]:
        self.state.powered = False
        self.state.registered = False
        self.state.bearer_active = False
        return {"ok": True, "powered": False}

    def sim_state(self) -> dict[str, Any]:
        if not self.state.sim_present:
            return {"present": False, "ready": False, "imsi": None}
        # Soft unlock for digital fixture
        self.state.sim_ready = self.state.powered
        return {
            "present": True,
            "ready": self.state.sim_ready,
            "imsi": "310260000000001" if self.state.sim_ready else None,
            "iccid": "89014103211118510720" if self.state.sim_ready else None,
            "pin_required": False,
        }

    def signal(self) -> dict[str, Any]:
        return {
            "rsrp_dbm": self.state.signal_dbm,
            "tech": self.state.tech,
            "band": self.state.band,
            "quality": "good" if self.state.signal_dbm > -100 else "fair",
            "ntn": False,
        }

    def register(self) -> dict[str, Any]:
        if not self.state.powered:
            self.state.last_error = "not_powered"
            return {"ok": False, "reason": "not_powered"}
        sim = self.sim_state()
        if not sim["ready"]:
            self.state.last_error = "sim_not_ready"
            return {"ok": False, "reason": "sim_not_ready"}
        self.state.registered = True
        return {
            "ok": True,
            "registered": True,
            "plmn": "310260",
            "tech": self.state.tech,
            "ntn_claimed": False,
        }

    def activate_bearer(self) -> dict[str, Any]:
        if not self.state.registered:
            return {"ok": False, "reason": "not_registered"}
        self.state.bearer_active = True
        return {
            "ok": True,
            "bearer": "terrestrial",
            "apn": "internet",
            "ip": "10.64.0.2",
            "dns": ["1.1.1.1", "8.8.8.8"],
            "ntn_claimed": False,
        }

    def reconnect(self) -> dict[str, Any]:
        self.state.reconnect_count += 1
        self.state.bearer_active = False
        self.state.registered = False
        reg = self.register()
        if not reg.get("ok"):
            return {"ok": False, "reconnect_count": self.state.reconnect_count, **reg}
        bearer = self.activate_bearer()
        return {
            "ok": bool(bearer.get("ok")),
            "reconnect_count": self.state.reconnect_count,
            "register": reg,
            "bearer": bearer,
        }

    def enable_gnss(self, enabled: bool = True) -> dict[str, Any]:
        self.state.gnss_enabled = enabled
        if enabled:
            self.state.gnss_fix = {
                "lat": 30.2672,
                "lon": -97.7431,
                "alt_m": 160.0,
                "fix_source": "simulated",
                "at": time.time(),
            }
        else:
            self.state.gnss_fix = {}
        return {"ok": True, "gnss_enabled": enabled, "fix": dict(self.state.gnss_fix)}

    def diagnostics(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "firmware_version": self.state.firmware_version,
            "transport": self.state.transport,
            "enumerated": self.state.enumerated,
            "powered": self.state.powered,
            "sim": self.sim_state(),
            "signal": self.signal(),
            "registered": self.state.registered,
            "bearer_active": self.state.bearer_active,
            "reconnect_count": self.state.reconnect_count,
            "gnss_enabled": self.state.gnss_enabled,
            "last_error": self.state.last_error,
            "ntn_supported": False,
            "ntn_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "simulated": True,
            "mock": False,
        }

    def firmware_version(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "firmware_version": self.state.firmware_version,
            "ntn_claimed": False,
        }

    def set_transport(self, transport: str) -> dict[str, Any]:
        if transport not in ("mbim", "qmi", "modemmanager"):
            return {"ok": False, "reason": "unsupported_transport"}
        self.state.transport = transport
        return {"ok": True, "transport": transport}

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "device_path": self.device_path,
            "state": asdict(self.state),
            "ntn_supported": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "simulated": True,
            "mock": False,
        }


class ModemManagerFacade:
    """Thin facade mimicking ModemManager / libmbim / libqmi software surface."""

    def __init__(self, modem: SimulatedRM520NGL | None = None) -> None:
        self.modem = modem or SimulatedRM520NGL()

    def list_modems(self) -> list[dict[str, Any]]:
        enum = self.modem.enumerate()
        return [
            {
                "path": self.modem.device_path,
                "sku": self.modem.sku,
                "transport": self.modem.state.transport,
                "ntn_claimed": False,
                **{k: enum[k] for k in ("ok", "simulated", "claim_boundary") if k in enum},
            }
        ]

    def full_attach(self) -> dict[str, Any]:
        steps = [
            self.modem.enumerate(),
            self.modem.power_on(),
            self.modem.sim_state(),
            self.modem.register(),
            self.modem.activate_bearer(),
            self.modem.signal(),
            self.modem.firmware_version(),
        ]
        ok = all(
            (s.get("ok") is True) or (s.get("ready") is True) or ("rsrp_dbm" in s) or ("firmware_version" in s)
            for s in steps
        )
        return {
            "ok": ok,
            "steps": steps,
            "diagnostics": self.modem.diagnostics(),
            "ntn_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
            "simulated": True,
        }
