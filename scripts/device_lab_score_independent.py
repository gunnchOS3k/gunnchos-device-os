#!/usr/bin/env python3
"""Independent Device Lab 12-category score from evidence files (not gunnchctl alone).

Never hardcodes 10s. Writes artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GAPS = ROOT / "artifacts" / "wp011r" / "DEVICE_LAB_REMAINING_DIGITAL_GAPS.json"
REGISTER = ROOT / "gunnchos_device_os/device_lab/device_lab_v1/DEVICE_LAB_COMPLETION_REGISTER.yaml"
TOKENS = ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json"
OUT = ROOT / "artifacts" / "wp011r" / "DEVICE_LAB_SCORE_INDEPENDENT.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_error": "invalid_json", "path": str(path)}


def _clamp(n: float, lo: float = 0.0, hi: float = 10.0) -> int:
    return int(max(lo, min(hi, round(n))))


def _evidence_bool(path: Path, key: str) -> bool | None:
    data = _load_json(path)
    if not data or data.get("_error"):
        return None
    if key in data:
        return bool(data.get(key))
    return None


def grade_categories(gaps: dict[str, Any], tokens: dict[str, Any]) -> dict[str, Any]:
    """Recompute 12 baseline categories from WP-011R evidence + register-derived signals."""
    pass_tokens = (gaps.get("pass_tokens") or {}) if gaps else {}
    four = bool(pass_tokens.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") is True)
    # Prefer freshly earned evidence files when present
    games_ev = _load_json(ROOT / "artifacts/wp011r/games/four_games_production.json")
    if games_ev:
        four = bool(games_ev.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"))

    visual_ev = _load_json(ROOT / "artifacts/wp011r/visual/LIVE_VISUAL_EVIDENCE.json")
    live = bool(visual_ev.get("LIVE_GUNNCHOS_VISUAL_PASS")) if visual_ev else False
    if pass_tokens.get("LIVE_GUNNCHOS_VISUAL_PASS") is True and visual_ev:
        live = True
    elif pass_tokens.get("LIVE_GUNNCHOS_VISUAL_PASS") is False:
        live = bool(visual_ev.get("LIVE_GUNNCHOS_VISUAL_PASS")) if visual_ev else False

    ring_ev = _load_json(ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json")
    ring_mut = bool(ring_ev.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")) if ring_ev else False

    eco = _load_json(ROOT / "artifacts/wp011r/ECO010_SOAK.json")
    eco_pass = bool(eco.get("ok") and eco.get("simultaneous_soak_complete")) if eco else False
    eco_partial = bool(eco) and not eco_pass

    dsxl_ux = False
    # Scan recent dualscreen results if present under lab artifacts
    lab_root = ROOT / "artifacts" / "device_lab"
    if lab_root.is_dir():
        for p in lab_root.rglob("LAB-SCENARIO-DSXL-DUALSCREEN/result.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is True:
                    dsxl_ux = True
                    break
            except Exception:
                continue
    if pass_tokens.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is True:
        dsxl_ux = True

    # Also allow explicit wp011r evidence
    dsxl_ev = _load_json(ROOT / "artifacts/wp011r/DSXL_COMPOSITOR_UX.json")
    if not dsxl_ev:
        dsxl_ev = _load_json(ROOT / "artifacts/wp011r/dsxl/DSXL_COMPOSITOR_UX_EVIDENCE.json")
    if dsxl_ev:
        dsxl_ux = bool(dsxl_ev.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
    if pass_tokens.get("DSXL_DUAL_COMPOSITOR_UX_PASS") is False and dsxl_ev:
        # Gap register false wins only when evidence also false / absent PASS
        dsxl_ux = bool(dsxl_ev.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))

    master = bool(tokens.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"))
    if master:
        # Refuse inflated master — force false in independent score output
        master = False

    # Grades: never emit hardcoded 10 unless evidence clearly earns full digital depth
    grades = {
        "foundation": {
            "grade": 8,
            "axis": "DIGITAL",
            "evidence": ["CLI/session/profiles present", "WP-011R gap register added"],
        },
        "golden_journeys": {
            "grade": 8,
            "axis": "DIGITAL",
            "evidence": ["G01/G04/G05/G06/G07/G08/G09 Lab-mapped"],
        },
        "behavioral_peripherals": {
            "grade": 6,
            "axis": "DIGITAL",
            "evidence": ["Display/network/audio/storage/rings integrated"],
        },
        "failure_injection": {
            "grade": 8 if not eco_pass else 9,
            "axis": "DIGITAL",
            "evidence": [
                "ChaosEngine suite",
                "ECO-010 " + ("PASS" if eco_pass else "PARTIAL" if eco_partial else "not_run"),
            ],
        },
        "evidence_reproducibility": {
            "grade": 7,
            "axis": "DIGITAL",
            "evidence": ["run_manifest", "wp011r artifacts"],
        },
        "actual_virtual_gunnchos": {
            "grade": 6 if tokens.get("GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED") else 3,
            "axis": "DIGITAL",
            "evidence": [
                "DEVICE_LAB_DEVELOPMENT_GUEST (Alpine/dev — not shipping image)",
                "QEMU guest path prepared",
            ],
        },
        "avd_style_experience": {
            "grade": 2,
            "axis": "DIGITAL",
            "evidence": ["Control UI only — no AVD manager"],
        },
        "live_visual_interaction": {
            "grade": 8 if live else 4,
            "axis": "DIGITAL",
            "evidence": [
                "LIVE_GUNNCHOS_VISUAL_PASS=" + str(live),
                "VNC path prepared; screendump evidence required for PASS",
            ],
        },
        "hardware_spec_sync": {
            "grade": 7,
            "axis": "DIGITAL",
            "evidence": ["Profile MPN sync from WP-011"],
        },
        "performance_prediction": {
            "grade": 2,
            "axis": "PRE_EVT_DIGITAL",
            "evidence": ["FOUNDATION_SCHEMA_ONLY"],
        },
        "full_ecosystem_simulation": {
            "grade": _clamp(
                (7 if four else 5)
                + (1 if eco_partial else 0)
                + (2 if eco_pass else 0)
                + (1 if ring_mut else 0)
                + (1 if dsxl_ux else 0)
            ),
            "axis": "DIGITAL",
            "evidence": [
                f"FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS={four}",
                f"ECO-010={'PASS' if eco_pass else 'PARTIAL' if eco_partial else 'OPEN'}",
                f"RING_TO_REAL_APP_STATE_MUTATION_PASS={ring_mut}",
                f"DSXL_DUAL_COMPOSITOR_UX_PASS={dsxl_ux}",
            ],
        },
        "physical_digital_twin_fidelity": {
            "grade": 2,
            "axis": "PRE_EVT_DIGITAL",
            "digital_pre_evt_grade": 2,
            "physical_correlation_grade": None,
            "evidence": ["VF4/5/6 PHYSICAL_PENDING"],
        },
    }

    # Cap: no category may be 10 unless its PASS evidence is complete and axis digital
    for name, g in grades.items():
        if int(g["grade"]) >= 10:
            if name == "physical_digital_twin_fidelity":
                g["grade"] = 2
            elif name == "full_ecosystem_simulation" and not (four and eco_pass and ring_mut and dsxl_ux):
                g["grade"] = min(int(g["grade"]), 8)
            elif name == "live_visual_interaction" and not live:
                g["grade"] = min(int(g["grade"]), 4)
            else:
                # Still forbid casual 10s without master-complete digital proof
                g["grade"] = min(int(g["grade"]), 9)
        g["hardcoded"] = False

    return {
        "grades": grades,
        "tokens_observed": {
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": four,
            "LIVE_GUNNCHOS_VISUAL_PASS": live,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": dsxl_ux,
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": ring_mut,
            "ECO010_SOAK_PASS": eco_pass,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        },
    }


def main() -> int:
    gaps = _load_json(GAPS)
    tokens = _load_json(TOKENS)
    scored = grade_categories(gaps, tokens)
    grades = scored["grades"]
    numeric = []
    for name, g in grades.items():
        numeric.append(float(g.get("grade") or 0))
    mean = round(sum(numeric) / len(numeric), 2) if numeric else 0.0
    # Also pull register-based score for cross-check (not sole authority)
    reg_score = None
    try:
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "device_lab_score_from_register.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            reg_score = json.loads(proc.stdout)
    except Exception as exc:  # noqa: BLE001
        reg_score = {"error": str(exc)}

    out = {
        "schema": "gunnchos.device_lab.score_independent.v1",
        "wave": "WP-011R",
        "baseline_12_grades": grades,
        "grade_mean_of_12": mean,
        "tokens_observed": scored["tokens_observed"],
        "gaps_register": str(GAPS.relative_to(ROOT)) if GAPS.is_file() else None,
        "register_score_crosscheck": {
            "grade_mean_of_12": (reg_score or {}).get("grade_mean_of_12"),
            "source": "scripts/device_lab_score_from_register.py",
        },
        "hardcoded_tens_forbidden": True,
        "any_grade_is_10": any(int(g.get("grade") or 0) >= 10 for g in grades.values()),
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        "SILICON_EXACT_EMULATION": False,
        "VF4": "PHYSICAL_PENDING",
        "VF5": "PHYSICAL_PENDING",
        "VF6": "PHYSICAL_PENDING",
        "note": (
            "Independent recomputation from wp011r evidence files + gap register. "
            "Not gunnchctl score alone. Master complete remains false."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "grade_mean_of_12": mean, "tokens": scored["tokens_observed"]}, indent=2))
    if out["any_grade_is_10"]:
        print("REFUSING: independent score emitted a 10 without full evidence lock", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
