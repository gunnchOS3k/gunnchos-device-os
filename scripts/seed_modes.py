#!/usr/bin/env python3
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

MODES = [
    "school", "developer", "play", "research_measurement", "fleet_admin", "accessibility",
    "low_bandwidth", "offline_learning", "crisis_privacy", "community_kiosk", "repair_diagnostics",
    "gunnchai_tutor", "waike_lesson", "edge_io_measurement", "seven_gc_export",
    "airan_lab", "beam_lab", "ntn_lab",
]
ROOT = Path(__file__).resolve().parents[1]


def mode_doc(mode_id: str) -> dict:
    return {
        "mode_id": mode_id,
        "allowed_apps": ["launcher", "waike", "gunnchai"],
        "blocked_apps": [],
        "network_policy": "school_safe",
        "telemetry_policy": "aggregate_opt_in",
        "privacy_policy": "strict",
        "input_latency_profile": "balanced",
        "power_profile": "efficiency",
        "display_profile": "standard",
        "accessibility_profile": "default",
        "offline_behavior": "cache_lessons",
        "sync_behavior": "deferred",
        "failure_behavior": "safe_fallback",
    }


def main() -> None:
    d = ROOT / "configs/modes"
    d.mkdir(parents=True, exist_ok=True)
    for m in MODES:
        body = yaml.dump(mode_doc(m), sort_keys=False) if yaml else str(mode_doc(m))
        (d / f"{m}.yaml").write_text(body, encoding="utf-8")
    print(f"Wrote {len(MODES)} mode configs")


if __name__ == "__main__":
    main()
