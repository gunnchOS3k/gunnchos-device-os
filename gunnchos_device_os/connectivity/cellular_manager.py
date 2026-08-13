"""Cellular manager — SIM/eSIM *interface*, APN, registration, IP/DNS, airplane, recovery.

Digital / simulated software path. Real eSIM and carrier credentials are
EXTERNAL and are never generated, stored, or accepted as in-repo secrets.
Quectel RM520N-GL remains a terrestrial 5G NR Sub-6 + LTE fixture only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from gunnchos_device_os.connectivity.honest_tokens import (
    CARRIER_ACCEPTED,
    CLAIM_BOUNDARY,
    LIVE_CARRIER_ATTACH,
    REAL_CARRIER_CREDENTIALS,
    REAL_ESIM_CREDENTIALS,
    RM520N_GL_NTN,
    STANDARDIZED_6G,
    honest_tokens,
)
from gunnchos_device_os.connectivity.modem_rm520n import SimulatedRM520NGL


class RegistrationState(str, Enum):
    IDLE = "idle"
    SEARCHING = "searching"
    REGISTERED_HOME = "registered_home"
    REGISTERED_ROAMING = "registered_roaming"
    DENIED = "denied"
    AIRPLANE = "airplane"
    RECOVERING = "recovering"


class PdnType(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    IPV4V6 = "ipv4v6"


@dataclass
class ApnConfig:
    apn: str = "internet"
    pdn_type: PdnType = PdnType.IPV4V6
    user: str | None = None
    password: str | None = None
    auth: str = "none"  # none | pap | chap — software field only

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pdn_type"] = self.pdn_type.value
        d["password_present"] = bool(self.password)
        d["password"] = None  # never serialize secrets
        d["user"] = self.user
        d["credentials_source"] = REAL_CARRIER_CREDENTIALS
        return d


@dataclass
class IpSession:
    ipv4: str | None = None
    ipv6: str | None = None
    dns_v4: list[str] = field(default_factory=list)
    dns_v6: list[str] = field(default_factory=list)
    mtu: int = 1500
    active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SimSlot:
    """Physical SIM *interface* — fixture values are simulated, not operator SIMs."""

    present: bool = True
    ready: bool = False
    pin_required: bool = False
    form: str = "nano-sim"
    iccid: str | None = None
    imsi: str | None = None
    simulated: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "real_operator_sim": False}


@dataclass
class EsimProfileSlot:
    """eSIM profile *slot* — no SM-DP+ credentials live here."""

    slot: int
    enabled: bool = False
    iccid: str | None = None
    nickname: str | None = None
    status: str = "EXTERNAL_PENDING"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EsimInterface:
    """LPA-shaped interface only. Real eSIM/carrier credentials are EXTERNAL."""

    def __init__(self) -> None:
        self.slots: list[EsimProfileSlot] = [EsimProfileSlot(slot=1), EsimProfileSlot(slot=2)]
        self.last_request: dict[str, Any] | None = None

    def list_profiles(self) -> dict[str, Any]:
        return {
            "ok": True,
            "profiles": [s.to_dict() for s in self.slots],
            "active": None,
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "claim_boundary": CLAIM_BOUNDARY,
            "simulated": True,
            "mock": False,
        }

    def request_download(self, activation_code: str | None = None) -> dict[str, Any]:
        """Request a profile download. Never stores or validates real codes."""
        self.last_request = {
            "schema": "gunnchos.connectivity.esim_download_request.v1",
            "activation_code_supplied": bool(activation_code),
            "activation_code": None,  # stripped
            "status": "EXTERNAL_PENDING",
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
        }
        return {
            "ok": False,
            "status": "EXTERNAL_PENDING",
            "reason": "real_esim_credentials_external",
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

    def enable_profile(self, iccid: str) -> dict[str, Any]:
        return {
            "ok": False,
            "iccid": iccid,
            "status": "EXTERNAL_PENDING",
            "reason": "no_in_repo_esim_profile",
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
            "mock": False,
        }


@dataclass
class CellularManager:
    """Software cellular manager over the RM520N-GL simulated fixture."""

    modem: SimulatedRM520NGL = field(default_factory=SimulatedRM520NGL)
    sim: SimSlot = field(default_factory=SimSlot)
    esim: EsimInterface = field(default_factory=EsimInterface)
    apn: ApnConfig = field(default_factory=ApnConfig)
    registration: RegistrationState = RegistrationState.IDLE
    ip: IpSession = field(default_factory=IpSession)
    airplane: bool = False
    recovery_attempts: int = 0
    last_error: str | None = None

    def claim_boundary(self) -> str:
        return CLAIM_BOUNDARY

    def set_airplane(self, enabled: bool) -> dict[str, Any]:
        self.airplane = bool(enabled)
        if self.airplane:
            self.registration = RegistrationState.AIRPLANE
            self.ip = IpSession()
            self.modem.power_off()
            self.sim.ready = False
        else:
            self.registration = RegistrationState.IDLE
        return {
            "ok": True,
            "airplane": self.airplane,
            "registration": self.registration.value,
            "LIVE_CARRIER_ATTACH": LIVE_CARRIER_ATTACH,
            **honest_tokens(),
        }

    def set_apn(
        self,
        apn: str,
        *,
        pdn_type: str | PdnType = PdnType.IPV4V6,
        user: str | None = None,
        auth: str = "none",
    ) -> dict[str, Any]:
        kind = pdn_type if isinstance(pdn_type, PdnType) else PdnType(pdn_type)
        self.apn = ApnConfig(apn=apn, pdn_type=kind, user=user, auth=auth, password=None)
        return {"ok": True, "apn": self.apn.to_dict(), "CARRIER_ACCEPTED": CARRIER_ACCEPTED}

    def probe_sim(self) -> dict[str, Any]:
        if self.airplane:
            self.sim.ready = False
            return {**self.sim.to_dict(), "reason": "airplane"}
        raw = self.modem.sim_state()
        self.sim.present = bool(raw.get("present"))
        self.sim.ready = bool(raw.get("ready"))
        self.sim.pin_required = bool(raw.get("pin_required"))
        # Fixture identifiers only — labeled simulated.
        self.sim.iccid = raw.get("iccid")
        self.sim.imsi = raw.get("imsi")
        self.sim.simulated = True
        return {
            **self.sim.to_dict(),
            "esim": self.esim.list_profiles(),
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
            "mock": False,
        }

    def register(self, plmn: str = "00101") -> dict[str, Any]:
        if self.airplane:
            self.last_error = "airplane"
            return {"ok": False, "reason": "airplane", "registration": self.registration.value}
        if not self.modem.state.powered:
            self.modem.power_on()
        self.registration = RegistrationState.SEARCHING
        sim = self.probe_sim()
        if not sim.get("ready"):
            self.registration = RegistrationState.DENIED
            self.last_error = "sim_not_ready"
            return {"ok": False, "reason": "sim_not_ready", "registration": self.registration.value}
        result = self.modem.register()
        if not result.get("ok"):
            self.registration = RegistrationState.DENIED
            self.last_error = str(result.get("reason") or "register_failed")
            return {"ok": False, "reason": self.last_error, "registration": self.registration.value}
        self.registration = RegistrationState.REGISTERED_HOME
        return {
            "ok": True,
            "registration": self.registration.value,
            "plmn": result.get("plmn", plmn),
            "tech": result.get("tech"),
            "ntn_claimed": False,
            "RM520N_GL_NTN": RM520N_GL_NTN,
            "LIVE_CARRIER_ATTACH": LIVE_CARRIER_ATTACH,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "simulated": True,
            "mock": False,
        }

    def attach_pdn(self) -> dict[str, Any]:
        if self.airplane:
            return {"ok": False, "reason": "airplane"}
        if self.registration not in (
            RegistrationState.REGISTERED_HOME,
            RegistrationState.REGISTERED_ROAMING,
        ):
            return {"ok": False, "reason": "not_registered"}
        bearer = self.modem.activate_bearer()
        if not bearer.get("ok"):
            self.last_error = str(bearer.get("reason") or "attach_failed")
            return {"ok": False, "reason": self.last_error}
        kind = self.apn.pdn_type
        ipv4 = "10.64.0.2" if kind in (PdnType.IPV4, PdnType.IPV4V6) else None
        ipv6 = "2001:db8:7gc:1::2" if kind in (PdnType.IPV6, PdnType.IPV4V6) else None
        dns_v4 = ["1.1.1.1", "8.8.8.8"] if ipv4 else []
        dns_v6 = ["2001:4860:4860::8888"] if ipv6 else []
        self.ip = IpSession(
            ipv4=ipv4,
            ipv6=ipv6,
            dns_v4=dns_v4,
            dns_v6=dns_v6,
            active=True,
        )
        return {
            "ok": True,
            "apn": self.apn.to_dict(),
            "ip": self.ip.to_dict(),
            "ntn_claimed": False,
            "RM520N_GL_NTN": RM520N_GL_NTN,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "LIVE_CARRIER_ATTACH": LIVE_CARRIER_ATTACH,
            "simulated": True,
            "mock": False,
        }

    def recover(self) -> dict[str, Any]:
        """Detach, re-register, re-attach. Software recovery only."""
        if self.airplane:
            return {"ok": False, "reason": "airplane", "recovery_attempts": self.recovery_attempts}
        self.recovery_attempts += 1
        self.registration = RegistrationState.RECOVERING
        self.ip = IpSession()
        recon = self.modem.reconnect()
        if not recon.get("ok"):
            self.last_error = str(recon.get("reason") or "recover_failed")
            self.registration = RegistrationState.DENIED
            return {
                "ok": False,
                "reason": self.last_error,
                "recovery_attempts": self.recovery_attempts,
                "reconnect": recon,
            }
        self.registration = RegistrationState.REGISTERED_HOME
        attach = self.attach_pdn()
        return {
            "ok": bool(attach.get("ok")),
            "recovery_attempts": self.recovery_attempts,
            "reconnect": recon,
            "attach": attach,
            "registration": self.registration.value,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "simulated": True,
            "mock": False,
        }

    def full_bringup(self) -> dict[str, Any]:
        if self.airplane:
            return {"ok": False, "reason": "airplane", **self.snapshot()}
        self.modem.enumerate()
        self.modem.power_on()
        sim = self.probe_sim()
        reg = self.register()
        att = self.attach_pdn() if reg.get("ok") else {"ok": False, "reason": "skip_attach"}
        ok = bool(sim.get("present") and reg.get("ok") and att.get("ok"))
        return {
            "ok": ok,
            "sim": sim,
            "register": reg,
            "attach": att,
            "esim": self.esim.list_profiles(),
            "STANDARDIZED_6G": STANDARDIZED_6G,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "RM520N_GL_NTN": RM520N_GL_NTN,
            "REAL_ESIM_CREDENTIALS": REAL_ESIM_CREDENTIALS,
            "claim_boundary": CLAIM_BOUNDARY,
            "physical_attach": False,
            "simulated": True,
            "mock": False,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "airplane": self.airplane,
            "registration": self.registration.value,
            "apn": self.apn.to_dict(),
            "ip": self.ip.to_dict(),
            "sim": self.sim.to_dict(),
            "esim": self.esim.list_profiles(),
            "recovery_attempts": self.recovery_attempts,
            "last_error": self.last_error,
            "modem_sku": self.modem.sku,
            "ntn_supported": False,
            "ntn_claimed": False,
            **honest_tokens(),
        }
