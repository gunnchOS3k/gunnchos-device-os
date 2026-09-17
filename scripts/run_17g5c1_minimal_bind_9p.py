#!/usr/bin/env python3
"""17G.5C1 bind-only via 9p install (avoid HTTP stall after guestfwd proof)."""
from __future__ import annotations

import json
import os
import shutil
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.guest_service_forward import (  # noqa: E402
    apply_guest_service_forward_env,
    clear_guest_service_forward_env,
    device_lab_hub_httpd_forward,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _recover_guest_agent,
    _wait_agent,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import (  # noqa: E402
    DEVICE_LAB_HUB_ENDPOINT_POLICY_V1,
    resolve_waike_lp_checkout,
    stage_owner_waike_bundle,
)
from gunnchos_device_os.device_lab.owner_waike_guest import _guest_sh  # noqa: E402
from gunnchos_device_os.device_lab.owner_waike_gui_journey import (  # noqa: E402
    HUB_GUEST_URL,
    HUB_PORT,
    OWNER_HTTPD_PORT,
    guest_gui_launch,
    prove_client_hub_sockets,
    scrape_gui_log_hub_bind,
    start_host_real_hub,
    stop_gui_pid,
)

OUT = ROOT / "artifacts/device_lab_current_pin/waike/network_only"
WORK = ROOT / "artifacts/wp011r/interactive_guest_session_17g5c1_bind2"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def install_via_9p(session: Any) -> dict[str, Any]:
    marker = f"WAIKE9P_{int(time.time())}"
    cmd = (
        f"set -euo pipefail; MARKER={marker}; echo START_$MARKER; "
        "mkdir -p /mnt/gdlgames; "
        "mount -t 9p -o trans=virtio,version=9p2000.L gdlgames /mnt/gdlgames 2>/dev/null || true; "
        "ls -la /mnt/gdlgames/bin | head; "
        "test -f /mnt/gdlgames/bin/waike-learning-os; "
        "rm -rf /var/lib/gunnchos/waike-learning-os; "
        "mkdir -p /var/lib/gunnchos/waike-learning-os; "
        "cp -a /mnt/gdlgames/. /var/lib/gunnchos/waike-learning-os/; "
        "chmod +x /var/lib/gunnchos/waike-learning-os/bin/waike-learning-os "
        "  /var/lib/gunnchos/waike-learning-os/bin/waike-learning-os.qemu-x86_64-wrapper.sh || true; "
        "ls -la /var/lib/gunnchos/waike-learning-os/bin; "
        f"echo FETCH_OK_$MARKER"
    )
    r = _guest_sh(session, cmd, timeout_sec=180.0)
    blob = (r.get("stdout") or "") + (r.get("stderr") or "")
    return {
        "ok": f"FETCH_OK_{marker}" in blob,
        "via": "9p",
        "marker": marker,
        "stdout_tail": blob[-2000:],
        "returncode": r.get("returncode"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    session = None
    hub_proc = None
    hub_log = None
    try:
        lp = resolve_waike_lp_checkout(ROOT)
        ops = ROOT.parent / "waike-research-ops"
        if not ops.is_dir():
            ops = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/waike-research-ops")
        hub_work = OUT / "hub_sidecar_bind2"
        if hub_work.exists():
            shutil.rmtree(hub_work, ignore_errors=True)
        hub_work.mkdir(parents=True, exist_ok=True)
        hub = start_host_real_hub(lp, ops, hub_work)
        hub_proc = hub.pop("proc", None)
        hub_log = hub.pop("log_handle", None)
        if not hub.get("ok"):
            _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", {
                "generated_at_utc": _utc(),
                "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                "blocker": "real_hub_sidecar_failed_to_start",
                "mockHub": False,
            })
            return 2

        staging = OUT / "owner_bundle_stage"
        if not (staging / "bin" / "waike-learning-os").is_file():
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            stage_owner_waike_bundle(ROOT, staging)
        os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging)
        clear_guest_service_forward_env()
        # Hub-only guestfwd is enough for bind; keep httpd rule for policy parity.
        apply_guest_service_forward_env(
            device_lab_hub_httpd_forward(hub_port=HUB_PORT, httpd_port=OWNER_HTTPD_PORT)
        )

        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True, exist_ok=True)
        boot = boot_interactive_guest(ROOT, WORK, dual=False, boot_timeout_s=240, memory_mb=4096)
        session = boot.pop("_session", None)
        if not boot.get("ok") or session is None or not _wait_agent(session, tries=50, sleep_s=1.0):
            _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", {
                "generated_at_utc": _utc(),
                "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                "blocker": boot.get("error") or "boot_or_agent_failed",
                "mockHub": False,
            })
            return 3

        # Bounded TCP-only hub check (no urllib) to avoid agent stall.
        tcp = _guest_sh(
            session,
            "python3 - <<'PY'\n"
            "import socket,json\n"
            "ok=False\n"
            "try:\n"
            "  s=socket.create_connection(('10.0.2.100',8787),timeout=3); s.close(); ok=True\n"
            "except Exception as e:\n"
            "  print(json.dumps({'tcp_ok':False,'error':repr(e)})); raise SystemExit\n"
            "print(json.dumps({'tcp_ok':ok}))\n"
            "PY",
            timeout_sec=20.0,
        )
        tcp_blob = (tcp.get("stdout") or "") + (tcp.get("stderr") or "")
        if '"tcp_ok": true' not in tcp_blob and '"tcp_ok":true' not in tcp_blob:
            _recover_guest_agent(session)
            time.sleep(2)
            tcp = _guest_sh(
                session,
                "python3 -c \"import socket; s=socket.create_connection(('10.0.2.100',8787),timeout=3); s.close(); print('TCP_HUB_OK')\"",
                timeout_sec=20.0,
            )
            tcp_blob = (tcp.get("stdout") or "") + (tcp.get("stderr") or "")

        fetch = install_via_9p(session)
        if not fetch.get("ok"):
            _recover_guest_agent(session)
            time.sleep(2)
            fetch = install_via_9p(session)
        if not fetch.get("ok"):
            _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", {
                "schema": "gunnchos.device_lab.waike_minimal_real_hub_bind.v1",
                "generated_at_utc": _utc(),
                "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                "blocker": "guest_9p_bundle_install_failed",
                "mockHub": False,
                "atspi_used": False,
                "tcp_probe": tcp_blob[-500:],
                "fetch": fetch,
                "note": "Network closed earlier; bind blocked on 9p install.",
            })
            return 4

        launch = guest_gui_launch(session, journey_tag="N", hub_url=HUB_GUEST_URL)
        time.sleep(6.0)
        sockets = prove_client_hub_sockets(session, hub_port=HUB_PORT)
        log_bind = scrape_gui_log_hub_bind(session, journey_tag="N")
        hub_log_path = hub_work / "hub_sidecar.log"
        hub_log_tail = hub_log_path.read_text(encoding="utf-8", errors="replace")[-2500:] if hub_log_path.is_file() else ""
        client_http_evidence = bool(
            sockets.get("established_to_hub")
            or log_bind.get("hub_http_chip_in_log")
            or ("10.0.2.100:8787" in str(log_bind.get("tail") or ""))
            or ("GET /" in hub_log_tail)
        )
        ack_ok = bool(launch.get("acknowledged") or launch.get("launched_gui"))
        alive = bool(launch.get("alive_beyond_ipc_ack") or launch.get("alive_after_3s"))
        bind_pass = bool(
            ack_ok
            and alive
            and launch.get("hub_url") == HUB_GUEST_URL
            and client_http_evidence
            and not launch.get("headless")
        )
        doc = {
            "schema": "gunnchos.device_lab.waike_minimal_real_hub_bind.v1",
            "generated_at_utc": _utc(),
            "hub_url": HUB_GUEST_URL,
            "policy": DEVICE_LAB_HUB_ENDPOINT_POLICY_V1,
            "tcp_probe": tcp_blob[-500:],
            "fetch": {
                "ok": fetch.get("ok"),
                "via": fetch.get("via"),
                "stdout_tail": fetch.get("stdout_tail"),
            },
            "launch": {
                k: launch.get(k)
                for k in (
                    "acknowledged",
                    "alive_beyond_ipc_ack",
                    "alive_after_3s",
                    "launched_gui",
                    "hub_url",
                    "nack_reason",
                    "pid",
                    "fixture_rejected",
                    "headless",
                    "xvfb_primary",
                )
            },
            "client_sockets": {
                k: sockets.get(k)
                for k in ("ok", "established_to_hub", "procs", "ss_tail", "errors")
            },
            "gui_log_bind": {
                k: log_bind.get(k)
                for k in (
                    "ok",
                    "hub_http_chip_in_log",
                    "hub_mock_in_log",
                    "hub_unavailable_in_log",
                    "runtime_hub_url_seen",
                    "tail",
                )
            },
            "hub_log_tail": hub_log_tail,
            "mockHub": False,
            "atspi_used": False,
            "WAIKE_REAL_HUB_CLIENT_BIND_PASS": bind_pass,
        }
        _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", doc)
        try:
            stop_gui_pid(session, "N")
        except Exception:
            pass
        print(json.dumps({
            "bind_pass": bind_pass,
            "ack": ack_ok,
            "alive": alive,
            "client_http_evidence": client_http_evidence,
            "fetch_ok": fetch.get("ok"),
        }, indent=2))
        return 0 if bind_pass else 5
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass
        clear_guest_service_forward_env()
        if hub_proc is not None:
            try:
                hub_proc.terminate()
                hub_proc.wait(timeout=10)
            except Exception:
                try:
                    hub_proc.kill()
                except Exception:
                    pass
        if hub_log is not None:
            try:
                hub_log.close()
            except Exception:
                pass
        pid_file = WORK / "qemu.pid"
        if pid_file.is_file():
            try:
                os.kill(int(pid_file.read_text().strip()), signal.SIGTERM)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
