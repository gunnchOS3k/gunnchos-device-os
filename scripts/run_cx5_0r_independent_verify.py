#!/usr/bin/env python3
"""CX5.0R independent digital verifier — fresh disk read, fail-closed, adversarial copies."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CX5 = ROOT / "artifacts" / "complete_experience" / "cx5_0" / "release_regression"
AUTH_PIN = ROOT / "artifacts" / "device_lab_current_pin"
OUT = CX5 / "independent_verify"


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"_missing": True, "path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"_invalid_json": str(exc), "path": str(path)}


def tip() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def verify_bundle(life: dict, eco: dict, eco_pass: dict, gates: dict[str, dict], expected_head: str) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    missing: list[str] = []

    checks["lifecycle_pass"] = life.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS") is True
    if not checks["lifecycle_pass"]:
        missing.append("lifecycle_pass")
    mandatory = life.get("mandatory_apps") or []
    req = [
        "gunnchos_shell_home",
        "waike",
        "gunnchai",
        "anime_aggressors",
        "pedestrian_pursuit",
        "archive_of_life",
        "beatlink_party",
        "vault",
        "app_center",
        "browser",
        "mail",
        "device_management",
        "creator_studio",
    ]
    checks["lifecycle_mandatory_apps_present"] = all(a in mandatory for a in req) and len(mandatory) >= 13
    if not checks["lifecycle_mandatory_apps_present"]:
        missing.append("lifecycle_mandatory_apps_present")
    summaries = life.get("app_summaries") or {}
    checks["lifecycle_all_apps_ok"] = bool(summaries) and all(
        bool((summaries.get(a) or {}).get("ok")) for a in req
    )
    if not checks["lifecycle_all_apps_ok"]:
        missing.append("lifecycle_all_apps_ok")
    life_head = life.get("exact_integration_head") or ""
    checks["lifecycle_head_matches"] = bool(life_head) and life_head == expected_head
    if not checks["lifecycle_head_matches"]:
        missing.append(f"lifecycle_head_matches:{life_head}!={expected_head}")

    eco_ok = (
        eco.get("ok") is True
        and eco.get("simultaneous_soak_complete") is True
        and float(eco.get("duration_sec_ran") or 0) >= 1800
        and int(eco.get("duration_sec_requested") or 0) >= 1800
        and eco.get("duration_shortened_to_pass") is not True
        and eco.get("dry_check") is not True
    )
    checks["eco010_soak_body"] = eco_ok
    if not eco_ok:
        missing.append("eco010_soak_body")
    checks["eco010_pass_token"] = eco_pass.get("ECO010_SOAK_PASS") is True
    if not checks["eco010_pass_token"]:
        missing.append("eco010_pass_token")
    checks["eco010_head_matches"] = (eco_pass.get("exact_integration_head") or eco.get("exact_integration_head")) == expected_head
    if not checks["eco010_head_matches"]:
        missing.append("eco010_head_matches")

    for name, key in [
        ("LIVE", "LIVE_GUNNCHOS_VISUAL_PASS"),
        ("DSXL", "DSXL_DUAL_COMPOSITOR_UX_PASS"),
        ("RING", "RING_TO_REAL_APP_STATE_MUTATION_PASS"),
        ("FOUR_GAME", "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"),
        ("WAIKE", "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"),
        ("GUNNCHAI", "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS"),
    ]:
        ok = gates[name].get(key) is True
        checks[name] = ok
        if not ok:
            missing.append(name)

    passed = all(checks.values()) and not missing
    return {"checks": checks, "missing": missing, "PASS": passed}


def adversarial(life_path: Path, eco_path: Path, eco_pass_path: Path, expected_head: str, gates: dict) -> dict[str, Any]:
    cases = []
    with tempfile.TemporaryDirectory(prefix="cx5_0r_adv_") as td:
        tdp = Path(td)
        # forged PASS token
        forged = json.loads(eco_pass_path.read_text())
        forged["ECO010_SOAK_PASS"] = True
        forged["forged"] = True
        forged["duration_sec_ran"] = 12
        forged["simultaneous_soak_complete"] = True
        fp = tdp / "eco_pass_forged.json"
        fp.write_text(json.dumps(forged))
        life = json.loads(life_path.read_text())
        eco = json.loads(eco_path.read_text())
        r = verify_bundle(life, eco, forged, gates, expected_head)
        cases.append({"case": "forged_pass_token_short_duration", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

        # deleted lifecycle row
        life2 = json.loads(life_path.read_text())
        life2["mandatory_apps"] = [a for a in life2.get("mandatory_apps", []) if a != "vault"]
        if "app_summaries" in life2:
            life2["app_summaries"].pop("vault", None)
        r = verify_bundle(life2, eco, json.loads(eco_pass_path.read_text()), gates, expected_head)
        cases.append({"case": "lifecycle_row_removed", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

        # shortened soak
        eco2 = json.loads(eco_path.read_text())
        eco2["duration_sec_ran"] = 60
        eco2["ok"] = True
        eco2["simultaneous_soak_complete"] = True
        r = verify_bundle(life, eco2, json.loads(eco_pass_path.read_text()), gates, expected_head)
        cases.append({"case": "shortened_soak", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

        # stale SHA
        life3 = json.loads(life_path.read_text())
        life3["exact_integration_head"] = "0" * 40
        r = verify_bundle(life3, eco, json.loads(eco_pass_path.read_text()), gates, expected_head)
        cases.append({"case": "stale_sha", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

        # modified artifact hash (body claim ok but duration_shortened true)
        eco3 = json.loads(eco_path.read_text())
        eco3["duration_shortened_to_pass"] = True
        r = verify_bundle(life, eco3, json.loads(eco_pass_path.read_text()), gates, expected_head)
        cases.append({"case": "modified_shortened_flag", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

        # draft/accepted identity substitution — invent PASS without repo_soak
        fake_pass = {
            "ECO010_SOAK_PASS": True,
            "exact_integration_head": expected_head,
            "repo_soak_ok": False,
            "simultaneous_soak_complete": False,
            "duration_sec_requested": 1800,
            "duration_sec_ran": 1800,
        }
        # Body still authoritative; pass token alone insufficient if body fails
        eco_bad = dict(eco)
        eco_bad["ok"] = False
        eco_bad["simultaneous_soak_complete"] = False
        r = verify_bundle(life, eco_bad, fake_pass, gates, expected_head)
        cases.append({"case": "draft_accepted_identity_substitution", "must_fail": True, "failed": not r["PASS"], "missing": r["missing"]})

    all_fail_closed = all(c["failed"] for c in cases)
    return {"cases": cases, "all_fail_closed": all_fail_closed}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    expected_head = tip()
    life_path = CX5 / "lifecycle" / "CURRENT_PIN_APP_LIFECYCLE_MATRIX.json"
    eco_path = CX5 / "eco010" / "ECO010_SOAK.json"
    eco_pass_path = CX5 / "eco010" / "ECO010_SOAK_PASS.json"

    gates = {
        "LIVE": load(AUTH_PIN / "LIVE_GUNNCHOS_VISUAL_PASS.json"),
        "DSXL": load(AUTH_PIN / "DSXL_DUAL_COMPOSITOR_UX_PASS.json"),
        "RING": load(AUTH_PIN / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json"),
        "FOUR_GAME": load(AUTH_PIN / "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.json"),
        "WAIKE": load(AUTH_PIN / "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json"),
        "GUNNCHAI": load(AUTH_PIN / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json"),
    }
    # Prefer nested gunnchai path if needed
    if gates["GUNNCHAI"].get("_missing"):
        gates["GUNNCHAI"] = load(AUTH_PIN / "gunnchai" / "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json")

    life = load(life_path)
    eco = load(eco_path)
    eco_pass = load(eco_pass_path)
    auth = verify_bundle(life, eco, eco_pass, gates, expected_head)
    adv = adversarial(life_path, eco_path, eco_pass_path, expected_head, gates) if not any(
        x.get("_missing") for x in (life, eco, eco_pass)
    ) else {"cases": [], "all_fail_closed": False, "error": "missing_inputs"}

    overall = bool(auth["PASS"] and adv.get("all_fail_closed"))
    report = {
        "schema": "CX5_0R_INDEPENDENT_VERIFY/v1",
        "generated_at_utc": utc(),
        "exact_integration_head": expected_head,
        "authoritative": auth,
        "adversarial": adv,
        "hashes": {
            "lifecycle": sha256_file(life_path),
            "eco010": sha256_file(eco_path),
            "eco010_pass": sha256_file(eco_pass_path),
        },
        "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": overall,
        "prefer_fail_over_false_pass": True,
    }
    (OUT / "CX5_0R_INDEPENDENT_VERIFY.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "ADVERSARIAL_TESTS.json").write_text(json.dumps(adv, indent=2) + "\n")
    (CX5 / "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS.json").write_text(
        json.dumps(
            {
                "generated_at_utc": utc(),
                "exact_integration_head": expected_head,
                "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": overall,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": overall, "missing": auth.get("missing"), "adv": adv.get("all_fail_closed")}, indent=2))
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
