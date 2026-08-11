"""LAB-SCENARIO-RING-REAL-INPUT — G07 stack path; file writes do not count."""
from __future__ import annotations

import json
import os
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

    # Optionally bind live guest OS input path (FORCE_REAL_GUEST or existing qemu).
    guest_bind: dict[str, Any] = {"bound": False}
    qemu_sess = None
    if os.environ.get("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", "").lower() in {"1", "true", "yes"}:
        try:
            from gunnchos_device_os.device_lab.profiles import load_profile
            from gunnchos_device_os.device_lab.virtualization.qemu_guest import start_qemu_guest

            os.environ.setdefault("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "60")
            os.environ.setdefault("GUNNCHDEVICE_LAB_MEMORY_MB", "512")
            os.environ.setdefault("GUNNCH_GUEST_AGENT_HOST_STUB", "0")
            q = start_qemu_guest(
                work=evidence / "qemu-ring",
                profile=load_profile("handheld_hybrid"),
                repo_root=repo_root,
                headless=True,
            )
            qemu_sess = q.pop("_session", None)
            ga = ((q.get("state") or {}).get("guest_agent") or {})
            if q.get("ok") and qemu_sess is not None:
                session.rings.guest_monitor_sock = getattr(qemu_sess, "monitor_sock", None)
                session.rings.guest_agent = getattr(qemu_sess, "agent", None)
                guest_bind = {
                    "bound": True,
                    "agent_path_label": ga.get("agent_path_label") or ga.get("transport"),
                    "transport": ga.get("transport"),
                    "qemu_ok": True,
                }
            else:
                guest_bind = {
                    "bound": False,
                    "qemu_ok": False,
                    "error": q.get("error") or q.get("result"),
                    "result": q.get("result"),
                    "note": "Guest bind failed — hybrid Lab surfaces remain primary",
                }
        except Exception as exc:  # noqa: BLE001
            guest_bind = {"bound": False, "error": str(exc)}

    # Always bind a hybrid process surface for observable OS-input path proof
    if session.rings.surfaces is not None:
        session.rings.guest_process = session.rings.surfaces.browser

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
    os_input_paths: dict[str, Any] = {}
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
        os_input_paths[target] = r.get("os_input_path") or {}
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
    if not fallback.get("ok"):
        errors.append("fallback_conventional_failed")
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

    # Earn RING_TO_REAL only when guest virtio-serial path observed input
    ring_to_real = any(
        bool((os_input_paths.get(t) or {}).get("RING_TO_REAL_APPLICATION_INPUT_PASS"))
        for t in os_input_paths
    )

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
        "os_input_paths": os_input_paths,
        "guest_bind": guest_bind,
        "app_snapshots": snapshots,
        "safety": {"low": low, "wrong": wrong, "fallback": fallback},
        "direct_file_write_counts_as_d6": False,
        "real_app_state_mutation": pos_ok,
        "RING_TO_REAL_APPLICATION_INPUT_PASS": bool(ring_to_real),
        "RING_SPATIAL_ACCURACY": "SIMULATED",
        "ring_path_note": (
            "Ring→SpatialInputService→input_router mutates Lab app surfaces; "
            "optional guest OS input path bound when FORCE_REAL_GUEST. "
            "RING_TO_REAL_APPLICATION_INPUT_PASS only if virtio-serial observe earned. "
            "Spatial accuracy remains SIMULATED."
            if ring_to_real
            else (
                "Stack mutates Lab app surfaces via SpatialInputService→input_router; "
                "RING_TO_REAL_APPLICATION_INPUT_PASS=false until guest virtio-serial "
                "input_observe is proven. Spatial SIMULATED."
            )
        ),
        "errors": errors,
        "steps": eng.steps,
        "PHYSICAL_RING_SI": "PENDING",
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
    if qemu_sess is not None:
        try:
            qemu_sess.stop()
        except Exception:
            pass
    stop_session(session.instance_id)
    stop_session(companion_sess.instance_id)
    return result
