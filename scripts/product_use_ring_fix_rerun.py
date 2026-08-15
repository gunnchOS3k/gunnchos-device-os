#!/usr/bin/env python3
"""Boot sealed+COW (or attach if alive) and rerun RING only. Never second QEMU."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PRODUCT_USE_RING_TIMEOUT_S", "600")
os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "rc002"
os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    boot_interactive_guest,
)
from scripts.product_use_attach_s1_continue import attach_session  # noqa: E402
from scripts.product_use_rerun_failed_legs import (  # noqa: E402
    assert_no_qemu,
    clean_poweroff,
    run_ring_child,
)
import scripts.product_use_rerun_failed_legs as _rerun_mod  # noqa: E402

_rerun_mod.RING_TIMEOUT_S = int(os.environ.get("PRODUCT_USE_RING_TIMEOUT_S", "600"))
OUT = ROOT / "artifacts" / "product_use"
WORK = OUT / "interactive_guest_session_resume_open"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"{_utc()} {msg}", flush=True)


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    session = None
    attach = {"ok": False}
    pid_path = WORK / "qemu.pid"
    if pid_path.exists():
        session, attach = attach_session(WORK)
        _log(f"attach_attempt {attach}")
    if session is None or not attach.get("ok"):
        assert_no_qemu()
        _log("booting sealed+COW")
        boot = boot_interactive_guest(ROOT, WORK, dual=False, boot_timeout_s=240, memory_mb=2560)
        session = boot.pop("_session", None)
        _log(f"boot_ok={boot.get('ok')} err={boot.get('error')}")
        (OUT / "RING_FIX_BOOT.json").write_text(
            json.dumps({k: v for k, v in boot.items() if k != "_session"}, indent=2, default=str)
            + "\n"
        )
        if not boot.get("ok") or session is None:
            return 2
    for i in range(40):
        if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
            _log(f"compositor ready i={i}")
            break
        time.sleep(2)
    _log("RING child start")
    ring = run_ring_child(WORK)
    br = (ring.get("mutations") or {}).get("browser") or {}
    wf = br.get("latency_waterfall") or ring.get("latency_waterfall") or []
    summary = {
        "at_utc": _utc(),
        "pass": ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"),
        "blocker": ring.get("blocker"),
        "PHYSICAL_RING_E6": ring.get("PHYSICAL_RING_E6"),
        "browser_mutated": br.get("mutated"),
        "first_broken_boundary": br.get("first_broken_boundary"),
        "before_text": br.get("before_text"),
        "after_text": br.get("after_text"),
        "libreoffice": ((ring.get("mutations") or {}).get("libreoffice") or {}).get("mutated"),
        "game": ((ring.get("mutations") or {}).get("game") or {}).get("mutated"),
        "waterfall": wf,
    }
    (OUT / "RING_FIX_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    _log(
        f"RING pass={summary['pass']} blocker={summary['blocker']} "
        f"browser={summary['browser_mutated']} lo={summary['libreoffice']} game={summary['game']}"
    )
    for w in wf:
        _log(f"WF {w.get('stage')} { {k: v for k, v in w.items() if k != 'stage'} }")
    _log("poweroff")
    clean_poweroff(session, WORK)
    _log("done")
    return 0 if summary.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
