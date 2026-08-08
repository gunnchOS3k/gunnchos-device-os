"""Device-specific runtime profiles that CHANGE behavior.

Student / DS-XL / Handheld / Dock profiles alter power governor settings,
display topology selection, and AI inference tier — executable policy, not
JSON metadata alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable

from gunnchos_device_os.display_manager import DeviceSurface, DisplayManager
from gunnchos_device_os.performance_governor import get_performance_profile


CLAIM_BOUNDARY = (
    "Software runtime profile controller only. Changes in-process power, "
    "display topology, and AI tier behavior. Not firmware power management "
    "or hardware display controller claims."
)


class DeviceProfileId(str, Enum):
    STUDENT = "student_14_5"
    DS_XL = "ds_xl_coder"
    HANDHELD = "handheld_hybrid"
    DOCK = "dock"


class AiTier(str, Enum):
    TINY_LOCAL = "tiny_local"       # on-device micro models only
    LOCAL = "local"                 # local mid models
    LOCAL_PLUS = "local_plus"       # local high + optional edge
    EDGE_CLOUD = "edge_cloud"       # may use cloud with consent


@dataclass(frozen=True)
class PowerRuntime:
    cpu_cap_percent: int
    gpu_cap_percent: int
    tdp_boost: bool = False
    battery_saver: bool = False
    fan_bias: str = "balanced"  # quiet | balanced | performance

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DisplayTopologyRuntime:
    surface: str
    displays: tuple[str, ...]
    primary: str
    extend: bool = False
    dual_role: str | None = None  # e.g. top_bottom for DS-XL

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "displays": list(self.displays),
            "primary": self.primary,
            "extend": self.extend,
            "dual_role": self.dual_role,
        }


@dataclass(frozen=True)
class AiRuntime:
    tier: AiTier
    max_tokens_per_min: int
    allow_cloud: bool
    model_class: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d


# Executable profile table — values drive RuntimeProfileController decisions.
PROFILE_SPECS: dict[DeviceProfileId, dict[str, Any]] = {
    DeviceProfileId.STUDENT: {
        "power": PowerRuntime(
            cpu_cap_percent=70,
            gpu_cap_percent=50,
            battery_saver=False,
            fan_bias="quiet",
        ),
        "governor": "school",
        "display": DisplayTopologyRuntime(
            surface=DeviceSurface.STUDENT_14_5.value,
            displays=("internal-14.5",),
            primary="internal-14.5",
        ),
        "ai": AiRuntime(
            tier=AiTier.LOCAL,
            max_tokens_per_min=2_000,
            allow_cloud=False,
            model_class="tutor-small",
        ),
    },
    DeviceProfileId.DS_XL: {
        "power": PowerRuntime(
            cpu_cap_percent=100,
            gpu_cap_percent=85,
            tdp_boost=True,
            fan_bias="performance",
        ),
        "governor": "balanced",
        "display": DisplayTopologyRuntime(
            surface=DeviceSurface.DS_XL_CODER.value,
            displays=("ds-xl-top", "ds-xl-bottom"),
            primary="ds-xl-top",
            dual_role="top_bottom",
        ),
        "ai": AiRuntime(
            tier=AiTier.LOCAL_PLUS,
            max_tokens_per_min=8_000,
            allow_cloud=False,
            model_class="coder-mid",
        ),
    },
    DeviceProfileId.HANDHELD: {
        "power": PowerRuntime(
            cpu_cap_percent=50,
            gpu_cap_percent=40,
            battery_saver=True,
            fan_bias="quiet",
        ),
        "governor": "battery_saver",
        "display": DisplayTopologyRuntime(
            surface=DeviceSurface.HANDHELD_HYBRID.value,
            displays=("internal-handheld",),
            primary="internal-handheld",
        ),
        "ai": AiRuntime(
            tier=AiTier.TINY_LOCAL,
            max_tokens_per_min=500,
            allow_cloud=False,
            model_class="assist-tiny",
        ),
    },
    DeviceProfileId.DOCK: {
        "power": PowerRuntime(
            cpu_cap_percent=100,
            gpu_cap_percent=100,
            tdp_boost=True,
            battery_saver=False,
            fan_bias="performance",
        ),
        "governor": "docked_performance",
        "display": DisplayTopologyRuntime(
            surface=DeviceSurface.DOCK.value,
            displays=("internal-handheld", "external-dock"),
            primary="external-dock",
            extend=True,
        ),
        "ai": AiRuntime(
            tier=AiTier.EDGE_CLOUD,
            max_tokens_per_min=20_000,
            allow_cloud=True,
            model_class="assist-edge",
        ),
    },
}


@dataclass
class AppliedRuntime:
    profile_id: str
    power: dict[str, Any]
    governor: dict[str, Any]
    display: dict[str, Any]
    display_manager_event: dict[str, Any]
    ai: dict[str, Any]
    effects: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeProfileController:
    """Apply device profiles so behavior actually changes in-process."""

    display_manager: DisplayManager = field(default_factory=DisplayManager)
    active_profile: DeviceProfileId = DeviceProfileId.HANDHELD
    applied: AppliedRuntime | None = None
    # Mutable runtime knobs that callers/readouts observe
    power_state: dict[str, Any] = field(default_factory=dict)
    ai_state: dict[str, Any] = field(default_factory=dict)
    topology_state: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    _hooks: list[Callable[[AppliedRuntime], None]] = field(default_factory=list, repr=False)

    def on_apply(self, cb: Callable[[AppliedRuntime], None]) -> None:
        self._hooks.append(cb)

    def list_profiles(self) -> list[str]:
        return [p.value for p in DeviceProfileId]

    def spec(self, profile: DeviceProfileId | str) -> dict[str, Any]:
        pid = profile if isinstance(profile, DeviceProfileId) else DeviceProfileId(profile)
        s = PROFILE_SPECS[pid]
        return {
            "profile_id": pid.value,
            "power": s["power"].to_dict(),
            "governor": s["governor"],
            "display": s["display"].to_dict(),
            "ai": s["ai"].to_dict(),
        }

    def apply(self, profile: DeviceProfileId | str) -> dict[str, Any]:
        pid = profile if isinstance(profile, DeviceProfileId) else DeviceProfileId(profile)
        s = PROFILE_SPECS[pid]
        power: PowerRuntime = s["power"]
        display: DisplayTopologyRuntime = s["display"]
        ai: AiRuntime = s["ai"]
        governor_name: str = s["governor"]

        # 1) Power behavior change
        self.power_state = {
            **power.to_dict(),
            "governor": governor_name,
            "effective_cpu_cap": power.cpu_cap_percent,
            "effective_gpu_cap": power.gpu_cap_percent,
        }

        # 2) Governor lookup (existing module) — real call, not JSON dump
        governor = get_performance_profile(governor_name)

        # 3) Display topology via DisplayManager — changes active surface
        dm_event = self.display_manager.apply_surface(display.surface)
        self.topology_state = {
            **display.to_dict(),
            "active_surface": self.display_manager.active_surface.value,
            "backend_active": bool(self.display_manager.backend.current().get("active")),
        }

        # 4) AI tier behavior change
        self.ai_state = {
            **ai.to_dict(),
            "cloud_requests_enabled": ai.allow_cloud,
            "throttle_tokens_per_min": ai.max_tokens_per_min,
        }

        effects = [
            f"power_cpu_cap={power.cpu_cap_percent}",
            f"power_gpu_cap={power.gpu_cap_percent}",
            f"governor={governor_name}",
            f"display_surface={display.surface}",
            f"ai_tier={ai.tier.value}",
            f"ai_cloud={ai.allow_cloud}",
        ]
        applied = AppliedRuntime(
            profile_id=pid.value,
            power=dict(self.power_state),
            governor=governor,
            display=dict(self.topology_state),
            display_manager_event=dm_event,
            ai=dict(self.ai_state),
            effects=effects,
        )
        self.active_profile = pid
        self.applied = applied
        self.history.append(applied.to_dict())
        for cb in self._hooks:
            cb(applied)
        return {
            **applied.to_dict(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def allow_ai_request(self, tokens: int, *, cloud: bool = False) -> dict[str, Any]:
        """Behavior gate driven by active AI tier — not a static JSON read."""
        if not self.ai_state:
            self.apply(self.active_profile)
        limit = int(self.ai_state.get("throttle_tokens_per_min", 0))
        allow_cloud = bool(self.ai_state.get("cloud_requests_enabled", False))
        if cloud and not allow_cloud:
            return {
                "allowed": False,
                "reason": "cloud_disabled_for_profile",
                "profile": self.active_profile.value,
                "mock": False,
            }
        if tokens > limit:
            return {
                "allowed": False,
                "reason": "token_budget_exceeded",
                "limit": limit,
                "requested": tokens,
                "profile": self.active_profile.value,
                "mock": False,
            }
        return {
            "allowed": True,
            "reason": "within_profile_budget",
            "limit": limit,
            "requested": tokens,
            "tier": self.ai_state.get("tier"),
            "profile": self.active_profile.value,
            "mock": False,
        }

    def effective_power_caps(self) -> dict[str, Any]:
        if not self.power_state:
            self.apply(self.active_profile)
        return {
            "cpu_cap_percent": self.power_state["effective_cpu_cap"],
            "gpu_cap_percent": self.power_state["effective_gpu_cap"],
            "tdp_boost": self.power_state.get("tdp_boost", False),
            "battery_saver": self.power_state.get("battery_saver", False),
            "profile": self.active_profile.value,
            "mock": False,
        }

    def status(self) -> dict[str, Any]:
        return {
            "active_profile": self.active_profile.value,
            "power_state": dict(self.power_state),
            "ai_state": dict(self.ai_state),
            "topology_state": dict(self.topology_state),
            "history_len": len(self.history),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
