#!/usr/bin/env python3
"""Re-run ONLY four-game on one COW-backed guest. No second concurrent QEMU."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import (  # noqa: E402
    prepare_owner_guest_staging,
)
from gunnchos_device_os.device_lab.owner_four_game_guest import (  # noqa: E402
    attempt_owner_four_game_in_guest_pass,
)
from scripts.product_use_close_s1 import OUT  # noqa: E402


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"{_utc()} {msg}", flush=True)


def assert_no_qemu() -> None:
    try:
        out = subprocess.check_output(["pgrep", "-lf", "qemu-system-"], text=True).strip()
    except subprocess.CalledProcessError:
        return
    lines = [
        ln
        for ln in out.splitlines()
        if "qemu-system-" in ln
        and "pgrep" not in ln
        and "product_use_rerun" not in ln
        and "assert_no_qemu" not in ln
        and "/bin/zsh" not in ln
    ]
    if lines:
        raise SystemExit("REFUSING_SECOND_QEMU still_running:\n" + "\n".join(lines))


def clean_poweroff(session: Any, work: Path) -> dict[str, Any]:
    pid_path = work / "qemu.pid"
    pid = int(pid_path.read_text().strip()) if pid_path.exists() else None
    try:
        _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "sync; systemctl poweroff -i || poweroff"],
            timeout_sec=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f"poweroff_agent_err={exc}")
    mon = getattr(session, "monitor_sock", None)
    if mon:
        try:
            import socket

            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(str(mon))
            s.sendall(b"system_powerdown\n")
            s.close()
        except OSError:
            pass
    if not pid:
        return {"ok": False, "error": "no_pid"}
    for i in range(90):
        try:
            os.kill(pid, 0)
            time.sleep(1)
        except OSError:
            return {"ok": True, "exited": True, "wait_s": i}
    return {"ok": False, "exited": False, "error": "timeout_no_sigkill"}


def main() -> int:
    assert_no_qemu()
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "rc002"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    staging = prepare_owner_guest_staging(ROOT)
    _log(f"staging_ok={staging.get('ok')}")
    if not staging.get("ok"):
        raise SystemExit(f"staging_failed: {staging}")

    work = ROOT / "artifacts/wp011r/interactive_guest_session_four"
    work.mkdir(parents=True, exist_ok=True)
    for name in ("qemu.pid", "qemu_boot.log"):
        p = work / name
        if p.exists() or p.is_symlink():
            try:
                p.unlink()
            except OSError:
                pass
    tmpl = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
    if tmpl.is_file():
        shutil.copyfile(tmpl, work / "edk2-aarch64-vars.fd")

    _log("boot_four_game_cow")
    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=300, memory_mb=3072)
    session = boot.pop("_session", None)
    if not boot.get("ok") or session is None:
        result = {
            "ok": False,
            "boot": boot,
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
            "blocker": "boot_failed",
        }
        (OUT / "FOUR_GAME").mkdir(parents=True, exist_ok=True)
        (OUT / "FOUR_GAME" / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        _log(f"boot_failed {boot}")
        return 1

    try:
        for _ in range(40):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2)
        os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging.get("staging"))
        evid = _evidence_dir(ROOT, "games")
        _log("FOUR_GAME_start")
        result = attempt_owner_four_game_in_guest_pass(session, ROOT, evid)
    finally:
        power = clean_poweroff(session, work)
        _log(f"poweroff {power}")
        assert_no_qemu()

    (OUT / "FOUR_GAME").mkdir(parents=True, exist_ok=True)
    (OUT / "FOUR_GAME" / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    fg = ROOT / "artifacts/wp011r/games/four_games_in_guest.json"
    if fg.exists():
        shutil.copy2(fg, OUT / "FOUR_GAME" / "four_games_in_guest.json")
    _log(
        f"FOUR_GAME pass={result.get('FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS')} "
        f"blocker={result.get('blocker')}"
    )
    print(json.dumps(result, indent=2, default=str)[:4000], flush=True)
    return 0 if result.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
