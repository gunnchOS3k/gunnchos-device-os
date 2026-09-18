"""CX QEMU slot lock — never kill foreign guests."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

LOCK_PATH = Path("/tmp/gunnchos-cx-qemu.lock")
FOREIGN_BUSY = "CX2G_QEMU_SLOT_BUSY_FOREIGN_PROCESS"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_lock() -> Optional[Dict[str, Any]]:
    if not LOCK_PATH.is_file():
        return None
    try:
        return json.loads(LOCK_PATH.read_text())
    except Exception:
        return None


def acquire_lock(
    *,
    branch: str,
    repo: str,
    purpose: str,
    monitor: str,
    ssh_port: int,
    wait_s: int = 90,
    poll_s: float = 3.0,
) -> Dict[str, Any]:
    """Acquire CX QEMU slot. Only steal if prior lock PID is dead or owned by CX2G purpose."""
    deadline = time.time() + wait_s
    while True:
        cur = read_lock()
        if cur:
            pid = int(cur.get("pid") or 0)
            alive = pid > 0 and _pid_alive(pid)
            owned = (
                str(cur.get("purpose", "")).startswith(("CX2F", "CX2G", "CX2H", "CX3"))
                or str(cur.get("branch", "")).startswith(("eng/cx2f", "eng/cx2g", "eng/cx2h", "eng/cx3"))
            )
            if alive and not owned:
                if time.time() >= deadline:
                    return {"ok": False, "blocker": FOREIGN_BUSY, "foreign": cur}
                time.sleep(poll_s)
                continue
            if alive and owned and pid != os.getpid():
                # prior CX2G holder still alive — wait then fail
                if time.time() >= deadline:
                    return {"ok": False, "blocker": FOREIGN_BUSY, "foreign": cur}
                time.sleep(poll_s)
                continue
            # stale lock
            try:
                LOCK_PATH.unlink()
            except OSError:
                pass
        meta = {
            "pid": os.getpid(),
            "branch": branch,
            "repo": repo,
            "purpose": purpose,
            "start_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "monitor": monitor,
            "ssh_port": ssh_port,
            "wave": "CX2G",
        }
        tmp = LOCK_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=2) + "\n")
        os.replace(tmp, LOCK_PATH)
        return {"ok": True, "lock": meta}


def release_lock(*, only_if_pid: Optional[int] = None) -> None:
    cur = read_lock()
    if not cur:
        return
    if only_if_pid is not None and int(cur.get("pid") or 0) != only_if_pid:
        return
    if int(cur.get("pid") or 0) not in (0, os.getpid(), only_if_pid or -1):
        # do not clear foreign
        if _pid_alive(int(cur["pid"])):
            return
    try:
        LOCK_PATH.unlink()
    except OSError:
        pass


def qemu_owned_by_cx2g(pidfile: Path, lock: Optional[Dict[str, Any]] = None) -> bool:
    lock = lock or read_lock()
    if not lock:
        return False
    if not str(lock.get("purpose", "")).startswith(("CX2G", "CX2H")):
        return False
    if not pidfile.is_file():
        return False
    try:
        qpid = int(pidfile.read_text().strip())
    except Exception:
        return False
    return _pid_alive(qpid)
