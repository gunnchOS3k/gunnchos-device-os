"""NET-ORCH-026 — satellite visibility windows with freshness (SIMULATED / DIGITAL_TWIN only)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import (
    SatelliteVisibilityProvenance,
    SatelliteVisibilityWindow,
)


def build_visibility_window(
    *,
    candidate_id: str,
    elevation_deg: float | None,
    satellites_in_view: int,
    window_start_utc: float,
    window_end_utc: float,
    observed_or_generated_at: float,
    max_age_s: float = 30.0,
    provenance: SatelliteVisibilityProvenance = SatelliteVisibilityProvenance.SIMULATED,
    latency_estimate_ms: float | None = 250.0,
    confidence: float = 0.8,
    source: str = "fixtures/satellite_visibility.json",
    source_repo: str = "gunnchos-device-os",
    source_commit: str = "repo-relative",
) -> SatelliteVisibilityWindow:
    if provenance not in (
        SatelliteVisibilityProvenance.SIMULATED,
        SatelliteVisibilityProvenance.DIGITAL_TWIN,
        SatelliteVisibilityProvenance.CONFIGURED_TARGET,
        SatelliteVisibilityProvenance.UNKNOWN,
    ):
        provenance = SatelliteVisibilityProvenance.UNKNOWN
    if elevation_deg is None or satellites_in_view < 0 or window_end_utc < window_start_utc:
        return SatelliteVisibilityWindow(
            candidate_id=candidate_id,
            visible=False,
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
            expected_duration_s=max(0.0, window_end_utc - window_start_utc),
            elevation_deg=elevation_deg,
            latency_estimate_ms=latency_estimate_ms,
            confidence=min(confidence, 0.3),
            observed_or_generated_at=observed_or_generated_at,
            max_age_s=max_age_s,
            source=source,
            source_repo=source_repo,
            source_commit=source_commit,
            provenance=provenance,
            satellites_in_view=max(0, satellites_in_view),
            note="missing/invalid visibility inputs → not visible (never best-case)",
        )
    visible = elevation_deg >= 10.0 and satellites_in_view >= 1
    return SatelliteVisibilityWindow(
        candidate_id=candidate_id,
        visible=visible,
        window_start_utc=window_start_utc,
        window_end_utc=window_end_utc,
        expected_duration_s=window_end_utc - window_start_utc,
        elevation_deg=elevation_deg,
        latency_estimate_ms=latency_estimate_ms,
        confidence=confidence if provenance != SatelliteVisibilityProvenance.UNKNOWN else min(confidence, 0.3),
        observed_or_generated_at=observed_or_generated_at,
        max_age_s=max_age_s,
        source=source,
        source_repo=source_repo,
        source_commit=source_commit,
        provenance=provenance,
        satellites_in_view=satellites_in_view,
    )


# Backward-compatible wrapper
def evaluate_satellite_visibility(
    *,
    elevation_deg: float | None,
    satellites_in_view: int,
    provenance: SatelliteVisibilityProvenance,
    confidence: float = 0.8,
    now: float = 1_700_000_000.0,
    window_start_utc: float | None = None,
    window_end_utc: float | None = None,
    observed_or_generated_at: float | None = None,
    max_age_s: float = 30.0,
    candidate_id: str = "ntn-sim-1",
) -> SatelliteVisibilityWindow:
    start = window_start_utc if window_start_utc is not None else now - 5.0
    end = window_end_utc if window_end_utc is not None else now + 60.0
    observed = observed_or_generated_at if observed_or_generated_at is not None else now
    return build_visibility_window(
        candidate_id=candidate_id,
        elevation_deg=elevation_deg,
        satellites_in_view=satellites_in_view,
        window_start_utc=start,
        window_end_utc=end,
        observed_or_generated_at=observed,
        max_age_s=max_age_s,
        provenance=provenance,
        confidence=confidence,
    )


def prove_satellite_visibility() -> dict[str, Any]:
    now = 1_700_000_100.0
    fresh = build_visibility_window(
        candidate_id="ntn-sim-fresh",
        elevation_deg=35.0,
        satellites_in_view=4,
        window_start_utc=now - 10.0,
        window_end_utc=now + 90.0,
        observed_or_generated_at=now - 1.0,
        provenance=SatelliteVisibilityProvenance.SIMULATED,
    )
    future = build_visibility_window(
        candidate_id="ntn-sim-future",
        elevation_deg=40.0,
        satellites_in_view=3,
        window_start_utc=now + 120.0,
        window_end_utc=now + 240.0,
        observed_or_generated_at=now,
        provenance=SatelliteVisibilityProvenance.SIMULATED,
    )
    expired = build_visibility_window(
        candidate_id="ntn-sim-expired",
        elevation_deg=40.0,
        satellites_in_view=3,
        window_start_utc=now - 200.0,
        window_end_utc=now - 20.0,
        observed_or_generated_at=now - 5.0,
        provenance=SatelliteVisibilityProvenance.DIGITAL_TWIN,
    )
    stale = build_visibility_window(
        candidate_id="ntn-sim-stale",
        elevation_deg=45.0,
        satellites_in_view=5,
        window_start_utc=now - 10.0,
        window_end_utc=now + 90.0,
        observed_or_generated_at=now - 120.0,
        max_age_s=30.0,
        provenance=SatelliteVisibilityProvenance.SIMULATED,
    )
    short_window = build_visibility_window(
        candidate_id="ntn-sim-short",
        elevation_deg=30.0,
        satellites_in_view=2,
        window_start_utc=now - 1.0,
        window_end_utc=now + 5.0,
        observed_or_generated_at=now,
        provenance=SatelliteVisibilityProvenance.SIMULATED,
    )
    unknown = build_visibility_window(
        candidate_id="ntn-unknown",
        elevation_deg=None,
        satellites_in_view=0,
        window_start_utc=now,
        window_end_utc=now + 60.0,
        observed_or_generated_at=now,
        provenance=SatelliteVisibilityProvenance.UNKNOWN,
    )

    checks = {
        "fresh_visible_eligible": fresh.is_visible_now(now) and fresh.can_support_action(30.0, now),
        "future_not_yet": not future.is_visible_now(now),
        "expired_ineligible": not expired.is_visible_now(now),
        "stale_ineligible": not stale.is_fresh(now) and not stale.is_visible_now(now),
        "short_window_blocks_long_action": short_window.is_visible_now(now)
        and not short_window.can_support_action(30.0, now),
        "unknown_not_best_case": not unknown.is_visible_now(now) and unknown.confidence <= 0.3,
        "repo_relative_source": not fresh.source.startswith("/") and "gunnchos" in fresh.source_repo,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.satellite_visibility.v1",
        "ok": ok,
        "checks": checks,
        "fresh": fresh.to_dict(),
        "future": future.to_dict(),
        "expired": expired.to_dict(),
        "stale": stale.to_dict(),
        "short_window": short_window.to_dict(),
        "unknown": unknown.to_dict(),
        "REAL_NTN_MODEM_VALIDATED": False,
        "FIELD_MEASURED_SATELLITE_VISIBILITY": False,
        "allowed_provenance": [p.value for p in SatelliteVisibilityProvenance],
        "SATELLITE_VISIBILITY_WINDOWS": True,
    }
