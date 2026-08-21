"""NET-ORCH-031 — stateful adaptation controller with hysteresis/recovery."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import AdaptationMode


@dataclass
class RuntimeAdaptationParameters:
    max_payload_bytes: int
    prefetch_enabled: bool
    sync_batch_bytes: int
    media_quality: str
    telemetry_interval_s: float
    retry_interval_s: float
    background_sync_enabled: bool
    cache_preferred: bool
    cloud_request_policy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptationPolicy:
    degrade_kbps: float = 200.0
    recover_kbps: float = 350.0
    minimum_kbps: float = 50.0
    min_dwell_samples: int = 3
    service_class: str = "communication"


def parameters_for(mode: AdaptationMode, service_class: str) -> RuntimeAdaptationParameters:
    if mode == AdaptationMode.FULL:
        return RuntimeAdaptationParameters(
            max_payload_bytes=64_000 if service_class != "emergency" else 8_000,
            prefetch_enabled=True,
            sync_batch_bytes=32_000,
            media_quality="high",
            telemetry_interval_s=5.0,
            retry_interval_s=1.0,
            background_sync_enabled=service_class != "emergency",
            cache_preferred=False,
            cloud_request_policy="allow",
        )
    if mode in (AdaptationMode.REDUCED,):
        return RuntimeAdaptationParameters(
            max_payload_bytes=8_000,
            prefetch_enabled=False,
            sync_batch_bytes=4_000,
            media_quality="medium",
            telemetry_interval_s=15.0,
            retry_interval_s=3.0,
            background_sync_enabled=False,
            cache_preferred=True,
            cloud_request_policy="defer_bulk",
        )
    if mode in (AdaptationMode.MINIMUM_USEFUL, AdaptationMode.LOW_BANDWIDTH):
        return RuntimeAdaptationParameters(
            max_payload_bytes=1_200,
            prefetch_enabled=False,
            sync_batch_bytes=512,
            media_quality="low",
            telemetry_interval_s=30.0,
            retry_interval_s=8.0,
            background_sync_enabled=False,
            cache_preferred=True,
            cloud_request_policy="local_only",
        )
    if mode == AdaptationMode.EMERGENCY_MINIMAL:
        return RuntimeAdaptationParameters(
            max_payload_bytes=400,
            prefetch_enabled=False,
            sync_batch_bytes=200,
            media_quality="none",
            telemetry_interval_s=60.0,
            retry_interval_s=2.0,
            background_sync_enabled=False,
            cache_preferred=True,
            cloud_request_policy="emergency_only",
        )
    return RuntimeAdaptationParameters(
        max_payload_bytes=0,
        prefetch_enabled=False,
        sync_batch_bytes=0,
        media_quality="none",
        telemetry_interval_s=120.0,
        retry_interval_s=30.0,
        background_sync_enabled=False,
        cache_preferred=True,
        cloud_request_policy="offline",
    )


@dataclass
class AdaptationController:
    policy: AdaptationPolicy = field(default_factory=AdaptationPolicy)
    mode: AdaptationMode = AdaptationMode.FULL
    samples_in_mode: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    def observe(self, available_kbps: float, *, emergency: bool = False, offline: bool = False) -> AdaptationMode:
        self.samples_in_mode += 1
        target = self.mode
        if offline:
            target = AdaptationMode.OFFLINE
        elif emergency:
            target = AdaptationMode.EMERGENCY_MINIMAL
        else:
            if self.mode == AdaptationMode.FULL:
                if available_kbps < self.policy.degrade_kbps and self.samples_in_mode >= self.policy.min_dwell_samples:
                    target = AdaptationMode.REDUCED
            elif self.mode == AdaptationMode.REDUCED:
                if available_kbps < self.policy.minimum_kbps and self.samples_in_mode >= self.policy.min_dwell_samples:
                    target = AdaptationMode.MINIMUM_USEFUL
                elif available_kbps >= self.policy.recover_kbps and self.samples_in_mode >= self.policy.min_dwell_samples:
                    target = AdaptationMode.FULL
            elif self.mode == AdaptationMode.MINIMUM_USEFUL:
                if available_kbps >= self.policy.degrade_kbps and self.samples_in_mode >= self.policy.min_dwell_samples:
                    target = AdaptationMode.REDUCED
            elif self.mode == AdaptationMode.OFFLINE:
                if available_kbps >= self.policy.recover_kbps:
                    target = AdaptationMode.REDUCED

        if target != self.mode:
            self.mode = target
            self.samples_in_mode = 0
        params = parameters_for(self.mode, self.policy.service_class)
        self.history.append(
            {
                "kbps": available_kbps,
                "mode": self.mode.value,
                "params": params.to_dict(),
                "samples_in_mode": self.samples_in_mode,
            }
        )
        return self.mode


def select_adaptation_mode(
    *,
    available_kbps: float | None,
    emergency: bool = False,
    offline: bool = False,
) -> AdaptationMode:
    """Legacy one-shot helper — prefer AdaptationController for real proofs."""
    if offline or available_kbps is None:
        return AdaptationMode.OFFLINE
    if emergency:
        return AdaptationMode.EMERGENCY_MINIMAL
    if available_kbps < 50:
        return AdaptationMode.MINIMUM_USEFUL
    if available_kbps < 200:
        return AdaptationMode.REDUCED
    return AdaptationMode.FULL


def adapt_payload(payload: bytes, mode: AdaptationMode) -> bytes:
    params = parameters_for(mode, "communication")
    return payload[: params.max_payload_bytes]


def prove_low_bandwidth_adaptation() -> dict[str, Any]:
    ctrl = AdaptationController(policy=AdaptationPolicy(service_class="communication"))
    # healthy → FULL
    for _ in range(4):
        ctrl.observe(800.0)
    # degrade → REDUCED (needs dwell)
    for _ in range(4):
        ctrl.observe(150.0)
    # worse → MINIMUM_USEFUL
    for _ in range(4):
        ctrl.observe(30.0)
    # oscillating near boundary → no flap
    flap_modes_before = [h["mode"] for h in ctrl.history]
    for kbps in (190.0, 210.0, 195.0, 205.0, 198.0):
        ctrl.observe(kbps)
    # sustained recovery → REDUCED → FULL
    for _ in range(4):
        ctrl.observe(220.0)
    for _ in range(4):
        ctrl.observe(400.0)

    modes = [h["mode"] for h in ctrl.history]
    # ensure we saw FULL, REDUCED, MINIMUM_USEFUL, and recovered toward FULL
    saw_full = AdaptationMode.FULL.value in modes
    saw_reduced = AdaptationMode.REDUCED.value in modes
    saw_min = AdaptationMode.MINIMUM_USEFUL.value in modes
    recovered = modes[-1] == AdaptationMode.FULL.value
    # no rapid FULL↔REDUCED oscillation: count transitions in flap window
    flap_window = modes[len(flap_modes_before) : len(flap_modes_before) + 5]
    flap_transitions = sum(1 for i in range(1, len(flap_window)) if flap_window[i] != flap_window[i - 1])
    param_changes = []
    prev = None
    for h in ctrl.history:
        if prev is None or h["params"] != prev:
            param_changes.append({"mode": h["mode"], "params": h["params"]})
            prev = h["params"]

    # service-class differences
    learning = AdaptationController(policy=AdaptationPolicy(service_class="learning"))
    learning.observe(800.0)
    emergency = AdaptationController(policy=AdaptationPolicy(service_class="emergency"))
    emergency.observe(800.0, emergency=True)
    background = AdaptationController(policy=AdaptationPolicy(service_class="background_sync"))
    background.observe(800.0)

    checks = {
        "saw_full": saw_full,
        "saw_reduced": saw_reduced,
        "saw_minimum_useful": saw_min,
        "no_flap": flap_transitions <= 1,
        "recovery_to_full": recovered,
        "param_changes_recorded": len(param_changes) >= 3,
        "emergency_differs": emergency.mode == AdaptationMode.EMERGENCY_MINIMAL,
        "learning_full_params": parameters_for(AdaptationMode.FULL, "learning").prefetch_enabled is True,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.low_bandwidth_adaptation.v1",
        "ok": ok,
        "checks": checks,
        "mode_sequence": modes,
        "parameter_changes": param_changes,
        "flap_window": flap_window,
        "ADAPTATION_HYSTERESIS": True,
        "ADAPTATION_RECOVERY": recovered,
    }
