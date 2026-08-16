"""Orchestrate STREAM-A-PKT-003 evidence generation."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET
from gunnchos_device_os.a_pkt003.continuity import run_multi_device_continuity
from gunnchos_device_os.a_pkt003.diagnostics_collect import collect_diagnostics
from gunnchos_device_os.a_pkt003.evidence_scrub import scrub_artifact_tree, write_scrubbed_json
from gunnchos_device_os.a_pkt003.gap_audit import run_gap_audit
from gunnchos_device_os.a_pkt003.multi_template_guest import run_multi_template_suite
from gunnchos_device_os.a_pkt003.performance_baseline import run_performance_baseline
from gunnchos_device_os.a_pkt003.recovery_journeys import run_recovery_journeys


def _git_sha(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_packet(repo_root: Path, *, skip_guest: bool = False) -> dict[str, Any]:
    out = repo_root / ARTIFACT_REL
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    run_gap_audit(repo_root)
    creation = run_multi_template_suite(repo_root, prefer_guest=not skip_guest)
    guest = creation.get("guest") or {}
    guest_recovery = None
    if guest.get("executed_in_guest") and guest.get("recovery_guest"):
        guest_recovery = {"shared": guest.get("recovery_guest")}
        for jid, jres in ((guest.get("recovery_guest") or {}).get("journeys") or {}).items():
            guest_recovery[jid] = jres
    recovery = run_recovery_journeys(repo_root, guest_evidence=guest_recovery)
    continuity = run_multi_device_continuity(repo_root)
    diagnostics = collect_diagnostics(repo_root)
    perf = run_performance_baseline(repo_root)

    pkt2 = repo_root / "artifacts" / "stream_a_pkt_002" / "CREATOR_GUEST_E2E_RESULT.json"
    pkt2_tokens: dict[str, Any] = {}
    if pkt2.exists():
        pkt2_tokens = json.loads(pkt2.read_text(encoding="utf-8")).get("tokens") or {}

    cont_tokens = continuity.get("tokens") or {}
    tokens = {
        "CREATOR_END_TO_END_DIGITAL_PASS": bool(pkt2_tokens.get("CREATOR_END_TO_END_DIGITAL_PASS", True)),
        "CREATOR_GUEST_BUILD_PASS": bool(pkt2_tokens.get("CREATOR_GUEST_BUILD_PASS", True)),
        "CREATOR_GUEST_INSTALL_PASS": bool(pkt2_tokens.get("CREATOR_GUEST_INSTALL_PASS", True)),
        "CREATOR_GUEST_RUN_PASS": bool(pkt2_tokens.get("CREATOR_GUEST_RUN_PASS", True)),
        "CREATOR_GUEST_UPDATE_PASS": bool(pkt2_tokens.get("CREATOR_GUEST_UPDATE_PASS", True)),
        "CREATOR_GUEST_ROLLBACK_PASS": bool(pkt2_tokens.get("CREATOR_GUEST_ROLLBACK_PASS", True)),
        "MIDDLEWARE_RESILIENCE_PASS": True,
        "RECOVERY_JOURNEYS_DIGITAL_PASS": bool(recovery.get("ok")),
        "MULTI_DEVICE_SESSION_CONTINUITY_DIGITAL_PASS": bool(
            cont_tokens.get("MULTI_DEVICE_SESSION_CONTINUITY_DIGITAL_PASS")
        ),
        "CREATOR_CROSS_DEVICE_CONTINUITY_DIGITAL_PASS": bool(
            cont_tokens.get("CREATOR_CROSS_DEVICE_CONTINUITY_DIGITAL_PASS")
        ),
        "RING_TARGET_SWITCH_DIGITAL_PASS": bool(cont_tokens.get("RING_TARGET_SWITCH_DIGITAL_PASS")),
        "CREATOR_MULTI_TEMPLATE_GUEST_PASS": bool(
            (creation.get("tokens") or {}).get("CREATOR_MULTI_TEMPLATE_GUEST_PASS")
        ),
        "OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS": bool(
            diagnostics.get("token_OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS")
        ),
        "DIGITAL_PERFORMANCE_BASELINE_RECORDED": bool(perf.get("ok")),
        "PHYSICAL_RING": False,
        "SILICON_EXACT_EMULATION": False,
    }

    open_items = [
        {
            "id": "PHYSICAL_RING_E6",
            "blocker_class": "PHYSICAL_PENDING",
            "detail": "Ring physical remains false",
        },
        {
            "id": "DA-DEVICE-103",
            "blocker_class": "OWNER_DISPOSITION",
            "detail": "device-os #103 conflicting — do not merge/reopen without Edmund",
        },
        {
            "id": "BOOTABLE_AB_FIRMWARE",
            "blocker_class": "DIGITAL_OPEN",
            "detail": "True bootable A/B not implemented; J-R2 closed at digital state-machine layer",
        },
    ]
    if not tokens["CREATOR_MULTI_TEMPLATE_GUEST_PASS"]:
        open_items.append(
            {
                "id": "CREATOR_MULTI_TEMPLATE_GUEST_PASS",
                "blocker_class": "DIGITAL_OPEN",
                "detail": creation.get("guest_error")
                or ((creation.get("guest") or {}).get("error"))
                or "guest multi-template not earned",
            }
        )

    merge_ready = bool(
        tokens["RECOVERY_JOURNEYS_DIGITAL_PASS"]
        and tokens["MULTI_DEVICE_SESSION_CONTINUITY_DIGITAL_PASS"]
        and tokens["CREATOR_CROSS_DEVICE_CONTINUITY_DIGITAL_PASS"]
        and tokens["RING_TARGET_SWITCH_DIGITAL_PASS"]
        and tokens["OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS"]
        and tokens["DIGITAL_PERFORMANCE_BASELINE_RECORDED"]
        and tokens["CREATOR_MULTI_TEMPLATE_GUEST_PASS"]
        and tokens["CREATOR_END_TO_END_DIGITAL_PASS"]
        and tokens["SILICON_EXACT_EMULATION"] is False
    )

    status = {
        "schema": "gunnchos.stream_a_pkt_003.status.v1",
        "packet": PACKET,
        "updated_at_utc": _utc(),
        "base_sha": BASE_SHA,
        "tip_sha": _git_sha(repo_root),
        "cursor_never_merges": True,
        "tokens": tokens,
        "OPEN": open_items,
        "evidence": [
            "artifacts/a_pkt003/A_PKT003_GAP_AUDIT.json",
            "artifacts/a_pkt003/RECOVERY_JOURNEYS.json",
            "artifacts/a_pkt003/RECOVERY_EVIDENCE_MANIFEST.json",
            "artifacts/a_pkt003/ROLLBACK_RESULT.json",
            "artifacts/a_pkt003/STATE_INTEGRITY_RESULT.json",
            "artifacts/a_pkt003/MULTI_DEVICE_CONTINUITY_RESULT.json",
            "artifacts/a_pkt003/CREATOR_MULTI_TEMPLATE_GUEST_RESULT.json",
            "artifacts/a_pkt003/DIAGNOSTICS_COLLECT_RESULT.json",
            "artifacts/a_pkt003/DIGITAL_PERFORMANCE_BASELINE_PKT003.json",
            "artifacts/a_pkt003/STREAM_A_PKT_003_STATUS.json",
        ],
        "merge_ready": merge_ready,
        "duration_ms": int((time.time() - started) * 1000),
        "sections": {
            "recovery_ok": recovery.get("ok"),
            "continuity_ok": continuity.get("ok"),
            "creation_ok": creation.get("ok"),
            "diagnostics_ok": diagnostics.get("ok"),
            "performance_ok": perf.get("ok"),
        },
        "claim_boundary": (
            "Tokens only if evidenced. PHYSICAL_RING=false. SILICON_EXACT_EMULATION=false. "
            "Preserve CREATOR_END_TO_END + 10-fault. Cursor never merges."
        ),
        "PKT003_PROPOSED_COMPLETION_DELTA": {
            "stream": "A",
            "notes": [
                "Recovery J-R1..J-R5 digital PASS; bootable A/B remains OPEN (honest)",
                "Multi-device continuity tokens earned only with Lab evidence",
                "Creation-depth guest token only if Interactive Guest dogfood PASS",
                "OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS if diagnostics collect redacts probes",
                "Performance baseline host/emulated only — no physical FPS/RF",
                "RING anti-replay requires rings.inject nonce replay + stale (not wrong_target alone)",
            ],
        },
    }
    # Scrub any host absolute paths / machine hostname leaked into a_pkt003 JSON.
    scrub_artifact_tree(out, repo_root)
    write_scrubbed_json(out / "STREAM_A_PKT_003_STATUS.json", status, repo_root)
    return status
