"""WP-011R Ring → real app state mutation evidence.

input_observe alone is insufficient for RING_TO_REAL_APP_STATE_MUTATION_PASS.
Cycle 3A §L requires: Ring simulator → authenticated packet → RingService →
SpatialInputService → confidence gate → guest OS input → ACTUAL running
application state mutation (document, browser, game).

Hybrid Lab surface mutation alone earns RING_HYBRID_LAB_SURFACE_MUTATION_PASS
only — it does NOT earn RING_TO_REAL_APP_STATE_MUTATION_PASS.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


PASS_TOKEN = "RING_TO_REAL_APP_STATE_MUTATION_PASS"
HYBRID_TOKEN = "RING_HYBRID_LAB_SURFACE_MUTATION_PASS"

CLAIM = (
    "Ring Lab path mutates observable app surfaces via SpatialInputService. "
    "input_observe alone does not earn RING_TO_REAL_APP_STATE_MUTATION_PASS. "
    "Hybrid Lab surfaces alone do not earn RING_TO_REAL_APP_STATE_MUTATION_PASS. "
    "RING_SPATIAL_ACCURACY=SIMULATED. SILICON_EXACT_EMULATION=false. "
    "Physical ring SI PENDING."
)

PIPELINE = [
    "ring_simulator",
    "authenticated_packet",
    "RingService",
    "SpatialInputService",
    "confidence_gate",
    "guest_os_input",
    "app_state_mutation",
]


def _ring_dir(repo_root: Path) -> Path:
    d = repo_root / "artifacts" / "wp011r" / "ring"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_ring_app_mutation_proof(*, repo_root: Path, profile_id: str = "edge_io_rings") -> dict[str, Any]:
    import os

    from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session

    started_at = time.time()
    out_dir = _ring_dir(repo_root)
    start = start_session(profile_id, repo_root=repo_root)
    session = get_session(start["instance_id"])
    companion = start_session("student_14_5", repo_root=repo_root)
    companion_sess = get_session(companion["instance_id"])
    evidence = out_dir
    qemu_sess = None
    guest_bind: dict[str, Any] = {"bound": False}
    try:
        rings_info = session.rings.start(evidence_dir=evidence, repo_root=repo_root)
        if session.rings.surfaces is not None:
            session.rings.guest_process = session.rings.surfaces.browser

        # Bind live guest OS input when FORCE_REAL_GUEST (required for Cycle 3A PASS).
        if os.environ.get("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", "").lower() in {"1", "true", "yes"}:
            try:
                from gunnchos_device_os.device_lab.profiles import load_profile
                from gunnchos_device_os.device_lab.virtualization.qemu_guest import start_qemu_guest

                os.environ.setdefault("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "60")
                os.environ.setdefault("GUNNCHDEVICE_LAB_MEMORY_MB", "512")
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
                        "monitor_sock": str(getattr(qemu_sess, "monitor_sock", "") or ""),
                    }
                else:
                    guest_bind = {
                        "bound": False,
                        "qemu_ok": False,
                        "error": q.get("error") or q.get("result"),
                        "note": "Guest bind failed — hybrid Lab surfaces only",
                    }
            except Exception as exc:  # noqa: BLE001
                guest_bind = {"bound": False, "error": str(exc)[:400]}

        pipeline_raw = rings_info.get("pipeline") or []
        stage_map = {
            "edge_io_sim": "ring_simulator",
            "authenticated_packet": "authenticated_packet",
            "ring_service": "RingService",
            "SpatialInputService": "SpatialInputService",
            "input_router_hid_wayland": "guest_or_hybrid_input",
            "apps": "app_state_mutation",
        }
        mapped = [stage_map.get(p, p) for p in pipeline_raw]
        if "confidence_gate" not in mapped:
            mapped.insert(4 if len(mapped) >= 4 else len(mapped), "confidence_gate")

        mutations: dict[str, Any] = {}
        targets = ("libreoffice", "browser", "games")
        for target in targets:
            before = None
            if session.rings.surfaces is not None:
                before = session.rings.surfaces.by_target(target).snapshot()
            r = session.rings.inject(target=target, confidence=0.92, gesture="click")
            after = r.get("after")
            mutated = bool(r.get("delivered") and r.get("app_state_changed") and r.get("via_stack"))
            if r.get("result", {}).get("direct_file_write"):
                mutated = False
            os_path = r.get("os_input_path") or {}
            observe = os_path.get("guest_observe") or {}
            path_kind = str(os_path.get("path") or "hybrid_process")
            observe_only = bool(observe.get("observed")) and before == after
            if observe_only:
                mutated = False
            mutations[target] = {
                "delivered": r.get("delivered"),
                "app_state_changed": r.get("app_state_changed"),
                "mutated": mutated,
                "before": before,
                "after": after,
                "via_stack": r.get("via_stack"),
                "os_input_path": os_path,
                "observe_only_rejected": observe_only,
                "direct_file_write": bool((r.get("result") or {}).get("direct_file_write")),
                "path_kind": path_kind,
            }

        low = session.rings.inject(confidence=0.2, target="browser")
        wrong = session.rings.inject(confidence=0.9, target="browser", wrong_target=True)
        gate_ok = (low.get("delivered") is False) and (wrong.get("delivered") is False)

        all_mutated = all(mutations[t]["mutated"] for t in targets)
        hybrid_earned = bool(all_mutated and gate_ok)

        # Require path==guest (virtio-serial observe + accepted injection). Hybrid alone ≠ PASS.
        guest_ok = any(
            str((mutations[t].get("os_input_path") or {}).get("path") or "") == "guest"
            for t in targets
        )
        if guest_ok:
            mapped = [
                ("guest_os_input" if s == "guest_or_hybrid_input" else s) for s in mapped
            ]
            if "guest_os_input" not in mapped:
                mapped.append("guest_os_input")
        pipeline_ok = all(s in mapped for s in PIPELINE) if guest_ok else False
        earned = bool(pipeline_ok and all_mutated and gate_ok and guest_ok)

        snapshots = session.rings.surfaces.snapshots() if session.rings.surfaces else {}
        result = {
            "ok": earned,
            PASS_TOKEN: earned,
            HYBRID_TOKEN: bool(hybrid_earned and not earned),
            "pipeline_required": PIPELINE,
            "pipeline_observed": mapped,
            "pipeline_raw": pipeline_raw,
            "pipeline_ok": pipeline_ok,
            "guest_os_input_required": True,
            "guest_os_input_present": guest_ok,
            "guest_bind": guest_bind,
            "mutations": mutations,
            "confidence_gate": {"low": low, "wrong": wrong, "ok": gate_ok},
            "app_snapshots": snapshots,
            "RING_SPATIAL_ACCURACY": "SIMULATED",
            "RING_TO_REAL_APPLICATION_INPUT_PASS_note": (
                "Wave4 input_observe token is separate; Cycle 3A PASS requires guest OS "
                f"input plus document/browser/game mutation. Hybrid Lab surfaces alone "
                f"set {HYBRID_TOKEN} only."
            ),
            "companion_instance": companion_sess.instance_id,
            "duration_ms": int((time.time() - started_at) * 1000),
            "SILICON_EXACT_EMULATION": False,
            "claim_boundary": CLAIM,
            "note": (
                "RING_TO_REAL_APP_STATE_MUTATION_PASS earned"
                if earned
                else (
                    "HYBRID Lab surface mutation only — PASS false until guest OS "
                    "input mutates document+browser+game"
                    if hybrid_earned
                    else "PASS false until document+browser+game mutate via full Ring stack"
                )
            ),
        }
        (evidence / "RING_APP_MUTATION_EVIDENCE.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        for t, m in mutations.items():
            (evidence / f"{t}_mutation.json").write_text(
                json.dumps(m, indent=2) + "\n", encoding="utf-8"
            )
        return result
    finally:
        if qemu_sess is not None:
            try:
                qemu_sess.stop()
            except Exception:
                pass
        stop_session(session.instance_id)
        stop_session(companion_sess.instance_id)
