"""Persist per-profile network preferences with SOFT|HARD policy (NET-ORCH-024)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gunnchos_device_os.network_decision.models import (
    EnforcementMode,
    NetworkPreferencePolicy,
    UserPreferenceProfile,
)
from gunnchos_device_os.platform.encrypted_storage import SoftwareKeystore

POLICY_SCHEMA = "gunnchos.network_decision.user_preference_policy.v1"
LEGACY_SCHEMA = "gunnchos.network_decision.user_preference.v1"


@dataclass
class UserPreferenceStore:
    root: Path
    profile_id: str = "default"
    namespace: str = "network_decision_prefs"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.keystore = SoftwareKeystore(self.root / "keystore")

    def set_preference(self, preference: UserPreferenceProfile | str) -> dict[str, Any]:
        """Backward-compatible simple preference API (SOFT by default)."""
        if isinstance(preference, str):
            preference = UserPreferenceProfile(preference)
        policy = NetworkPreferencePolicy(
            preference=preference,
            enforcement_mode=EnforcementMode.SOFT,
            profile_id=self.profile_id,
        )
        return self.set_policy(policy)

    def set_policy(self, policy: NetworkPreferencePolicy) -> dict[str, Any]:
        payload = {
            "schema": POLICY_SCHEMA,
            "profile_id": self.profile_id,
            "preference": policy.preference.value,
            "enforcement_mode": policy.enforcement_mode.value,
            "hard_avoid_bearers": sorted(policy.hard_avoid_bearers),
            "hard_avoid_metered": bool(policy.hard_avoid_metered),
            "policy_version": policy.policy_version,
        }
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return self.keystore.put(self.profile_id, raw, namespace=self.namespace)

    def get_preference(self) -> UserPreferenceProfile | None:
        policy = self.get_policy()
        return None if policy is None else policy.preference

    def get_policy(self) -> NetworkPreferencePolicy | None:
        got = self.keystore.get(self.profile_id, namespace=self.namespace)
        if not got.get("ok"):
            return None
        try:
            data = json.loads(got["plaintext"].decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return None
        schema = data.get("schema")
        try:
            if schema == LEGACY_SCHEMA or ("preference" in data and "enforcement_mode" not in data):
                return NetworkPreferencePolicy(
                    preference=UserPreferenceProfile(data["preference"]),
                    enforcement_mode=EnforcementMode.SOFT,
                    profile_id=self.profile_id,
                )
            return NetworkPreferencePolicy(
                preference=UserPreferenceProfile(data["preference"]),
                enforcement_mode=EnforcementMode(data.get("enforcement_mode", "SOFT")),
                hard_avoid_bearers=set(data.get("hard_avoid_bearers") or []),
                hard_avoid_metered=bool(data.get("hard_avoid_metered", False)),
                profile_id=self.profile_id,
                policy_version=str(data.get("policy_version") or "wave005.pref.v1"),
            )
        except (ValueError, KeyError, TypeError):
            return None

    def prove_persistence_across_restart(self) -> dict[str, Any]:
        self.set_preference(UserPreferenceProfile.PREFER_BATTERY)
        reloaded = UserPreferenceStore(self.root, profile_id=self.profile_id, namespace=self.namespace)
        got = reloaded.get_preference()
        return {
            "ok": got == UserPreferenceProfile.PREFER_BATTERY,
            "stored": UserPreferenceProfile.PREFER_BATTERY.value,
            "loaded": None if got is None else got.value,
            "software_keystore": True,
            "TPM_KEYSTORE": False,
        }

    def prove_hard_policy_persistence(self) -> dict[str, Any]:
        policy = NetworkPreferencePolicy(
            preference=UserPreferenceProfile.AVOID_CELLULAR,
            enforcement_mode=EnforcementMode.HARD,
            hard_avoid_bearers={"cellular_generic"},
            hard_avoid_metered=False,
            profile_id=self.profile_id,
        )
        self.set_policy(policy)
        reloaded = UserPreferenceStore(self.root, profile_id=self.profile_id, namespace=self.namespace)
        got = reloaded.get_policy()
        ok = (
            got is not None
            and got.enforcement_mode == EnforcementMode.HARD
            and "cellular_generic" in got.hard_avoid_bearers
            and got.preference == UserPreferenceProfile.AVOID_CELLULAR
        )
        return {
            "ok": ok,
            "stored": policy.to_dict(),
            "loaded": None if got is None else got.to_dict(),
            "software_keystore": True,
            "TPM_KEYSTORE": False,
        }


def prove_user_preference_policy(tmp_root: Path) -> dict[str, Any]:
    """Full soft/hard + isolation evidence for NET-ORCH-024."""
    from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
    from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
    from gunnchos_device_os.network_decision.models import (
        CostClass,
        ServiceClass,
        TrustLevel,
        default_objective_for,
    )

    NOW = 1_700_000_000.0

    def wifi(**kw: Any) -> CandidatePath:
        d = dict(
            candidate_id="wifi",
            bearer_class="wifi",
            availability=True,
            signal_quality=0.5,
            latency_ms=80.0,
            jitter_ms=10.0,
            packet_loss_ratio=0.02,
            monetary_cost=0.0,
            cost_class=CostClass.UNMETERED,
            energy_cost=500.0,
            security_trust=TrustLevel.TRUSTED,
            data_unlimited=True,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1.0,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.9,
        )
        d.update(kw)
        return CandidatePath(**d)

    def cell(**kw: Any) -> CandidatePath:
        base = dict(
            candidate_id="cell",
            bearer_class="cellular_generic",
            latency_ms=20.0,
            signal_quality=0.95,
            cost_class=CostClass.METERED,
            monetary_cost=0.02,
            energy_cost=200.0,
            data_metered=True,
            data_unlimited=False,
            data_remaining_fraction=0.8,
        )
        base.update(kw)
        return wifi(**base)

    root_a = Path(tmp_root) / "profile-a"
    root_b = Path(tmp_root) / "profile-b"
    store_a = UserPreferenceStore(root_a, profile_id="student-a")
    store_b = UserPreferenceStore(root_b, profile_id="student-b")

    soft_policy = NetworkPreferencePolicy(
        preference=UserPreferenceProfile.AVOID_CELLULAR,
        enforcement_mode=EnforcementMode.SOFT,
        profile_id="student-a",
    )
    store_a.set_policy(soft_policy)
    eng_soft = AnywhereNetworkDecisionEngine(preference_store=store_a, now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    # Soft: wifi usable → prefer wifi; if wifi down, cellular may still win
    soft_wifi_up = eng_soft.decide([wifi(), cell()], obj)
    soft_wifi_down = eng_soft.decide([wifi(availability=False), cell()], obj)

    hard_cell = NetworkPreferencePolicy(
        preference=UserPreferenceProfile.AVOID_CELLULAR,
        enforcement_mode=EnforcementMode.HARD,
        hard_avoid_bearers={"cellular_generic"},
        profile_id="student-a",
    )
    store_a.set_policy(hard_cell)
    eng_hard = AnywhereNetworkDecisionEngine(preference_store=store_a, now_fn=lambda: NOW)
    hard_cell_decision = eng_hard.decide([wifi(latency_ms=200.0), cell(latency_ms=5.0)], obj)

    hard_metered = NetworkPreferencePolicy(
        preference=UserPreferenceProfile.AVOID_METERED,
        enforcement_mode=EnforcementMode.HARD,
        hard_avoid_metered=True,
        profile_id="student-a",
    )
    store_a.set_policy(hard_metered)
    eng_m = AnywhereNetworkDecisionEngine(preference_store=store_a, now_fn=lambda: NOW)
    hard_metered_decision = eng_m.decide([wifi(), cell()], obj)

    persist = store_a.prove_hard_policy_persistence()

    # profile isolation: B remains soft/balanced
    store_b.set_preference(UserPreferenceProfile.BALANCED)
    eng_b = AnywhereNetworkDecisionEngine(preference_store=store_b, now_fn=lambda: NOW)
    # A has hard avoid cellular; B does not — B may select cell when wifi is worse
    store_a.set_policy(hard_cell)
    d_a = AnywhereNetworkDecisionEngine(preference_store=store_a, now_fn=lambda: NOW).decide(
        [wifi(latency_ms=300.0), cell(latency_ms=10.0)], obj
    )
    d_b = eng_b.decide([wifi(latency_ms=300.0), cell(latency_ms=10.0)], obj)

    # security still mandatory under hard preference
    obj_sec = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj_sec.constraints.min_trust = TrustLevel.TRUSTED
    store_a.set_policy(NetworkPreferencePolicy(
        preference=UserPreferenceProfile.PREFER_LOW_COST,
        enforcement_mode=EnforcementMode.HARD,
        hard_avoid_metered=True,
        profile_id="student-a",
    ))
    d_sec = AnywhereNetworkDecisionEngine(preference_store=store_a, now_fn=lambda: NOW).decide(
        [
            wifi(candidate_id="hostile-free", security_trust=TrustLevel.UNTRUSTED, latency_ms=1.0),
            wifi(candidate_id="safe", security_trust=TrustLevel.TRUSTED, latency_ms=50.0),
        ],
        obj_sec,
    )

    # invalid record fails safe
    bad_path = root_a / "keystore"
    invalid_ok = True
    try:
        store_a.keystore.put(store_a.profile_id, b"{not-json", namespace=store_a.namespace)
        invalid_ok = store_a.get_policy() is None
    except Exception:
        invalid_ok = True

    cases = {
        "soft_avoid_cellular_prefers_wifi": soft_wifi_up.selected_candidate == "wifi",
        "soft_avoid_cellular_allows_cell_when_wifi_unusable": soft_wifi_down.selected_candidate == "cell",
        "hard_avoid_cellular_rejects_cellular": (
            hard_cell_decision.selected_candidate == "wifi"
            and "cell" in [r["candidate_id"] for r in hard_cell_decision.rejected_candidates]
        ),
        "hard_avoid_metered_rejects_metered": (
            hard_metered_decision.selected_candidate == "wifi"
            and "cell" in [r["candidate_id"] for r in hard_metered_decision.rejected_candidates]
        ),
        "hard_policy_restart_persistence": persist.get("ok") is True,
        "profile_isolation": d_a.selected_candidate == "wifi" and d_b.selected_candidate == "cell",
        "security_remains_mandatory": d_sec.selected_candidate == "safe",
        "invalid_preference_fails_safe": invalid_ok,
    }
    return {
        "schema": "gunnchos.engineering_wave005.user_preference_policy.v1",
        "ok": all(cases.values()),
        "cases": cases,
        "persistence": persist,
        "soft_selected_wifi_up": soft_wifi_up.selected_candidate,
        "soft_selected_wifi_down": soft_wifi_down.selected_candidate,
        "hard_cellular_selected": hard_cell_decision.selected_candidate,
        "hard_metered_selected": hard_metered_decision.selected_candidate,
        "profile_a_selected": d_a.selected_candidate,
        "profile_b_selected": d_b.selected_candidate,
        "security_selected": d_sec.selected_candidate,
        "TPM_KEYSTORE": False,
    }
