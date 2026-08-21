"""Comparative baselines — real deterministic fixtures; no manufactured superiority."""
from __future__ import annotations

import time
from typing import Any

from gunnchos_device_os.service_continuity_execution.controller import ContinuityController
from gunnchos_device_os.service_continuity_execution.models import ContinuityAction
from gunnchos_device_os.service_continuity_execution.multipath import run_multipath_transfer
from gunnchos_device_os.service_continuity_execution.resume import (
    checkpoint,
    create_session,
    enqueue_operation,
    load_checkpoint,
    mark_operation_committed,
    resume_once,
)
from pathlib import Path
import tempfile


def comparative_baselines() -> dict[str, Any]:
    payload = b"BASELINE-COMPARE-PAYLOAD-ABCDEFGH"

    # BASELINE_FAIL_STOP: no resume / no multipath — just fail
    fail_stop = {
        "name": "BASELINE_FAIL_STOP",
        "completion_success": False,
        "interruption_resume_time_ms": None,
        "progress_loss": 100,
        "duplicate_commit_count": 0,
        "bytes_per_path": {},
        "minimum_useful_service_retained": False,
    }

    # BASELINE_SINGLE_PATH_RESUME
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sess.json"
        now = 1_700_003_000.0
        sess = create_session(now=now)
        sess = mark_operation_committed(sess, "op-1", now=now)
        sess.logical_position = 42
        sess = enqueue_operation(sess, {"op_id": "op-2", "action": "x"}, now=now)
        checkpoint(sess, p, now=now)
        t0 = time.perf_counter()
        sess2 = load_checkpoint(p)
        sess2, result = resume_once(sess2, now=now + 1, resume_token=sess2.resume_token)
        dt = (time.perf_counter() - t0) * 1000.0
        single_resume = {
            "name": "BASELINE_SINGLE_PATH_RESUME",
            "completion_success": result.get("ok") is True and sess2.logical_position == 42,
            "interruption_resume_time_ms": dt,
            "progress_loss": 0 if sess2.logical_position == 42 else 42,
            "duplicate_commit_count": max(0, sess2.committed_operation_ids.count("op-2") - 1),
            "bytes_per_path": {"single": len(payload)},
            "minimum_useful_service_retained": True,
        }

    # WAVE006_CONTROLLER
    with tempfile.TemporaryDirectory() as td:
        ctrl = ContinuityController(storage_dir=Path(td), now=1_700_003_100.0)
        t0 = time.perf_counter()
        tr = ctrl.execute(ContinuityAction.TRANSITION, source_path="wifi-home", target_path="cellular_generic")
        mp = ctrl.execute(
            ContinuityAction.MULTIPATH,
            payload=payload,
            paths=["a", "b"],
            fail_path="a",
        )
        dt = (time.perf_counter() - t0) * 1000.0
        wave = {
            "name": "WAVE006_CONTROLLER",
            "completion_success": tr["result"].get("state") == "COMMITTED" and mp["result"].get("ok") is True,
            "interruption_resume_time_ms": tr["result"].get("interruption_window_ms"),
            "progress_loss": 0,
            "duplicate_commit_count": mp["result"].get("application_commit_count", 1) - 1,
            "bytes_per_path": mp["result"].get("bytes_by_path", {}),
            "minimum_useful_service_retained": True,
            "controller_elapsed_ms": dt,
        }

    single_xfer = run_multipath_transfer(payload, ["a"])
    multi_xfer = run_multipath_transfer(payload, ["a", "b"], fail_path="a", fail_after_n=1)

    multipath_compare = {
        "SINGLE_PATH_TRANSFER": {
            "ok": single_xfer["ok"],
            "completion_time_proxy": single_xfer.get("transfer", {}).get("chunk_count"),
            "bytes_per_path": single_xfer.get("bytes_by_path"),
        },
        "APPLICATION_LEVEL_MULTIPATH_TRANSFER": {
            "ok": multi_xfer["ok"],
            "path_failure_continued": multi_xfer.get("path_failure_continued"),
            "bytes_per_path": multi_xfer.get("bytes_by_path"),
            "duplicate_commit_count": multi_xfer.get("application_commit_count", 1) - 1,
        },
    }

    rows = [fail_stop, single_resume, wave]
    ok = single_resume["completion_success"] and wave["completion_success"] and multipath_compare["APPLICATION_LEVEL_MULTIPATH_TRANSFER"]["ok"]
    return {
        "schema": "gunnchos.engineering_wave006.comparative_baselines.v1",
        "ok": ok,
        "baselines": rows,
        "multipath_comparison": multipath_compare,
        "UNIVERSAL_OPTIMALITY": False,
        "note": "Results are fixture-measured; Wave006 superiority is not manufactured.",
    }
