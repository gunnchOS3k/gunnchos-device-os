from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.phase_xi import (
    CLAIM_BOUNDARY,
    CLASS_TOKENS,
    CONTEXT_JOURNEYS,
    MULTITASK_JOURNEYS,
    TOKEN_CONTEXT,
    TOKEN_DIGITAL_LOCK,
    TOKEN_MULTITASK,
)
from gunnchos_device_os.phase_xi.adapters.productivity import detect_stack
from gunnchos_device_os.phase_xi.defects import DefectRegister
from gunnchos_device_os.phase_xi.harness import JourneyHarness
from gunnchos_device_os.phase_xi.policies import (
    ContinuityPolicy,
    MediaFocusPolicy,
    MultitaskingPolicy,
    NotificationPolicy,
    PowerPolicy,
)


REPRESENTATIVE_CI = [
    "J-STU-001",
    "J-OFF-001",
    "J-CREATOR-001",
    "J-NET-001",
    "J-GAME-001",
    "J-RING-001",
    "J-REC-003",
]


def _load_catalog(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / "user_journeys" / "journeys" / "CATALOG.json").read_text(encoding="utf-8"))
    return list(data["journeys"])


def run_campaign(
    root: Path | None = None,
    only: list[str] | None = None,
    representative: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    harness = JourneyHarness(root)
    register = DefectRegister(root)
    catalog = _load_catalog(root)
    if representative:
        ids = list(REPRESENTATIVE_CI)
    elif only:
        ids = list(only)
    else:
        ids = [j["id"] for j in catalog]

    results: list[dict[str, Any]] = []
    for jid in ids:
        harness.session = {
            "authenticated": False,
            "network": "online",
            "open_files": {},
            "cursor_position": {},
            "music_position": 0,
            "video_position": 0,
            "chat_state": {},
            "game_save": None,
            "ai_sync_permitted": False,
            "focus_mode": False,
            "storage_used_pct": 40.0,
            "battery_pct": 80.0,
            "doc_versions": {},
        }
        harness.notify.focus_mode = False
        harness.media.active_session = None
        evidence = harness.run_journey(jid)
        status = evidence["status"]
        if status == "FAIL":
            step = (evidence.get("fail_reason") or "unknown").split(":", 1)[0]
            register.add(
                journey=jid,
                step=step,
                severity="U1",
                root_cause=evidence.get("fail_reason") or "unknown",
                repo="gunnchos-device-os",
                component="phase_xi.harness",
                fix="pending",
                regression="tests/test_phase_xi_user_journeys.py",
                status="OPEN",
                classification="DIGITAL",
            )
        results.append(
            {
                "id": jid,
                "status": status,
                "fail_reason": evidence.get("fail_reason"),
                "duration_ms": evidence.get("duration_ms"),
                "physical_followups": evidence.get("physical_followups") or [],
            }
        )

    harness.stack.stop()

    by_status = {"PASS": 0, "FAIL": 0, "BLOCKED_PHYSICAL": 0, "BLOCKED_EXTERNAL": 0}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    class_map: dict[str, list[str]] = {}
    meta = {j["id"]: j for j in catalog}
    for r in results:
        jclass = meta.get(r["id"], {}).get("class", "unknown")
        class_map.setdefault(jclass, []).append(r["id"])

    result_by_id = {r["id"]: r for r in results}
    full_class_map: dict[str, list[str]] = {}
    for j in catalog:
        full_class_map.setdefault(j.get("class", "unknown"), []).append(j["id"])

    earned: dict[str, bool] = {}
    for jclass, token in CLASS_TOKENS.items():
        members = full_class_map.get(jclass, [])
        # Earn only when every catalog member of the class was executed and PASSed
        if not members or any(mid not in result_by_id for mid in members):
            earned[token] = False
            continue
        earned[token] = all(result_by_id[mid]["status"] == "PASS" for mid in members)

    earned[TOKEN_MULTITASK] = all(
        mid in result_by_id and result_by_id[mid]["status"] == "PASS" for mid in MULTITASK_JOURNEYS
    )
    earned[TOKEN_CONTEXT] = all(
        mid in result_by_id and result_by_id[mid]["status"] == "PASS" for mid in CONTEXT_JOURNEYS
    )

    open_u0_u1 = register.open_digital_u0_u1()
    digital_fail = by_status.get("FAIL", 0)
    lock_ok = digital_fail == 0 and not open_u0_u1

    stack_audit = detect_stack(root)
    policies = {
        "multitasking": MultitaskingPolicy().to_dict(),
        "media_focus": MediaFocusPolicy().to_dict(),
        "notifications": NotificationPolicy().to_dict(),
        "continuity": ContinuityPolicy().to_dict(),
        "power": PowerPolicy().to_dict(),
    }

    report = {
        "schema": "gunnchos.phase_xi_campaign.v1",
        "ok": lock_ok,
        "totals": {
            "TOTAL": len(results),
            "PASS": by_status.get("PASS", 0),
            "FAIL": by_status.get("FAIL", 0),
            "BLOCKED_PHYSICAL": by_status.get("BLOCKED_PHYSICAL", 0),
            "BLOCKED_EXTERNAL": by_status.get("BLOCKED_EXTERNAL", 0),
        },
        "results": results,
        "earned_tokens": {k: v for k, v in earned.items() if v},
        "token_status": earned,
        "defects": [d.to_dict() for d in register.defects],
        "defect_counts": register.counts(),
        "open_digital_u0_u1": [d.id for d in open_u0_u1],
        "productivity_stack_audit": stack_audit,
        "policies": policies,
        "digital_release_lock": {
            "DIGITAL_RELEASE_LOCK_COMPLETE": lock_ok and not (only or representative),
            "DIGITAL_RELEASE_LOCK_REOPENED_BY_USER_JOURNEY": digital_fail > 0,
            "token": TOKEN_DIGITAL_LOCK if lock_ok and not (only or representative) else None,
        },
        "physical_execution_freeze": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "representative_ci": REPRESENTATIVE_CI,
        "auto_merge_request": None,
        "mock": False,
    }

    if write:
        art = root / "artifacts" / "phase_xi"
        art.mkdir(parents=True, exist_ok=True)
        (art / "CAMPAIGN_REPORT.json").write_text(json.dumps(report, indent=2) + chr(10), encoding="utf-8")
        (root / "user_journeys" / "reports" / "CAMPAIGN_REPORT.json").write_text(
            json.dumps(report, indent=2) + chr(10), encoding="utf-8"
        )
        register.write()
        tokens = {
            "schema": "gunnchos.phase_xi_tokens.v1",
            "earned": sorted(k for k, v in earned.items() if v),
            "status": earned,
            "digital_release_lock_complete": report["digital_release_lock"]["DIGITAL_RELEASE_LOCK_COMPLETE"],
            "claim_boundary": CLAIM_BOUNDARY,
        }
        (art / "JOURNEY_TOKENS.json").write_text(json.dumps(tokens, indent=2) + chr(10), encoding="utf-8")
        (root / "user_journeys" / "reports" / "JOURNEY_TOKENS.json").write_text(
            json.dumps(tokens, indent=2) + chr(10), encoding="utf-8"
        )
        cfg = root / "config" / "phase_xi"
        cfg.mkdir(parents=True, exist_ok=True)
        for name, payload in policies.items():
            (cfg / f"{name}_policy.json").write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")
        (cfg / "productivity_stack_audit.json").write_text(
            json.dumps(stack_audit, indent=2) + chr(10), encoding="utf-8"
        )
    return report


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Phase XI user-journey campaign")
    p.add_argument("--representative", action="store_true")
    p.add_argument("--only", nargs="*")
    args = p.parse_args()
    report = run_campaign(only=args.only, representative=args.representative)
    print(json.dumps({"ok": report["ok"], "totals": report["totals"], "earned": report["earned_tokens"]}, indent=2))


if __name__ == "__main__":
    main()
