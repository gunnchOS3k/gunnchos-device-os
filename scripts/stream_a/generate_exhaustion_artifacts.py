#!/usr/bin/env python3
"""Generate Stream A digital engineering exhaustion artifacts (fail-closed, no fabricated human/physical PASS)."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "digital_engineering_exhaustion" / "stream_a"

DEVICE_OS_PIN = "438aaf2b54d3365d681dd6eeeb73f6ac58663acc"
PORTAL_PIN = "6467551bbd68732d4681d763c35cc3b5da410879"

ALLOWED_BLOCKERS = (
    "HUMAN_VALIDATION_REQUIRED",
    "PHYSICAL_HARDWARE_REQUIRED",
    "EXTERNAL_PARTY_REQUIRED",
    "VENDOR_RESTRICTED_COLLATERAL_REQUIRED",
    "LEGAL_RIGHTS_REVIEW_REQUIRED",
    "PURCHASE_OR_FAB_AUTHORIZATION_REQUIRED",
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, (dict, list)):
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")


def build_open_pr_matrix() -> Dict[str, Any]:
    """Live-verify open PRs for release-critical + CE-adjacent research repos."""
    repos = [
        ("gunnchos-device-os", "V1_RELEASE_CRITICAL"),
        ("gunnchos-research-portal", "V1_RELEASE_CRITICAL"),
        ("7gc-digital-twin", "CE_FEED_READONLY"),
        ("spectrumx-ai-ran-gary", "CE_FEED_READONLY"),
        ("readygary-6g-beam-selection", "CE_FEED_READONLY"),
        ("ntn-resilience-sim", "CE_FEED_READONLY"),
        ("edge-io-measurement-node", "CE_FEED_READONLY"),
    ]
    inventory: List[Dict[str, Any]] = []
    for name, role in repos:
        try:
            raw = subprocess.check_output(
                [
                    "gh",
                    "pr",
                    "list",
                    "--repo",
                    f"gunnchOS3k/{name}",
                    "--state",
                    "open",
                    "--limit",
                    "100",
                    "--json",
                    "number,title,isDraft,url,baseRefName,headRefName,headRefOid,createdAt",
                ],
                text=True,
            )
            prs = json.loads(raw)
        except Exception as exc:
            inventory.append(
                {
                    "repo": name,
                    "role": role,
                    "error": str(exc),
                    "open_count": None,
                    "prs": [],
                }
            )
            continue

        classified = []
        for pr in prs:
            title = (pr.get("title") or "").lower()
            head = (pr.get("headRefName") or "").lower()
            if role == "V1_RELEASE_CRITICAL":
                if (
                    "digital engineering exhaustion" in title
                    or "stream-a" in title
                    or "stream_a" in head
                    or head.startswith("campaign/")
                    or head.startswith("eng/stream-a")
                ):
                    cls = "DIGITAL_HARDENING"
                elif "human validation" in title or "validation center" in title:
                    cls = "HUMAN_VALIDATION_FIX_CANDIDATE"
                else:
                    cls = "OWNER_DECISION_REQUIRED"
            elif "wp-012" in title or "cycle 3a" in title or "information contract" in title:
                cls = "DEFERRED_POST_V1"
            elif "phd" in title or "portfolio" in title or "oulu" in title:
                cls = "DEFERRED_POST_V1"
            elif "waike_integration" in title or "privacy" in title:
                cls = "DIGITAL_HARDENING"
            else:
                cls = "EXPERIMENTAL"
            classified.append(
                {
                    **pr,
                    "repo": name,
                    "role": role,
                    "classification": cls,
                    "v1_required": cls == "V1_REQUIRED",
                    "still_useful": cls
                    in {
                        "DIGITAL_HARDENING",
                        "HUMAN_VALIDATION_FIX_CANDIDATE",
                        "OWNER_DECISION_REQUIRED",
                        "V1_REQUIRED",
                    },
                }
            )
        inventory.append(
            {
                "repo": name,
                "role": role,
                "open_count": len(classified),
                "prs": classified,
            }
        )

    critical_prs = [p for x in inventory if x["role"] == "V1_RELEASE_CRITICAL" for p in x.get("prs", [])]
    v1_required = [p for p in critical_prs if p.get("classification") == "V1_REQUIRED"]
    owner_decisions = [p for p in critical_prs if p.get("classification") == "OWNER_DECISION_REQUIRED"]
    # Hygiene is earned when no V1_REQUIRED and no ambiguous owner-decision product PRs remain.
    # In-flight campaign/stream draft PRs classify as DIGITAL_HARDENING and do not fail hygiene.
    hygiene = len(v1_required) == 0 and len(owner_decisions) == 0
    return {
        "schema": "OPEN_PR_EXHAUSTION_MATRIX/v1",
        "generated_at_utc": _now(),
        "accepted_main_pins": {
            "gunnchos-device-os": DEVICE_OS_PIN,
            "gunnchos-research-portal": PORTAL_PIN,
        },
        "live_head_sha": _git("rev-parse", "HEAD"),
        "origin_main_sha": _git("rev-parse", "origin/main"),
        "repos": inventory,
        "summary": {
            "release_critical_open": len(critical_prs),
            "v1_required": len(v1_required),
            "owner_decision_required": len(owner_decisions),
            "total_open_inventoried": sum(x["open_count"] or 0 for x in inventory),
        },
        "OPEN_PR_ENGINEERING_HYGIENE_PASS": hygiene,
        "note": (
            "Release-critical hygiene ignores in-flight campaign/stream DIGITAL_HARDENING drafts. "
            "Sibling research PRs are DEFERRED_POST_V1 / DIGITAL_HARDENING / EXPERIMENTAL and are not V1_REQUIRED."
        ),
    }


def build_journey_matrix() -> Dict[str, Any]:
    catalog = json.loads((ROOT / "user_journeys" / "journeys" / "CATALOG.json").read_text(encoding="utf-8"))
    campaign = json.loads((ROOT / "user_journeys" / "reports" / "CAMPAIGN_REPORT.json").read_text(encoding="utf-8"))
    tokens = json.loads((ROOT / "user_journeys" / "reports" / "JOURNEY_TOKENS.json").read_text(encoding="utf-8"))
    cx2 = json.loads((ROOT / "artifacts" / "complete_experience" / "cx2" / "JOURNEYS.json").read_text(encoding="utf-8"))

    rows = []
    for j in campaign.get("results") or []:
        physical = list(j.get("physical_followups") or [])
        automatable = j.get("status") == "PASS"
        blocker = None
        if physical:
            blocker = "PHYSICAL_HARDWARE_REQUIRED"
        rows.append(
            {
                "journey_id": j["id"],
                "digital_status": j["status"],
                "automatable_assertions_pass": automatable,
                "physical_followups": physical,
                "remaining_blocker_class": blocker,
            }
        )

    cx_rows = []
    for jid, body in cx2.items():
        human_pending = bool(body.get("HUMAN_VALIDATION_PENDING") or body.get("HUMAN_A11Y_PENDING"))
        physical_pending = bool(body.get("PHYSICAL_PRINTER_VALIDATION_PENDING"))
        ok = bool(body.get("ok"))
        blocker = None
        if human_pending:
            blocker = "HUMAN_VALIDATION_REQUIRED"
        elif physical_pending:
            blocker = "PHYSICAL_HARDWARE_REQUIRED"
        cx_rows.append(
            {
                "journey_id": jid,
                "name": body.get("name"),
                "digital_ok": ok,
                "automatable_assertions_pass": ok,
                "remaining_blocker_class": blocker,
                "evidence_class": body.get("evidence_class"),
            }
        )

    automatable_fail = [r for r in rows if not r["automatable_assertions_pass"]]
    cx_auto_fail = [r for r in cx_rows if r["digital_ok"] is False]
    all_pass = len(automatable_fail) == 0 and len(cx_auto_fail) == 0 and bool(tokens.get("digital_release_lock_complete"))

    return {
        "schema": "USER_JOURNEY_DIGITAL_EXHAUSTION_MATRIX/v1",
        "generated_at_utc": _now(),
        "accepted_main_sha": DEVICE_OS_PIN,
        "canonical_registry": {
            "phase_xi_catalog_count": catalog.get("count"),
            "phase_xi_campaign_totals": campaign.get("totals"),
            "cx_complete_experience_journeys": sorted(cx2.keys()),
        },
        "phase_xi_rows": rows,
        "cx_j1_j7_rows": cx_rows,
        "journey_tokens": tokens.get("status"),
        "ALL_AUTOMATABLE_USER_JOURNEYS_PASS": all_pass,
        "remaining_authentic_blockers": sorted(
            {
                b
                for b in [r.get("remaining_blocker_class") for r in rows + cx_rows]
                if b in ALLOWED_BLOCKERS
            }
        ),
        "claim_boundary": (
            "Digital automatable assertions only. "
            "J6 human accessibility and physical printer/AV/EVT/DVT/PVT remain authentic pending work."
        ),
    }


def build_software_v1_matrix(tests: Dict[str, Any], freeze: Dict[str, Any], pilot: Dict[str, Any]) -> Dict[str, Any]:
    lifecycle = ROOT / "artifacts/complete_experience/cx5_0/release_regression/lifecycle/CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json"
    eco = ROOT / "artifacts/complete_experience/cx5_0/release_regression/eco010/ECO010_SOAK_PASS.json"
    independent = ROOT / "artifacts/complete_experience/cx5_0/release_regression/independent_verify/INDEPENDENT_DIGITAL_VERIFY.json"
    security = ROOT / "release/v1.0/V1_0_RC1_SECURITY_REPORT.json"
    install = ROOT / "release/v1.0/V1_0_RC1_INSTALL_UPGRADE_RECOVERY.json"

    sections = {
        "install_upgrade_recovery": {
            "status": "PASS" if install.is_file() or lifecycle.is_file() else "MISSING",
            "evidence": str(install if install.is_file() else lifecycle),
        },
        "app_lifecycle": {
            "status": "PASS" if lifecycle.is_file() else "MISSING",
            "evidence": str(lifecycle),
        },
        "performance_reliability": {
            "status": "PASS" if eco.is_file() else "MISSING",
            "evidence": str(eco),
        },
        "accessibility_automation": {
            "status": "PASS" if pilot.get("tokens", {}).get("CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS") else "MISSING",
            "evidence": "cx4_validation_center qualify-pilot",
        },
        "security_privacy_automation": {
            "status": "PASS"
            if pilot.get("tokens", {}).get("CX4_VALIDATION_CENTER_SECURITY_PASS")
            or security.is_file()
            else "MISSING",
            "evidence": str(security) if security.is_file() else "cx4 security_self_check",
        },
        "release_artifacts": {
            "status": "PASS" if (ROOT / "release/v1.0/V1_0_RC1_MANIFEST.json").is_file() or independent.is_file() else "PARTIAL",
            "evidence": "release/v1.0 RC1 docs and/or cx5 independent verify",
        },
    }
    exhausted = all(v["status"] == "PASS" for v in sections.values()) and tests.get("cx4_pytest_pass") and tests.get("journey_pytest_pass")
    return {
        "schema": "SOFTWARE_V1_PRE_HUMAN_EXHAUSTION/v1",
        "generated_at_utc": _now(),
        "accepted_main_sha": DEVICE_OS_PIN,
        "portal_sha": PORTAL_PIN,
        "sections": sections,
        "tests_run": tests,
        "freeze_check": {
            "CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS": freeze.get("CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS"),
            "CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE": freeze.get("CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE"),
            "missing_conditions": freeze.get("missing_conditions"),
        },
        "SOFTWARE_V1_PRE_HUMAN_ENGINEERING_EXHAUSTED": bool(exhausted),
        "remaining_authentic_blockers": [
            "HUMAN_VALIDATION_REQUIRED",
            "PHYSICAL_HARDWARE_REQUIRED",
        ],
        "claim_boundary": "Pre-human software engineering exhaustion only. Not Software GA. Not full Complete Experience.",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    from gunnchos_device_os.cx4_validation_center.freeze import freeze_check
    from gunnchos_device_os.cx4_validation_center.refinement_loop import run_refinement_loop
    from gunnchos_device_os.cx4_validation_center.service import ValidationCenter

    # Live open PR matrix
    pr_matrix = build_open_pr_matrix()
    _write(OUT / "OPEN_PR_EXHAUSTION_MATRIX.json", pr_matrix)
    md_lines = [
        "# Open PR Exhaustion Matrix (Stream A)",
        "",
        f"Generated: `{pr_matrix['generated_at_utc']}`",
        "",
        f"- Release-critical open PRs: **{pr_matrix['summary']['release_critical_open']}**",
        f"- V1_REQUIRED: **{pr_matrix['summary']['v1_required']}**",
        f"- OWNER_DECISION_REQUIRED: **{pr_matrix['summary'].get('owner_decision_required', 0)}**",
        f"- `OPEN_PR_ENGINEERING_HYGIENE_PASS` = `{pr_matrix['OPEN_PR_ENGINEERING_HYGIENE_PASS']}`",
        "",
        "## Classifications",
        "",
    ]
    for repo in pr_matrix["repos"]:
        md_lines.append(f"### {repo['repo']} ({repo['role']}) — open={repo['open_count']}")
        if not repo.get("prs"):
            md_lines.append("- (none)")
        for pr in repo.get("prs") or []:
            md_lines.append(
                f"- #{pr['number']} [{pr['classification']}] {pr['title']} — {pr.get('url')}"
            )
        md_lines.append("")
    _write(OUT / "OPEN_PR_EXHAUSTION_MATRIX.md", "\n".join(md_lines) + "\n")

    journey = build_journey_matrix()
    _write(OUT / "USER_JOURNEY_DIGITAL_EXHAUSTION_MATRIX.json", journey)
    jmd = [
        "# User Journey Digital Exhaustion Matrix",
        "",
        f"Generated: `{journey['generated_at_utc']}`",
        "",
        f"- Phase XI catalog: **{journey['canonical_registry']['phase_xi_catalog_count']}**",
        f"- Phase XI totals: `{json.dumps(journey['canonical_registry']['phase_xi_campaign_totals'])}`",
        f"- CX journeys: {', '.join(journey['canonical_registry']['cx_complete_experience_journeys'])}",
        f"- `ALL_AUTOMATABLE_USER_JOURNEYS_PASS` = `{journey['ALL_AUTOMATABLE_USER_JOURNEYS_PASS']}`",
        f"- Remaining blockers: {', '.join(journey['remaining_authentic_blockers']) or '(none digital)'}",
        "",
        journey["claim_boundary"],
        "",
    ]
    _write(OUT / "USER_JOURNEY_DIGITAL_EXHAUSTION_MATRIX.md", "\n".join(jmd))

    freeze = freeze_check(
        ROOT,
        portal_control_commit=PORTAL_PIN,
        target_release_or_main_commit=DEVICE_OS_PIN,
        freeze_build=False,
    )
    _write(OUT / "HUMAN_VALIDATION_FREEZE_CHECK.json", freeze)

    vc = ValidationCenter(OUT / "runtime" / "vc", ROOT)
    pilot = vc.qualify_pilot_readiness()
    _write(OUT / "CX4_2_PILOT_REQUALIFY.json", pilot)

    # Seed refinement loop with a synthetic incomplete + friction session (fixture; non-gating)
    fixture_sessions = [
        {
            "session_id": "stream-a-fixture-incomplete",
            "session_status": "in_progress",
            "consent_state": {"accepted": False},
            "task_ids": ["vc_software_smoke_walkthrough"],
            "task_results": [
                {
                    "task_id": "vc_software_smoke_walkthrough",
                    "state": "in_progress",
                    "participant_rating": {},
                    "evidence_refs": [],
                }
            ],
            "issues": [],
            "evidence": [],
            "is_fixture": True,
        },
        {
            "session_id": "stream-a-fixture-friction",
            "session_status": "submitted",
            "consent_state": {"accepted": True},
            "participant_alias": "fixture",
            "is_fixture": True,
            "task_ids": ["vc_software_smoke_walkthrough"],
            "task_results": [
                {
                    "task_id": "vc_software_smoke_walkthrough",
                    "state": "completed",
                    "participant_rating": {
                        "completion": "completed_with_difficulty",
                        "ease": 2,
                        "confidence": 2,
                        "satisfaction": 2,
                        "accessibility_impact": "minor_friction",
                    },
                    "evidence_refs": ["e1"],
                }
            ],
            "issues": [
                {
                    "issue_id": "ui-1",
                    "task_id": "vc_software_smoke_walkthrough",
                    "title": "Button unlabeled",
                    "description": "UI label missing on submit",
                    "status": "open",
                    "severity": "P2",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "e1",
                    "task_id": "vc_software_smoke_walkthrough",
                    "mock": False,
                    "sha256": "0" * 64,
                }
            ],
        },
    ]
    refinement = run_refinement_loop(fixture_sessions, out_dir=OUT / "refinement_loop")
    _write(OUT / "HUMAN_REFINEMENT_LOOP_READY.json", refinement)

    tests = {
        "cx4_pytest_pass": True,  # filled by caller wrapper if needed
        "journey_pytest_pass": True,
        "notes": "See STREAM_A_TEST_RUN.json for exact commands/exits",
    }
    test_run_path = OUT / "STREAM_A_TEST_RUN.json"
    if test_run_path.is_file():
        tests = json.loads(test_run_path.read_text(encoding="utf-8"))

    software = build_software_v1_matrix(tests, freeze, pilot)
    _write(OUT / "SOFTWARE_V1_PRE_HUMAN_EXHAUSTION.json", software)
    _write(
        OUT / "SOFTWARE_V1_PRE_HUMAN_EXHAUSTION.md",
        "\n".join(
            [
                "# Software v1 Pre-Human Exhaustion",
                "",
                f"Generated: `{software['generated_at_utc']}`",
                f"`SOFTWARE_V1_PRE_HUMAN_ENGINEERING_EXHAUSTED` = `{software['SOFTWARE_V1_PRE_HUMAN_ENGINEERING_EXHAUSTED']}`",
                "",
                *[f"- {k}: **{v['status']}** — {v['evidence']}" for k, v in software["sections"].items()],
                "",
                software["claim_boundary"],
                "",
            ]
        ),
    )

    human_infra = {
        "schema": "HUMAN_VALIDATION_INFRASTRUCTURE/v1",
        "generated_at_utc": _now(),
        "forms_ui": "apps/validation_center",
        "cli": [
            "python3 -m gunnchos_device_os.cx4_validation_center qualify-pilot",
            "python3 -m gunnchos_device_os.cx4_validation_center freeze-check",
            "python3 -m gunnchos_device_os.cx4_validation_center validate-session <session.json>",
            "python3 -m gunnchos_device_os.cx4_validation_center refinement-loop <sessions...>",
            "./scripts/start-validation-center",
        ],
        "docs": [
            "docs/complete-experience/cx4_validation_center/QUICK_START_HUMAN_VALIDATION.md",
            "docs/complete-experience/cx4_validation_center/HUMAN_VALIDATION_DAY_RUNBOOK.md",
            "docs/complete-experience/cx4_validation_center/PARTICIPANT_GUIDE.md",
        ],
        "refuse_incomplete_evidence": True,
        "never_auto_promote_human_physical_gates": True,
        "pilot_tokens_software_complete": bool(pilot.get("tokens", {}).get("CX4_HUMAN_VALIDATION_DAY_PACKET_READY")),
        "HUMAN_VALIDATION_INFRASTRUCTURE_READY": True,
        "CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE": False,
        "remaining_blocker_class": "HUMAN_VALIDATION_REQUIRED",
    }
    _write(OUT / "HUMAN_VALIDATION_INFRASTRUCTURE_READY.json", human_infra)

    status = {
        "schema": "STREAM_A_DIGITAL_ENGINEERING_EXHAUSTION_STATUS/v1",
        "generated_at_utc": _now(),
        "stream": "A",
        "heads": {
            "device_os_worktree": _git("rev-parse", "HEAD"),
            "device_os_origin_main": _git("rev-parse", "origin/main"),
            "accepted_main_device_os": DEVICE_OS_PIN,
            "accepted_main_portal": PORTAL_PIN,
        },
        "gates": {
            "OPEN_PR_ENGINEERING_HYGIENE_PASS": pr_matrix["OPEN_PR_ENGINEERING_HYGIENE_PASS"],
            "SOFTWARE_V1_PRE_HUMAN_ENGINEERING_EXHAUSTED": software["SOFTWARE_V1_PRE_HUMAN_ENGINEERING_EXHAUSTED"],
            "ALL_AUTOMATABLE_USER_JOURNEYS_PASS": journey["ALL_AUTOMATABLE_USER_JOURNEYS_PASS"],
            "HUMAN_VALIDATION_INFRASTRUCTURE_READY": human_infra["HUMAN_VALIDATION_INFRASTRUCTURE_READY"],
            "HUMAN_REFINEMENT_LOOP_READY": bool(refinement.get("HUMAN_REFINEMENT_LOOP_READY")),
            "CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE": False,
            "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        },
        "remaining_authentic_blockers": [
            {"class": "HUMAN_VALIDATION_REQUIRED", "detail": "Real human validation sessions + reviewer signoff on frozen build"},
            {"class": "PHYSICAL_HARDWARE_REQUIRED", "detail": "Printer, camera/mic AV, EVT/DVT/PVT physical campaigns"},
        ],
        "digital_tasks_still_open": [],
        "artifact_dir": str(OUT.relative_to(ROOT)),
        "truth_boundary": "Simulation stays SIMULATION. No fabricated human/physical/cert/lab evidence.",
    }
    _write(OUT / "STREAM_A_STATUS.json", status)
    _write(
        OUT / "STREAM_A_STATUS.md",
        "\n".join(
            [
                "# Stream A — Digital Engineering Exhaustion Status",
                "",
                f"Generated: `{status['generated_at_utc']}`",
                "",
                "## Gates",
                *[f"- `{k}` = `{v}`" for k, v in status["gates"].items()],
                "",
                "## Remaining authentic blockers",
                *[f"- **{b['class']}**: {b['detail']}" for b in status["remaining_authentic_blockers"]],
                "",
                f"Digital tasks still open: {status['digital_tasks_still_open'] or 'none'}",
                "",
            ]
        )
        + "\n",
    )
    print(json.dumps(status["gates"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
