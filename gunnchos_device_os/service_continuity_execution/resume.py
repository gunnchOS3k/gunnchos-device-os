"""NET-ORCH-029 — session resume A→B→C across fresh processes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import BearerClass, ContinuityState, ServiceSession


def save_session_checkpoint(session: ServiceSession, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), sort_keys=True, indent=2), encoding="utf-8")


def load_session_checkpoint(path: Path) -> ServiceSession:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ServiceSession(
        session_id=data["session_id"],
        service_name=data["service_name"],
        bearer=BearerClass(data["bearer"]),
        checkpoint=dict(data.get("checkpoint") or {}),
        sequence=int(data.get("sequence") or 0),
        continuity_state=ContinuityState(data.get("continuity_state") or ContinuityState.RESUMING.value),
    )


def resume_session(session: ServiceSession, *, progress_key: str = "cursor") -> ServiceSession:
    """Resume from checkpoint when seamless transition is impossible."""
    cursor = int(session.checkpoint.get(progress_key, 0))
    session.checkpoint[progress_key] = cursor
    session.checkpoint["resumed"] = True
    session.continuity_state = ContinuityState.RESUMING
    session.sequence += 1
    return session


def _write_worker(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "from pathlib import Path",
                "sys.path.insert(0, sys.argv[1])",
                "from gunnchos_device_os.service_continuity_execution.resume import (",
                "    load_session_checkpoint, resume_session, save_session_checkpoint,",
                ")",
                "from gunnchos_device_os.service_continuity_execution.models import (",
                "    BearerClass, ContinuityState, ServiceSession,",
                ")",
                "root = Path(sys.argv[2])",
                "phase = sys.argv[3]",
                "ckpt = root / 'session_checkpoint.json'",
                "meta = root / f'meta_{phase}.json'",
                "if phase == 'A':",
                "    a = ServiceSession(",
                "        session_id='sess-wave006-001',",
                "        service_name='learning_stream',",
                "        bearer=BearerClass.WIFI,",
                "        checkpoint={'cursor': 42, 'chapter': 'intro'},",
                "        sequence=1,",
                "        continuity_state=ContinuityState.HEALTHY,",
                "    )",
                "    save_session_checkpoint(a, ckpt)",
                "    meta.write_text(json.dumps({'pid': os.getpid(), 'cursor': 42, 'sequence': 1}), encoding='utf-8')",
                "elif phase == 'B':",
                "    b = load_session_checkpoint(ckpt)",
                "    b = resume_session(b)",
                "    save_session_checkpoint(b, ckpt)",
                "    meta.write_text(json.dumps({",
                "        'pid': os.getpid(),",
                "        'cursor': int(b.checkpoint['cursor']),",
                "        'resumed': bool(b.checkpoint.get('resumed')),",
                "        'sequence': b.sequence,",
                "        'state': b.continuity_state.value,",
                "    }), encoding='utf-8')",
                "elif phase == 'C':",
                "    c = load_session_checkpoint(ckpt)",
                "    meta.write_text(json.dumps({",
                "        'pid': os.getpid(),",
                "        'cursor': int(c.checkpoint.get('cursor', -1)),",
                "        'resumed': bool(c.checkpoint.get('resumed')),",
                "        'sequence': c.sequence,",
                "        'state': c.continuity_state.value,",
                "    }), encoding='utf-8')",
                "else:",
                "    raise SystemExit('bad phase')",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prove_session_resume_a_b_c(storage_dir: Path) -> dict[str, Any]:
    """Fresh OS processes A→B→C (same-object / same-PID insufficient)."""
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[2]
    worker = storage_dir / "_resume_worker.py"
    _write_worker(worker)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    pids: dict[str, int] = {}
    for phase in ("A", "B", "C"):
        subprocess.check_call(
            [sys.executable, str(worker), str(repo_root), str(storage_dir), phase],
            env=env,
            cwd=str(repo_root),
        )
        meta = json.loads((storage_dir / f"meta_{phase}.json").read_text(encoding="utf-8"))
        pids[phase] = int(meta["pid"])

    meta_b = json.loads((storage_dir / "meta_B.json").read_text(encoding="utf-8"))
    meta_c = json.loads((storage_dir / "meta_C.json").read_text(encoding="utf-8"))
    distinct_pids = len(set(pids.values())) == 3
    ok = (
        distinct_pids
        and meta_b["cursor"] == 42
        and meta_c["cursor"] == 42
        and meta_b["resumed"] is True
        and meta_c["resumed"] is True
        and meta_b["sequence"] == 2
        and meta_c["sequence"] == 2
        and meta_c["state"] == ContinuityState.RESUMING.value
    )
    return {
        "schema": "gunnchos.engineering_wave006.session_resume_a_b_c.v1",
        "ok": ok,
        "fresh_process_required": True,
        "distinct_pids": distinct_pids,
        "pids": pids,
        "process_b_cursor": meta_b["cursor"],
        "process_c_cursor": meta_c["cursor"],
        "process_b_resumed": meta_b["resumed"],
        "process_c_resumed": meta_c["resumed"],
        "process_c_sequence": meta_c["sequence"],
        "LIVE_CARRIER_HANDOVER_VALIDATED": False,
    }
