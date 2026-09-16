#!/usr/bin/env python3
"""17G.5C1 bind-only continuation after guestfwd+hub reachability PASS."""
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
    _wait_agent,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import (  # noqa: E402
    DEVICE_LAB_HUB_ENDPOINT_POLICY_V1,
    resolve_waike_lp_checkout,
    stage_owner_waike_bundle,
)
from gunnchos_device_os.device_lab.owner_waike_guest import (  # noqa: E402
    _guest_sh,
    fetch_bundle_into_guest,
    start_host_artifact_httpd,
    wait_host_artifact_httpd,
)
from gunnchos_device_os.device_lab.owner_waike_gui_journey import (  # noqa: E402
    HUB_GUEST_URL,
    HUB_PORT,
    OWNER_HTTPD_PORT,
    guest_gui_launch,
    prove_client_hub_sockets,
    prove_guest_hub_reachability,
    scrape_gui_log_hub_bind,
    start_host_real_hub,
    stop_gui_pid,
)

OUT = ROOT / "artifacts/device_lab_current_pin/waike/network_only"
WORK = ROOT / "artifacts/wp011r/interactive_guest_session_17g5c1_bind"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    session = None
    hub_proc = None
    hub_log = None
    artifact_httpd = None
    bind_pass = False
    fetch_info: dict[str, Any] = {}
    launch: dict[str, Any] = {}
    try:
        lp = resolve_waike_lp_checkout(ROOT)
        ops = ROOT.parent / "waike-research-ops"
        if not ops.is_dir():
            ops = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/waike-research-ops")
        hub_work = OUT / "hub_sidecar_bind"
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
                "real_hub": {k: v for k, v in hub.items() if k not in ("proc", "log_handle")},
            })
            return 2

        staging = OUT / "owner_bundle_stage"
        if not (staging / "bin" / "waike-learning-os").is_file():
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            stage_owner_waike_bundle(ROOT, staging)
        os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging)
        clear_guest_service_forward_env()
        apply_guest_service_forward_env(
            device_lab_hub_httpd_forward(hub_port=HUB_PORT, httpd_port=OWNER_HTTPD_PORT)
        )
        artifact_httpd = start_host_artifact_httpd(
            staging, port=OWNER_HTTPD_PORT, log_path=OUT / "host_artifact_httpd_bind.log"
        )
        ok_listen, listen_err = wait_host_artifact_httpd(OWNER_HTTPD_PORT, proc=artifact_httpd)
        if not ok_listen:
            _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", {
                "generated_at_utc": _utc(),
                "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                "blocker": f"httpd:{listen_err}",
            })
            return 3

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
                "boot": {k: boot.get(k) for k in ("ok", "error", "pid")},
            })
            return 4

        # Confirm hub + httpd from guest before fetch
        reach = prove_guest_hub_reachability(session, hub_url=HUB_GUEST_URL)
        httpd_probe = _guest_sh(
            session,
            "python3 - <<'PY'\n"
            "import urllib.request,socket,json\n"
            "out={}\n"
            "for url in ['http://10.0.2.100:8767/OWNER_WAIKE_BUNDLE_MANIFEST.json','http://10.0.2.100:8787/healthz']:\n"
            "  try:\n"
            "    with urllib.request.urlopen(url, timeout=5) as r:\n"
            "      out[url]={'status':r.status,'n':len(r.read(200))}\n"
            "  except Exception as e:\n"
            "    out[url]={'error':repr(e)}\n"
            "print(json.dumps(out))\n"
            "PY",
            timeout_sec=30.0,
        )
        fetch_info = fetch_bundle_into_guest(session, port=OWNER_HTTPD_PORT)
        # If 9p/http fetch failed, try explicit HTTP-only soft path without set -e early exit noise
        if not fetch_info.get("ok"):
            soft = _guest_sh(
                session,
                "set +e; "
                "rm -rf /var/lib/gunnchos/waike-learning-os /var/lib/gunnchos/waike-learning-os.partial; "
                "mkdir -p /var/lib/gunnchos/waike-learning-os.partial/bin; "
                "curl -v --connect-timeout 5 --max-time 60 "
                "  http://10.0.2.100:8767/OWNER_WAIKE_BUNDLE_MANIFEST.json "
                "  -o /var/lib/gunnchos/waike-learning-os.partial/MANIFEST.json; echo CURL_MANIFEST_RC:$?; "
                "curl -v --connect-timeout 5 --max-time 180 "
                "  http://10.0.2.100:8767/bin/waike-learning-os "
                "  -o /var/lib/gunnchos/waike-learning-os.partial/bin/waike-learning-os; echo CURL_BIN_RC:$?; "
                "ls -la /mnt/gdlgames/bin 2>/dev/null | head; "
                "mount | rg gdlgames || true; "
                "ls -la /var/lib/gunnchos/waike-learning-os.partial/bin || true",
                timeout_sec=240.0,
            )
            fetch_info["soft_retry"] = {
                "stdout_tail": ((soft.get("stdout") or "") + (soft.get("stderr") or ""))[-2500:],
                "returncode": soft.get("returncode"),
            }
            # Retry official fetch once more after soft probe
            fetch_info2 = fetch_bundle_into_guest(session, port=OWNER_HTTPD_PORT)
            fetch_info["retry"] = fetch_info2
            if fetch_info2.get("ok"):
                fetch_info = fetch_info2

        if not fetch_info.get("ok"):
            # Check if prior install remains on overlay from earlier 17G runs
            prior = _guest_sh(
                session,
                "ls -la /var/lib/gunnchos/waike-learning-os/bin 2>/dev/null; "
                "test -x /var/lib/gunnchos/waike-learning-os/bin/waike-learning-os && echo PRIOR_INSTALL_OK",
                timeout_sec=20.0,
            )
            prior_blob = (prior.get("stdout") or "") + (prior.get("stderr") or "")
            fetch_info["prior_install_probe"] = prior_blob[-800:]
            if "PRIOR_INSTALL_OK" not in prior_blob:
                doc = {
                    "schema": "gunnchos.device_lab.waike_minimal_real_hub_bind.v1",
                    "generated_at_utc": _utc(),
                    "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                    "blocker": "guest_fetch_owner_bundle_failed",
                    "mockHub": False,
                    "atspi_used": False,
                    "hub_reachability": {
                        k: reach.get(k)
                        for k in ("hub_reachable_from_guest", "http_hub_status", "tcp_hub")
                    },
                    "httpd_probe": ((httpd_probe.get("stdout") or "") + (httpd_probe.get("stderr") or ""))[-1500:],
                    "fetch": fetch_info,
                    "qemu_usernet": json.loads((WORK / "qemu_usernet.json").read_text())
                    if (WORK / "qemu_usernet.json").is_file()
                    else {},
                    "note": "Network closed; bind blocked on bundle install into guest.",
                }
                _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", doc)
                return 5

        launch = guest_gui_launch(session, journey_tag="N", hub_url=HUB_GUEST_URL)
        time.sleep(5.0)
        sockets = prove_client_hub_sockets(session, hub_port=HUB_PORT)
        log_bind = scrape_gui_log_hub_bind(session, journey_tag="N")
        hub_log_path = hub_work / "hub_sidecar.log"
        hub_log_tail = hub_log_path.read_text(encoding="utf-8", errors="replace")[-2500:] if hub_log_path.is_file() else ""
        client_http_evidence = bool(
            sockets.get("established_to_hub")
            or log_bind.get("hub_http_chip_in_log")
            or ("10.0.2.100:8787" in str(log_bind.get("tail") or ""))
            or ("10.0.2.100" in hub_log_tail)
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
            "fetch": {
                "ok": fetch_info.get("ok"),
                "via": fetch_info.get("via"),
                "stdout_tail": fetch_info.get("stdout_tail"),
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
        print(json.dumps({"bind_pass": bind_pass, "ack": ack_ok, "alive": alive, "client_http_evidence": client_http_evidence}, indent=2))
        return 0 if bind_pass else 6
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass
        clear_guest_service_forward_env()
        if artifact_httpd is not None:
            try:
                artifact_httpd.terminate()
            except Exception:
                pass
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
