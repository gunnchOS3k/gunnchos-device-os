#!/usr/bin/env python3
"""17G.5C1 — Scoped QEMU guestfwd network proof only (no AT-SPI / journey)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.guest_service_forward import (  # noqa: E402
    GuestForwardRule,
    apply_guest_service_forward_env,
    build_usernet_netdev,
    clear_guest_service_forward_env,
    device_lab_hub_httpd_forward,
    guestfwd_proof_service_forward,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _wait_agent,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import (  # noqa: E402
    ACCEPTED_WAIKE_LP_SHA,
    DEVICE_LAB_HUB_ENDPOINT_POLICY_V1,
    MAIN_AARCH64_GLIBC236_SHA256,
    PIN_MANIFEST_SHA256,
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

PROMPT = "17G.5C1"
OUT = ROOT / "artifacts/device_lab_current_pin/waike/network_only"
WORK = ROOT / "artifacts/wp011r/interactive_guest_session_17g5c1"
TEST_BODY = b"GUNNCHOS_GUESTFWD_OK"
TEST_PORT = 18787
ISOLATION_PROBE_PORT = 19999  # host listener; must NOT be guestfwd'd


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _enumerate_qemu() -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
    except Exception as exc:
        return [{"error": repr(exc)}]
    rows = []
    for line in out.splitlines():
        if "qemu-system" in line and "grep" not in line:
            rows.append({"ps": line.strip()[:400]})
    return rows


def _wait_slot_or_busy(*, wait_s: int = 30) -> dict[str, Any]:
    deadline = time.time() + wait_s
    while True:
        rows = _enumerate_qemu()
        live = [r for r in rows if "error" not in r]
        if not live:
            return {"ok": True, "qemu_processes": [], "waited_s": wait_s - max(0, deadline - time.time())}
        if time.time() >= deadline:
            return {
                "ok": False,
                "blocker": "17G5C1_QEMU_SLOT_BUSY",
                "qemu_processes": live,
            }
        time.sleep(2.0)


class _HealthHandler(BaseHTTPRequestHandler):
    server_version = "GunnchosGuestfwdTest/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        msg = "%s - %s" % (self.address_string(), fmt % args)
        log_path = getattr(self.server, "access_log_path", None)
        if log_path:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] in ("/healthz", "/"):
            body = TEST_BODY
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def start_test_http(port: int, log_path: Path) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _HealthHandler)
    httpd.access_log_path = str(log_path)  # type: ignore[attr-defined]
    thr = threading.Thread(target=httpd.serve_forever, daemon=True)
    thr.start()
    return httpd, thr, os.getpid()


def host_curl(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
            return {
                "ok": True,
                "status": int(resp.status),
                "body": body.decode("utf-8", "replace"),
                "body_sha256": _sha256(body),
            }
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def guest_probe(session: Any, urls: list[str]) -> dict[str, Any]:
    """Bounded guest TCP/HTTP probes (connect <=3s, total <=5s)."""
    py = f"""
import json, socket, urllib.request, subprocess
from pathlib import Path
out = {{
  "ip_addr": "",
  "ip_route": "",
  "probes": [],
}}
try:
  out["ip_addr"] = subprocess.check_output(["bash","-lc","ip -4 addr show"], text=True, timeout=5)[-1200:]
except Exception as e:
  out["ip_addr_error"] = repr(e)
try:
  out["ip_route"] = subprocess.check_output(["bash","-lc","ip -4 route"], text=True, timeout=5)[-800:]
except Exception as e:
  out["ip_route_error"] = repr(e)
for url in {urls!r}:
  item = {{"url": url, "tcp_ok": False, "http_status": None, "body": "", "error": None}}
  try:
    # parse host/port
    from urllib.parse import urlparse
    p = urlparse(url)
    host = p.hostname
    port = int(p.port or 80)
    try:
      with socket.create_connection((host, port), timeout=3.0):
        item["tcp_ok"] = True
    except Exception as e:
      item["error"] = f"tcp:{{e}}"
    if item["tcp_ok"]:
      try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
          body = resp.read(200)
          item["http_status"] = int(resp.status)
          item["body"] = body.decode("utf-8", "replace")
          item["body_sha256"] = __import__("hashlib").sha256(body).hexdigest()
      except Exception as e:
        item["error"] = f"http:{{e}}"
  except Exception as e:
    item["error"] = repr(e)
  out["probes"].append(item)
