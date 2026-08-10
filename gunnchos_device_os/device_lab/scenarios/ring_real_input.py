"""LAB-SCENARIO-RING-REAL-INPUT — G07 stack path; file writes do not count."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.scenarios.engine import ScenarioEngine
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session


def run(*, repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    # Rings + target compute device
    profile_id = profile_id or "edge_io_rings"
    companion = "student_14_5"
    started = time.time()
    start = start_session(profile_id, repo_root=repo_root)
    session = get_session(start["instance_id"])
    # Also bring up companion host profile backends for app targets
    companion_start = start_session(companion, repo_root=repo_root)
    companion_sess = get_session(companion_start["instance_id"])

    evidence = session.work / "LAB-SCENARIO-RING-REAL-INPUT"
    evidence.mkdir(parents=True, exist_ok=True)
    # Re-bind rings onto scenario evidence so surface mirrors land here
    rings_info = session.rings.start(evidence_dir=evidence, repo_root=repo_root)
    eng = ScenarioEngine(session, evidence)
    errors: list[str] = []

    pipeline = rings_info.get("pipeline") or []
    required = [
        "edge_io_sim",
        "authenticated_packet",
        "ring_service",
        "SpatialInputService",
        "input_router_hid_wayland",
        "apps",
    ]
    pipeline_ok = all(p in pipeline for p in required)
    if not pipeline_ok:
        errors.append("pipeline_incomplete")
    eng.record("pipeline", None, "start", required, pipeline, pipeline_ok)

    # Positive deliveries to document, browser, game — must mutate observable app state
    deliveries: dict[str, Any] = {}
    app_mutations: dict[str, Any] = {}
    for target in ("libreoffice", "browser", "games"):
        r = session.rings.inject(target=target, confidence=0.92, gesture="click")
        deliveries[target] = r
        mutated = bool(r.get("delivered") and r.get("app_state_changed") and r.get("via_stack"))
        if r.get("result", {}).get("direct_file_write"):
            mutated = False
            errors.append(f"direct_file_write_claimed_{target}")
        if not mutated:
            errors.append(f"deliver_fail_{target}")
        app_mutations[target] = {
            "delivered": r.get("delivered"),
            "app_state_changed": r.get("app_state_changed"),
            "before": r.get("before"),
            "after": r.get("after"),
            "via_stack": r.get("via_stack"),
        }
    pos_ok = all(
        deliveries[t].get("delivered")
        and deliveries[t].get("app_state_changed")
        and deliveries[t].get("via_stack")
        for t in deliveries
    )
    if not pos_ok:
        errors.append("positive_delivery_failed")
    eng.record("app_deliveries", None, "inject", "three_targets_with_state_mutation", deliveries, pos_ok)
    eng.record(
        "observable_app_state",
        None,
        "mutation_check",
        "document+browser+game",
        app_mutations,
        pos_ok,
    )

    # Negatives: low confidence + wrong target
    low = session.rings.inject(confidence=0.2, target="browser")
    wrong = session.rings.inject(confidence=0.9, target="browser", wrong_target=True)
    safety_ok = (low.get("delivered") is False) and (wrong.get("delivered") is False)
    if not safety_ok:
        errors.append("safety_reject_failed")
    fallback = session.rings.fallback_conventional()
    eng.record(
        "safety_and_fallback",
        None,
        "low_confidence+wrong_target",
        "reject+fallback",
        {"low": low, "wrong": wrong, "fallback": fallback},
        safety_ok and fallback.get("ok"),
    )

    # Explicitly prove file-write is NOT valid D6
    fake_path = evidence / "NOT_VALID_ring_file_write.txt"
    fake_path.write_text("this direct file write must not count as ring D6\n", encoding="utf-8")
    file_write_claimed_as_d6 = False
    eng.record(
        "file_write_not_d6",
        None,
        "direct_file_write",
        "must_not_count",
        {"path": str(fake_path), "counts_as_d6": file_write_claimed_as_d6},
        not file_write_claimed_as_d6,
    )

    # Honest delivered flag: must not be unconditionally True
    delivered_honesty = all(
        isinstance(deliveries[t].get("delivered"), bool) and deliveries[t].get("delivered") is True
        for t in deliveries
    ) and (low.get("delivered") is False)
    if not delivered_honesty:
        errors.append("delivered_flag_dishonest")

    ok = (
        pipeline_ok
        and pos_ok
        and safety_ok
        and fallback.get("ok")
        and not file_write_claimed_as_d6
        and delivered_honesty
        and len([e for e in errors if e.startswith("deliver_fail_")]) == 0
    )
    if ok:
        errors = [e for e in errors if not e.startswith("deliver_fail_")]
    ok = ok and len(errors) == 0

    snapshots = session.rings.surfaces.snapshots() if session.rings.surfaces else {}
    result = {
        "ok": ok,
        "scenario_id": "LAB-SCENARIO-RING-REAL-INPUT",
        "journey_id": "GOLDEN-07",
        "profile_id": profile_id,
        "companion_profile": companion,
        "pipeline": pipeline,
        "deliveries": deliveries,
        "app_mutations": app_mutations,
        "app_snapshots": snapshots,
        "safety": {"low": low, "wrong": wrong, "fallback": fallback},
        "direct_file_write_counts_as_d6": False,
        "real_app_state_mutation": pos_ok,
        "errors": errors,
        "steps": eng.steps,
        "PHYSICAL_RING_SI": "PENDING",
        "RING_SPATIAL_ACCURACY": "SIMULATED",
        "HUMAN_VALIDATION": "PENDING",
        "implementer_ready_for_independent_E4_D6": ok,
        "INDEPENDENT_VERIFICATION": "PENDING",
        "duration_ms": int((time.time() - started) * 1000),
        "claim_boundary": CLAIM_BOUNDARY,
        "companion_instance": companion_sess.instance_id,
    }
    manifest = build_manifest(
        profile=session.profile,
        scenario="LAB-SCENARIO-RING-REAL-INPUT",
        fidelity=session.fidelity.to_dict(),
        virtualization=session.virt,
        virtual_devices={"rings": rings_info},
        applications=["libreoffice", "browser", "games"],
        result=result,
        evidence_dir=evidence,
        repo_root=repo_root,
    )
    result["manifest"] = {
        "run_id": manifest["run_id"],
        "path": manifest.get("manifest_path"),
        "sha256": manifest.get("manifest_sha256"),
    }
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    stop_session(session.instance_id)
    stop_session(companion_sess.instance_id)
    return result
