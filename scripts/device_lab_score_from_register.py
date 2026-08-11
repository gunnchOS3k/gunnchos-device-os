#!/usr/bin/env python3
"""Compute Device Lab baseline grades from the completion register (no hardcoded 10s).

Usage:
  PYTHONPATH=. python3 scripts/device_lab_score_from_register.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "gunnchos_device_os/device_lab/device_lab_v1/DEVICE_LAB_COMPLETION_REGISTER.yaml"
TOKENS = ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json"

# Map register requirement IDs into the 12 baseline axes.
AXIS_IDS: dict[str, tuple[str, ...]] = {
    "foundation": ("DL-FOUNDATION-001", "DL-FOUNDATION-002", "DL-FOUNDATION-003", "DL-FOUNDATION-004", "DL-FOUNDATION-005"),
    "golden_journeys": ("DL-GOLDEN-001", "DL-GOLDEN-002", "DL-GOLDEN-002b", "DL-GOLDEN-003", "DL-GOLDEN-004", "DL-GOLDEN-005"),
    "behavioral_peripherals": ("DL-PERIPH-001", "DL-PERIPH-002", "DL-PERIPH-003", "DL-PERIPH-004", "DL-PERIPH-005", "DL-PERIPH-006", "DL-PERIPH-007"),
    "failure_injection": ("DL-FAULT-001", "DL-FAULT-002"),
    "evidence_reproducibility": ("DL-EVIDENCE-001", "DL-EVIDENCE-002", "DL-CAL-001"),
    "actual_virtual_gunnchos": ("DL-GUEST-001", "DL-GUEST-002", "DL-GUEST-003"),
    "avd_style_experience": ("DL-AVD-001", "DL-AVD-002"),
    "live_visual_interaction": ("DL-VISUAL-001", "DL-VISUAL-002"),
    "hardware_spec_sync": ("DL-HWSYNC-001", "DL-HWSYNC-002", "DL-HWSYNC-003"),
    "performance_prediction": ("DL-PERF-001", "DL-PERF-002"),
    "full_ecosystem_simulation": ("DL-ECOSYSTEM-001", "DL-ECOSYSTEM-002", "DL-ECOSYSTEM-003"),
    "physical_digital_twin_fidelity": ("DL-TWIN-001", "DL-TWIN-002"),
}

STATE_SCORE = {
    "DIGITALLY_VALIDATED": 10.0,
    "INTEGRATED": 7.0,
    "IMPLEMENTED": 5.0,
    "TARGET": 2.0,
    "PHYSICAL_PENDING": 1.0,
    "EXTERNAL_PENDING": 1.0,
    "FAILED_DIGITAL": 0.0,
}


def _load_yaml_register(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        # Minimal fallback parser for this register shape (list of id/state maps).
        text = path.read_text(encoding="utf-8")
        reqs: list[dict[str, Any]] = []
        cur: dict[str, Any] | None = None
        firewall: dict[str, Any] = {}
        in_firewall = False
        for line in text.splitlines():
            if line.startswith("claim_firewall:"):
                in_firewall = True
                continue
            if in_firewall:
                if line and not line.startswith(" ") and not line.startswith("\t"):
                    in_firewall = False
                elif ":" in line:
                    k, v = line.strip().split(":", 1)
                    firewall[k.strip()] = v.strip()
            if line.strip().startswith("-") and "id:" in line or (line.startswith("  -") and "id:" not in line):
                if cur and cur.get("id"):
                    reqs.append(cur)
                cur = {}
            if cur is not None and ":" in line:
                key = line.strip().lstrip("- ").split(":", 1)
                if len(key) == 2 and key[0] in {"id", "state", "description"}:
                    cur[key[0]] = key[1].strip()
        if cur and cur.get("id"):
            reqs.append(cur)
        return {"requirements": reqs, "claim_firewall": firewall}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data


def grade_axis(reqs_by_id: dict[str, dict[str, Any]], axis: str, ids: tuple[str, ...]) -> dict[str, Any]:
    present = [reqs_by_id[i] for i in ids if i in reqs_by_id]
    if not present:
        return {"grade": 0, "axis": axis, "n": 0, "note": "no mapped requirements"}
    scores = [STATE_SCORE.get(str(r.get("state") or "TARGET"), 2.0) for r in present]
    mean = sum(scores) / len(scores)
    # Cap physical twin axis: physical pending cannot inflate digital grade to 10.
    if axis == "physical_digital_twin_fidelity":
        mean = min(mean, 3.0)
    grade = int(round(mean / 10.0 * 10))  # 0-10 integer from mean state scores
    # Never emit hardcoded perfect 10 unless every mapped req is DIGITALLY_VALIDATED
    # and axis is not physical twin.
    if grade >= 10:
        if axis == "physical_digital_twin_fidelity":
            grade = 3
        elif not all(str(r.get("state")) == "DIGITALLY_VALIDATED" for r in present):
            grade = min(grade, 9)
    return {
        "grade": grade,
        "axis": "PRE_EVT_DIGITAL" if axis == "physical_digital_twin_fidelity" else "DIGITAL",
        "n": len(present),
        "states": Counter(str(r.get("state")) for r in present),
        "ids": [r.get("id") for r in present],
    }


def main() -> int:
    reg = _load_yaml_register(REGISTER)
    reqs = reg.get("requirements") or reg.get("requirement_register") or []
    # Some registers nest under "requirements:"; yaml load gives list at key.
    if not reqs and isinstance(reg.get("requirements"), list):
        reqs = reg["requirements"]
    # PyYAML path: top-level may use different key — scan for list of dicts with id+state
    if not reqs:
        for v in reg.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0] and "state" in v[0]:
                reqs = v
                break
    reqs_by_id = {str(r.get("id")): r for r in reqs if isinstance(r, dict) and r.get("id")}
    grades = {axis: grade_axis(reqs_by_id, axis, ids) for axis, ids in AXIS_IDS.items()}
    # physical twin returns nested digital grade
    numeric = []
    for axis, g in grades.items():
        if axis == "physical_digital_twin_fidelity":
            numeric.append(float(g.get("grade") or 0))
        else:
            numeric.append(float(g.get("grade") or 0))
    mean = round(sum(numeric) / len(numeric), 2) if numeric else 0.0
    tokens = json.loads(TOKENS.read_text(encoding="utf-8")) if TOKENS.exists() else {}
    firewall = reg.get("claim_firewall") or {}
    out = {
        "schema": "gunnchos.device_lab.score_from_register.v1",
        "register": str(REGISTER.relative_to(ROOT)),
        "requirement_count": len(reqs_by_id),
        "state_counts": dict(Counter(str(r.get("state")) for r in reqs_by_id.values())),
        "baseline_12_grades": grades,
        "grade_mean_of_12": mean,
        "claim_firewall": firewall,
        "tokens_master_complete": tokens.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"),
        "GUEST_DUAL_OUTPUT_PASS": tokens.get("GUEST_DUAL_OUTPUT_PASS"),
        "RING_TO_REAL_APPLICATION_INPUT_PASS": tokens.get("RING_TO_REAL_APPLICATION_INPUT_PASS"),
        "RING_SPATIAL_ACCURACY": tokens.get("RING_SPATIAL_ACCURACY"),
        "hardcoded_tens_forbidden": True,
        "note": "Grades derived from register states; master complete must stay false until all digital gates earned.",
    }
    print(json.dumps(out, indent=2, default=str))
    if tokens.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE") is True:
        print("REFUSING: master complete token is true while score script forbids premature lock", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
