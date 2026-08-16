#!/usr/bin/env python3
"""Targeted delta validation vs BASELINE_V1 accepted mains (no full Product-Use)."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SPINE_REPOS = REPO_ROOT.parent
BASELINE_SHAS = (
    SPINE_REPOS
    / "gunnchos-7gc-ai-ran-field-kit"
    / ".worktrees"
    / "digital-ecosystem-baseline-v1"
    / "program"
    / "digital_ecosystem_baseline_v1"
    / "ACCEPTED_MAIN_SHAS.json"
)
# Fallback: commit-local copy if baseline worktree absent
LOCAL_BASELINE = REPO_ROOT / "artifacts" / "stream_a_pkt_001" / "BASELINE_ACCEPTED_MAIN_SHAS.snapshot.json"


def _rev_parse(path: Path) -> str | None:
    if not path.exists():
        return None
    r = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    return r.stdout.strip() if r.returncode == 0 else None


def _load_baseline() -> dict[str, Any]:
    if BASELINE_SHAS.exists():
        return json.loads(BASELINE_SHAS.read_text(encoding="utf-8"))
    if LOCAL_BASELINE.exists():
        return json.loads(LOCAL_BASELINE.read_text(encoding="utf-8"))
    raise FileNotFoundError("baseline accepted SHAs not found")


def run_delta() -> dict[str, Any]:
    baseline = _load_baseline()
    pins_path = REPO_ROOT / "artifacts" / "product_use" / "OWNER_SHA_PINS.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8")).get("pins", {}) if pins_path.exists() else {}

    rows = []
    for name, meta in (baseline.get("repos") or {}).items():
        accepted = meta["sha"]
        pin = (pins.get(name) or {}).get("sha")
        live = _rev_parse(SPINE_REPOS / name)
        drifted = bool(pin and pin != accepted)
        rows.append(
            {
                "repo": name,
                "baseline_accepted": accepted,
                "rc002_pin": pin,
                "live_origin_main": live,
                "live_matches_baseline": live == accepted if live else None,
                "pin_matches_baseline": pin == accepted if pin else None,
                "behavior_affecting_candidate": drifted,
            }
        )

    affecting = [r for r in rows if r["behavior_affecting_candidate"]]
    # Lightweight digital smokes (no guest)
    waike_eval = SPINE_REPOS / "waike-research-ops" / "artifacts" / "mastery" / "AI_WAIKE_MASTERY_EVAL.json"
    gai_eval = SPINE_REPOS / "gunnchAI3k" / "artifacts" / "waike-mastery" / "AI_WAIKE_MASTERY_EVAL.json"
    smokes: dict[str, Any] = {}
    if waike_eval.exists():
        w = json.loads(waike_eval.read_text(encoding="utf-8"))
        smokes["waike"] = {
            "path": str(waike_eval),
            "WAIKE_AI_STUDENT_CORPUS_DISCOVERY_PASS": w.get("WAIKE_AI_STUDENT_CORPUS_DISCOVERY_PASS"),
            "WAIKE_AI_DIGITAL_MASTERY_PASS": w.get("WAIKE_AI_DIGITAL_MASTERY_PASS"),
        }
    if gai_eval.exists():
        g = json.loads(gai_eval.read_text(encoding="utf-8"))
        smokes["gunnchai"] = {
            "path": str(gai_eval),
            "WAIKE_AI_STUDENT_CORPUS_DISCOVERY_PASS": g.get("WAIKE_AI_STUDENT_CORPUS_DISCOVERY_PASS"),
            "WAIKE_AI_DIGITAL_MASTERY_PASS": g.get("WAIKE_AI_DIGITAL_MASTERY_PASS"),
            "WAIKE_AI_NO_KEY_LEAK_PASS": g.get("WAIKE_AI_NO_KEY_LEAK_PASS"),
        }

    four_game_unchanged = all(
        not r["behavior_affecting_candidate"]
        for r in rows
        if r["repo"]
        in {
            "anime-aggressors",
            "pedestrian-pursuit",
            "archive-of-life-artifact-world",
            "beatlink-party",
            "gunnchos-hardware-industrial-design",
            "gunnchos-device-os",
        }
    )

    full_pu_required = any(
        r["repo"] in {"waike-research-ops", "gunnchAI3k"} and r["behavior_affecting_candidate"] for r in rows
    )

    return {
        "schema": "gunnchos.stream_a.targeted_delta.v1",
        "packet": "STREAM-A-PKT-001",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device_os_base": "a1e11efcb502ce053d755a2539c26d252e216226",
        "baseline_source": str(BASELINE_SHAS if BASELINE_SHAS.exists() else LOCAL_BASELINE),
        "rows": rows,
        "behavior_affecting_repos": [r["repo"] for r in affecting],
        "four_game_and_hw_unchanged_vs_rc002_pins": four_game_unchanged,
        "digital_smokes": smokes,
        "FULL_PRODUCT_USE_CAMPAIGN_RERUN": {
            "required": full_pu_required,
            "executed": False,
            "reason": (
                "WAIKE and/or gunnchAI accepted mains advanced past RC-002 OWNER_SHA_PINS; "
                "persona/guest legs remain OPEN for re-earn at new SHAs. "
                "Four-game owner SHAs unchanged — no game relaunch forced by this delta."
            ),
            "blocker_class": "DIGITAL_OPEN" if full_pu_required else None,
        },
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": (
            "Targeted SHA delta + host digital smokes only. Not a full Product-Use campaign. "
            "Does not re-earn guest persona tokens."
        ),
    }


def main() -> int:
    result = run_delta()
    out = REPO_ROOT / "artifacts" / "stream_a_pkt_001" / "TARGETED_DELTA_VALIDATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "affecting": result["behavior_affecting_repos"], "full_pu_required": result["FULL_PRODUCT_USE_CAMPAIGN_RERUN"]["required"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