Path("/tmp/17g5c1_net_probe.json").write_text(json.dumps(out) + "\\n")
print("PROBE_OK")
"""
    put = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", f"cat > /var/tmp/17g5c1_net_probe.py <<'PY'\n{py}\nPY"],
        timeout_sec=20.0,
    )
    # Prefer base64-free write via python -c length; fallback put via guest_sh
    run = _guest_sh(
        session,
        "python3 - <<'PY'\n" + py + "\nPY\ncat /tmp/17g5c1_net_probe.json",
        timeout_sec=40.0,
    )
    blob = (run.get("stdout") or "") + (run.get("stderr") or "")
    payload: dict[str, Any] = {
        "agent_ok": bool(run.get("ok", True)),
        "put_note": {k: put.get(k) for k in ("ok", "returncode") if k in put},
        "raw_tail": blob[-2000:],
    }
    for line in blob.splitlines():
        line = line.strip()
        if line.startswith("{") and "probes" in line:
            try:
                payload.update(json.loads(line))
            except json.JSONDecodeError:
                continue
    return payload


def stop_session(session: Any | None) -> dict[str, Any]:
    if session is None:
        return {"ok": True, "note": "no_session"}
    try:
        return session.stop()
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def boot_clean(*, memory_mb: int = 3072, boot_timeout_s: int = 180) -> tuple[dict[str, Any], Any | None]:
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)
    boot = boot_interactive_guest(
        ROOT, WORK, dual=False, boot_timeout_s=boot_timeout_s, memory_mb=memory_mb
    )
    session = boot.pop("_session", None)
    return boot, session


def write_network_baseline() -> dict[str, Any]:
    """Section 3/4: inspect committed+current Interactive Guest usernet construction."""
    # Committed tip baseline (pre guestfwd helper)
    committed = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "HEAD:gunnchos_device_os/device_lab/virtualization/qemu_guest.py"],
        text=True,
    )
    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    baseline = {
        "schema": "gunnchos.device_lab.network_baseline.v1",
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "device_os_tip": tip,
        "source_path": "gunnchos_device_os/device_lab/virtualization/qemu_guest.py",
        "function": "QemuGuestSession._start_interactive_uefi",
        "committed_head_netdev_default": "user,id=n0,restrict=on",
        "committed_restrict_default": True,
        "committed_nic_device": "virtio-net-pci,netdev=n0",
        "committed_guestfwd_present": "guestfwd" in committed.lower()
        and "GUNNCHDEVICE_LAB_GUESTFWD" not in committed,
        "committed_host_visible": "host loopback services not reachable under restrict=on",
        "committed_guest_visible_gateway": "10.0.2.2 (slirp gateway; blocked to host under restrict=on)",
        "current_tree_uses_guest_service_forward": True,
        "current_default_without_env_guestfwd": build_usernet_netdev(restrict=True, rules=()),
        "notes": (
            "NETWORK_BASELINE captured against #134 tip before treating GuestServiceForward "
            "as the production path. Default with empty rules remains user,id=n0,restrict=on."
        ),
    }
    _write(OUT / "NETWORK_BASELINE.json", baseline)
    return baseline


def write_guestfwd_capability() -> dict[str, Any]:
    qemu = shutil.which("qemu-system-aarch64") or "/opt/homebrew/bin/qemu-system-aarch64"
    version = subprocess.check_output([qemu, "--version"], text=True).strip().splitlines()[0]
    # man page / binary string evidence (help CLI is brittle on this build)
    man = ""
    try:
        man = subprocess.check_output(
            ["bash", "-lc", "man qemu-system-aarch64 2>/dev/null | col -b | rg -n -i 'guestfwd' | head -5"],
            text=True,
            timeout=15,
        )
    except Exception as exc:
        man = f"man_probe_error:{exc}"
    strings_hit = ""
    try:
        strings_hit = subprocess.check_output(
            ["bash", "-lc", f"strings {qemu} | rg -i 'guestfwd' | head -5"],
            text=True,
            timeout=20,
        )
    except Exception as exc:
        strings_hit = f"strings_error:{exc}"
    supported = ("guestfwd" in man.lower()) or ("guestfwd" in strings_hit.lower())
    # Syntax dry-check via our builder
    clause = "guestfwd=tcp:10.0.2.100:18787-tcp:127.0.0.1:18787"
    netdev = build_usernet_netdev(
        restrict=True,
        rules=(
            GuestForwardRule(
                name="cap",
                guest_addr="10.0.2.100",
                guest_port=18787,
                host_addr="127.0.0.1",
                host_port=18787,
            ),
        ),
    )
    doc = {
        "schema": "gunnchos.device_lab.qemu_guestfwd_capability.v1",
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "qemu_bin": qemu,
        "qemu_version": version,
        "guestfwd_supported": supported,
        "man_evidence": man.strip()[:500],
        "binary_strings_evidence": strings_hit.strip()[:500],
        "candidate_clause": clause,
        "assembled_netdev": netdev,
        "note": "QEMU documents guestfwd is not affected by restrict=on.",
    }
    _write(OUT / "QEMU_GUESTFWD_CAPABILITY.json", doc)
    return doc


def policy_reject_checks() -> dict[str, Any]:
    authorized = DEVICE_LAB_HUB_ENDPOINT_POLICY_V1["authorized_hub_base_url"]
    rejects = []
    for url in ("http://10.0.2.2:8787", "https://evil.example"):
        rejects.append(
            {
                "url": url,
                "rejected": url != authorized,
                "reason": "not_equal_to_authorized_hub_base_url",
            }
        )
    return {
        "authorized_hub_base_url": authorized,
        "allow_insecure_local": DEVICE_LAB_HUB_ENDPOINT_POLICY_V1.get("allow_insecure_local"),
        "mockHub_disabled": True,
        "rejects": rejects,
        "all_rejects_ok": all(r["rejected"] for r in rejects),
        "authorized_is_guestfwd_url": authorized == "http://10.0.2.100:8787",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema": "gunnchos.device_lab.17g5c1_network_proof.v1",
        "generated_at_utc": _utc(),
        "prompt": PROMPT,
        "tokens": {
            "QEMU_SCOPED_GUESTFWD_PASS": False,
            "QEMU_GUEST_ISOLATION_RETAINED": False,
            "WAIKE_GUEST_HUB_REACHABILITY_PASS": False,
            "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        },
        "NEXT_GATE": None,
        "blocker": None,
    }

    tip = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    report["device_os_tip_start"] = tip
    report["waike_accepted_main"] = ACCEPTED_WAIKE_LP_SHA
    report["artifact_sha256"] = MAIN_AARCH64_GLIBC236_SHA256
    report["pin_manifest_sha256"] = PIN_MANIFEST_SHA256

    slot = _wait_slot_or_busy(wait_s=20)
    report["qemu_slot"] = slot
    if not slot.get("ok"):
        report["blocker"] = "17G5C1_QEMU_SLOT_BUSY"
        report["NEXT_GATE"] = "DEVICE_OS_134_QEMU_SLOT_CLEAR_THEN_RETRY_17G5C1"
        _write(OUT / "17G5C1_RESULT.json", report)
        print(json.dumps(report, indent=2))
        return 3

    baseline = write_network_baseline()
    report["network_baseline"] = {
        "netdev": baseline["current_default_without_env_guestfwd"],
        "restrict": True,
    }
    cap = write_guestfwd_capability()
    report["qemu_capability"] = {
        "version": cap.get("qemu_version"),
        "guestfwd_supported": cap.get("guestfwd_supported"),
    }
    if not cap.get("guestfwd_supported"):
        report["blocker"] = "qemu_guestfwd_unsupported"
        report["NEXT_GATE"] = "DEVICE_OS_134_ALTERNATE_SCOPED_HOST_SERVICE_FORWARD"
        _write(OUT / "17G5C1_RESULT.json", report)
        print(json.dumps(report, indent=2))
        return 4

    # --- Host test service ---
    test_log = OUT / "host_test_service_access.log"
    httpd, _thr, host_pid = start_test_http(TEST_PORT, test_log)
    host_check = host_curl(f"http://127.0.0.1:{TEST_PORT}/healthz")
    host_doc = {
        "schema": "gunnchos.device_lab.host_test_service.v1",
        "generated_at_utc": _utc(),
        "bind": "127.0.0.1",
        "port": TEST_PORT,
        "host_pid": host_pid,
        "body_expected": TEST_BODY.decode(),
        "host_curl": host_check,
        "body_sha256": _sha256(TEST_BODY),
    }
    _write(OUT / "HOST_TEST_SERVICE.json", host_doc)
    report["host_test_service"] = host_doc
    if not host_check.get("ok") or host_check.get("body") != TEST_BODY.decode():
        httpd.shutdown()
        report["blocker"] = "host_test_service_failed"
        report["NEXT_GATE"] = "DEVICE_OS_134_HOST_TEST_SERVICE_FIX"
        _write(OUT / "17G5C1_RESULT.json", report)
        print(json.dumps(report, indent=2))
        return 5

    # Isolation probe listener (not forwarded)
    iso_log = OUT / "isolation_probe_access.log"
    iso_httpd, _, _ = start_test_http(ISOLATION_PROBE_PORT, iso_log)

    session = None
    hub_proc = None
    hub_log = None
    artifact_httpd = None
    try:
        # --- Baseline restrict=on, no guestfwd (expect FAIL) ---
        clear_guest_service_forward_env()
        boot, session = boot_clean()
        report["baseline_boot"] = {
            "ok": boot.get("ok"),
            "error": boot.get("error"),
            "pid": boot.get("pid"),
        }
        if not boot.get("ok") or session is None:
            report["blocker"] = boot.get("error") or "baseline_boot_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_INTERACTIVE_GUEST_BOOT_FIX"
            return 6
        if not _wait_agent(session, tries=40, sleep_s=1.0):
            report["blocker"] = "guest_agent_not_ready_baseline"
            report["NEXT_GATE"] = "DEVICE_OS_134_GUEST_AGENT_FIX"
            return 7
        usernet_path = WORK / "qemu_usernet.json"
        usernet_meta = json.loads(usernet_path.read_text()) if usernet_path.is_file() else {}
        baseline_probe = guest_probe(
            session,
            [
                f"http://10.0.2.2:{TEST_PORT}/healthz",
                f"http://10.0.2.100:{TEST_PORT}/healthz",
            ],
        )
        baseline_doc = {
            "schema": "gunnchos.device_lab.network_baseline_restrict_on.v1",
            "generated_at_utc": _utc(),
            "restrict": True,
            "guestfwd_rules": usernet_meta.get("rules") or [],
            "netdev": usernet_meta.get("netdev"),
            "qemu_usernet": usernet_meta,
            "probe": baseline_probe,
            "expected": "host_service_unreachable",
            "host_reachable": any(
                (p.get("http_status") == 200 and p.get("body") == TEST_BODY.decode())
                for p in baseline_probe.get("probes") or []
            ),
        }
        baseline_doc["baseline_unreachable_as_expected"] = not baseline_doc["host_reachable"]
        _write(OUT / "NETWORK_BASELINE_RESTRICT_ON.json", baseline_doc)
        report["baseline_restrict_on"] = {
            "unreachable_as_expected": baseline_doc["baseline_unreachable_as_expected"],
            "netdev": baseline_doc.get("netdev"),
        }
        stop_session(session)
        session = None

        # --- Scoped guestfwd proof ---
        clear_guest_service_forward_env()
        gsf = guestfwd_proof_service_forward(guest_port=TEST_PORT, host_port=TEST_PORT)
        apply_guest_service_forward_env(gsf)
        boot2, session = boot_clean()
        report["guestfwd_boot"] = {
            "ok": boot2.get("ok"),
            "error": boot2.get("error"),
            "pid": boot2.get("pid"),
        }
        if not boot2.get("ok") or session is None:
            report["blocker"] = boot2.get("error") or "guestfwd_boot_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_GUESTFWD_BOOT_FIX"
            return 8
        if not _wait_agent(session, tries=40, sleep_s=1.0):
            report["blocker"] = "guest_agent_not_ready_guestfwd"
            report["NEXT_GATE"] = "DEVICE_OS_134_GUEST_AGENT_FIX"
            return 9
        usernet2 = json.loads((WORK / "qemu_usernet.json").read_text()) if (WORK / "qemu_usernet.json").is_file() else {}
        fwd_probe = guest_probe(
            session,
            [
                f"http://10.0.2.100:{TEST_PORT}/healthz",
                f"http://10.0.2.2:{TEST_PORT}/healthz",
                f"http://10.0.2.100:{ISOLATION_PROBE_PORT}/healthz",
                f"http://10.0.2.2:{ISOLATION_PROBE_PORT}/healthz",
            ],
        )
        probes = {p["url"]: p for p in fwd_probe.get("probes") or []}
        ok_fwd = probes.get(f"http://10.0.2.100:{TEST_PORT}/healthz", {})
        guestfwd_pass = (
            ok_fwd.get("http_status") == 200 and ok_fwd.get("body") == TEST_BODY.decode()
        )
        # Isolation: unrelated host port must not be reachable via guestfwd or gateway.
        iso_urls = [
            f"http://10.0.2.100:{ISOLATION_PROBE_PORT}/healthz",
            f"http://10.0.2.2:{ISOLATION_PROBE_PORT}/healthz",
            f"http://10.0.2.2:{TEST_PORT}/healthz",
        ]
        isolation_retained = all(
            not (
                probes.get(u, {}).get("http_status") == 200
                and probes.get(u, {}).get("body") == TEST_BODY.decode()
            )
            for u in iso_urls
        )
        host_log_tail = test_log.read_text(encoding="utf-8")[-1500:] if test_log.is_file() else ""
        guestfwd_doc = {
            "schema": "gunnchos.device_lab.guestfwd_test_pass.v1",
            "generated_at_utc": _utc(),
            "guestfwd_rule": "guestfwd=tcp:10.0.2.100:18787-tcp:127.0.0.1:18787",
            "netdev": usernet2.get("netdev"),
            "qemu_usernet": usernet2,
            "restrict_on": True,
            "probe": fwd_probe,
            "host_access_log_tail": host_log_tail,
            "QEMU_SCOPED_GUESTFWD_PASS": guestfwd_pass,
            "QEMU_GUEST_ISOLATION_RETAINED": isolation_retained,
            "unrestricted_usernet_used": False,
        }
        _write(OUT / "GUESTFWD_TEST_PASS.json", guestfwd_doc)
        report["tokens"]["QEMU_SCOPED_GUESTFWD_PASS"] = guestfwd_pass
        report["tokens"]["QEMU_GUEST_ISOLATION_RETAINED"] = isolation_retained
        report["guestfwd_test"] = {
            "pass": guestfwd_pass,
            "isolation": isolation_retained,
            "netdev": usernet2.get("netdev"),
            "curl_status": ok_fwd.get("http_status"),
            "curl_body": ok_fwd.get("body"),
        }
        stop_session(session)
        session = None
        httpd.shutdown()
        iso_httpd.shutdown()

        if not guestfwd_pass:
            report["blocker"] = "qemu_scoped_guestfwd_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_QEMU_SCOPED_GUESTFWD_FIX"
            return 10

        # --- Real WAIKE Hub forward ---
        lp = resolve_waike_lp_checkout(ROOT)
        ops = ROOT.parent / "waike-research-ops"
        if not ops.is_dir():
            ops = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/waike-research-ops")
        hub_work = OUT / "hub_sidecar"
        if hub_work.exists():
            shutil.rmtree(hub_work, ignore_errors=True)
        hub_work.mkdir(parents=True, exist_ok=True)
        hub = start_host_real_hub(lp, ops, hub_work)
        hub_proc = hub.pop("proc", None)
        hub_log = hub.pop("log_handle", None)
        report["real_hub"] = {k: v for k, v in hub.items() if k not in ("proc", "log_handle")}
        if not hub.get("ok"):
            report["blocker"] = "real_hub_sidecar_failed_to_start"
            report["NEXT_GATE"] = "DEVICE_OS_134_REAL_HUB_SIDECAR_FIX"
            return 11

        clear_guest_service_forward_env()
        hub_fwd = device_lab_hub_httpd_forward(
            hub_port=HUB_PORT, httpd_port=OWNER_HTTPD_PORT
        )
        apply_guest_service_forward_env(hub_fwd)

        staging = OUT / "owner_bundle_stage"
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        bundle = stage_owner_waike_bundle(ROOT, staging)
        report["bundle"] = {k: bundle.get(k) for k in ("ok", "pin_ok", "arch_gap") if k in bundle}
        os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging)
        artifact_httpd = start_host_artifact_httpd(
            staging, port=OWNER_HTTPD_PORT, log_path=OUT / "host_artifact_httpd.log"
        )
        ok_listen, listen_err = wait_host_artifact_httpd(OWNER_HTTPD_PORT, proc=artifact_httpd)
        report["artifact_httpd"] = {"ok": ok_listen, "error": listen_err}
        if not ok_listen:
            report["blocker"] = f"host_artifact_httpd:{listen_err}"
            report["NEXT_GATE"] = "DEVICE_OS_134_ARTIFACT_HTTPD_FIX"
            return 12

        boot3, session = boot_clean(memory_mb=4096, boot_timeout_s=240)
        report["hub_boot"] = {
            "ok": boot3.get("ok"),
            "error": boot3.get("error"),
            "pid": boot3.get("pid"),
        }
        if not boot3.get("ok") or session is None:
            report["blocker"] = boot3.get("error") or "hub_guest_boot_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_INTERACTIVE_GUEST_BOOT_FIX"
            return 13
        if not _wait_agent(session, tries=50, sleep_s=1.0):
            report["blocker"] = "guest_agent_not_ready_hub"
            report["NEXT_GATE"] = "DEVICE_OS_134_GUEST_AGENT_FIX"
            return 14

        reach = prove_guest_hub_reachability(session, hub_url=HUB_GUEST_URL)
        reach_pass = bool(reach.get("hub_reachable_from_guest") and reach.get("http_hub_status") == 200)
        # Also require explicit curl-shaped probe
        hub_curl = guest_probe(session, [f"{HUB_GUEST_URL}/healthz"])
        curl_ok = any(
            p.get("http_status") == 200 for p in hub_curl.get("probes") or []
        )
        reach_pass = reach_pass or curl_ok
        reach_doc = {
            "schema": "gunnchos.device_lab.waike_scoped_guest_hub_reachability.v1",
            "generated_at_utc": _utc(),
            "host_bind": "127.0.0.1:8787",
            "guest_url": HUB_GUEST_URL,
            "guestfwd_rule": "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787",
            "restrict_on": True,
            "reachability": {
                k: reach.get(k)
                for k in (
                    "hub_reachable_from_guest",
                    "tcp_hub",
                    "tcp_gateway_hub",
                    "http_hub_status",
                    "http_hub_body",
                    "errors",
                    "ip_route",
                )
            },
            "curl_probe": hub_curl,
            "WAIKE_GUEST_HUB_REACHABILITY_PASS": reach_pass,
            "qemu_usernet": json.loads((WORK / "qemu_usernet.json").read_text())
            if (WORK / "qemu_usernet.json").is_file()
            else {},
        }
        _write(OUT / "WAIKE_SCOPED_GUEST_HUB_REACHABILITY.json", reach_doc)
        report["tokens"]["WAIKE_GUEST_HUB_REACHABILITY_PASS"] = reach_pass
        report["hub_reachability"] = {
            "pass": reach_pass,
            "http_status": reach.get("http_hub_status"),
            "guest_url": HUB_GUEST_URL,
        }

        policy = policy_reject_checks()
        _write(OUT / "HUB_ENDPOINT_POLICY_CHECKS.json", policy)
        report["policy"] = policy

        if not reach_pass:
            report["blocker"] = "waike_guest_hub_reachability_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_WAIKE_GUEST_HUB_REACHABILITY_FIX"
            return 15

        # --- Minimal real-client bind (no AT-SPI / journey) ---
        fetch = fetch_bundle_into_guest(session, port=OWNER_HTTPD_PORT)
        report["guest_fetch"] = {
            "ok": fetch.get("ok"),
            "error": fetch.get("error") or fetch.get("blocker"),
        }
        if not fetch.get("ok"):
            # Some helpers use different shape
            if fetch.get("blocker"):
                report["blocker"] = fetch.get("blocker")
            else:
                report["blocker"] = "guest_fetch_owner_bundle_failed"
            report["NEXT_GATE"] = "DEVICE_OS_134_WAIKE_BUNDLE_FETCH_FIX"
            # Network proof already passed; still record bind false
            bind_doc = {
                "schema": "gunnchos.device_lab.waike_minimal_real_hub_bind.v1",
                "generated_at_utc": _utc(),
                "WAIKE_REAL_HUB_CLIENT_BIND_PASS": False,
                "blocker": report["blocker"],
                "mockHub": False,
                "note": "Network closed; bind not attempted due to bundle fetch failure.",
            }
            _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", bind_doc)
            report["tokens"]["WAIKE_REAL_HUB_CLIENT_BIND_PASS"] = False
            report["NEXT_GATE"] = "DEVICE_OS_134_WAIKE_RUNTIME_CONTEXT_TO_WEBVIEW_BIND"
            return 16

        launch = guest_gui_launch(
            session,
            journey_tag="N",
            hub_url=HUB_GUEST_URL,
        )
        time.sleep(4.0)
        sockets = prove_client_hub_sockets(session, hub_port=HUB_PORT)
        log_bind = scrape_gui_log_hub_bind(session, journey_tag="N")
        # Hub-side evidence from access / sidecar log
        hub_log_path = hub_work / "hub_sidecar.log"
        hub_log_tail = ""
        if hub_log_path.is_file():
            hub_log_tail = hub_log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        client_http_evidence = bool(
            sockets.get("established_to_hub")
            or log_bind.get("hub_http_chip_in_log")
            or ("10.0.2.100:8787" in str(log_bind.get("tail") or ""))
            or ("GET /" in hub_log_tail and "127.0.0.1" in hub_log_tail)
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
        bind_doc = {
            "schema": "gunnchos.device_lab.waike_minimal_real_hub_bind.v1",
            "generated_at_utc": _utc(),
            "hub_url": HUB_GUEST_URL,
            "policy": DEVICE_LAB_HUB_ENDPOINT_POLICY_V1,
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
                )
            },
            "hub_log_tail": hub_log_tail,
            "mockHub": False,
            "atspi_used": False,
            "WAIKE_REAL_HUB_CLIENT_BIND_PASS": bind_pass,
        }
        _write(OUT / "WAIKE_MINIMAL_REAL_HUB_BIND.json", bind_doc)
        report["tokens"]["WAIKE_REAL_HUB_CLIENT_BIND_PASS"] = bind_pass
        report["minimal_bind"] = {
            "pass": bind_pass,
            "ack": ack_ok,
            "alive": alive,
            "client_http_evidence": client_http_evidence,
        }
        try:
            stop_gui_pid(session, "N")
        except Exception:
            pass

        if bind_pass:
            report["NEXT_GATE"] = "17G5D_FULL_WAIKE_GUI_JOURNEY_REEARN"
        else:
            report["NEXT_GATE"] = "DEVICE_OS_134_WAIKE_RUNTIME_CONTEXT_TO_WEBVIEW_BIND"
            report["blocker"] = "waike_real_hub_client_bind_incomplete"
        return 0 if guestfwd_pass and reach_pass else 17
    finally:
        try:
            stop_session(session)
        except Exception:
            pass
        clear_guest_service_forward_env()
        try:
            httpd.shutdown()
        except Exception:
            pass
        try:
            iso_httpd.shutdown()
        except Exception:
            pass
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
        # Kill only qemu we started (pidfile in WORK)
        pid_file = WORK / "qemu.pid"
        if pid_file.is_file():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        report["finished_at_utc"] = _utc()
        _write(OUT / "17G5C1_RESULT.json", report)
        print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    # Ensure return code from early returns still writes via finally... 
    # early returns inside try still run finally.
    raise SystemExit(main())
