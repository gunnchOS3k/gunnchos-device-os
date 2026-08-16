"""Host orchestrator for STREAM-A-PKT-002 creator guest E2E.

Boots sealed-base + COW Interactive Guest, stages SDK payload via virtio-9p,
runs dogfood INSIDE the guest, pulls RESULT.json. Host packaging alone never
earns CREATOR_GUEST_* or CREATOR_END_TO_END_DIGITAL_PASS.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.interactive_guest_proofs import (
    _agent_call,
    _pull_guest_file,
    _wait_agent,
    boot_interactive_guest,
)

APP_ID = "gunnchos.stream_a_sample_memo"
PACKET = "STREAM-A-PKT-002"
PERSONA = "creator_pkt002"


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def artifact_dir(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "stream_a_pkt_002"


def stage_ninep_share(repo_root: Path) -> Path:
    """Stage readonly 9p share: SDK subset + sample app + dogfood entry."""
    share = artifact_dir(repo_root) / "ninep_share"
    if share.exists():
        shutil.rmtree(share)
    share.mkdir(parents=True, exist_ok=True)

    python_root = share / "python_root"
    # Minimal importable tree for packager/installer/runner.
    modules = [
        "gunnchos_device_os/__init__.py",
        "gunnchos_device_os/release_engineering/__init__.py",
        "gunnchos_device_os/release_engineering/dev_keys.py",
        "gunnchos_device_os/release_engineering/sdk/__init__.py",
        "gunnchos_device_os/release_engineering/sdk/compat.py",
        "gunnchos_device_os/release_engineering/sdk/manifest.py",
        "gunnchos_device_os/release_engineering/sdk/packager.py",
        "gunnchos_device_os/release_engineering/sdk/installer.py",
        "gunnchos_device_os/release_engineering/sdk/runner.py",
        "gunnchos_device_os/creation_enablement/__init__.py",
        "gunnchos_device_os/creation_enablement/guest_dogfood.py",
    ]
    for rel in modules:
        src = repo_root / rel
        dst = python_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
        else:
            dst.write_text('"""pkg marker"""\n', encoding="utf-8")

    # Ensure package markers for nested packages missing __init__ copies.
    for pkg in (
        "gunnchos_device_os",
        "gunnchos_device_os/release_engineering",
        "gunnchos_device_os/release_engineering/sdk",
        "gunnchos_device_os/creation_enablement",
    ):
        init = python_root / pkg / "__init__.py"
        if not init.exists():
            init.parent.mkdir(parents=True, exist_ok=True)
            init.write_text('"""staged"""\n', encoding="utf-8")

    app_src = repo_root / "sdk" / "apps" / "stream_a_sample_memo"
    app_dst = share / "apps" / "stream_a_sample_memo"
    shutil.copytree(app_src, app_dst)

    entry = share / "run_creator_e2e.py"
    entry.write_text(
        "#!/usr/bin/env python3\n"
        "from gunnchos_device_os.creation_enablement.guest_dogfood import main\n"
        "raise SystemExit(main())\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": "gunnchos.creation_enablement.ninep_payload.v1",
        "packet": PACKET,
        "staged_at_utc": _utc(),
        "modules": modules,
        "app_id": APP_ID,
        "mount_tag": "gdlgames",
        "note": "Readonly virtio-9p share for in-guest creator dogfood only.",
    }
    (share / "CREATOR_PAYLOAD_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return share


def _guest_bash(session: Any, script: str, *, timeout_sec: float = 120.0) -> dict[str, Any]:
    return _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", script],
        timeout_sec=timeout_sec,
    )


def run_guest_creator_e2e(
    repo_root: Path,
    *,
    boot_timeout_s: int = 240,
    memory_mb: int = 3072,
    keep_guest: bool = False,
) -> dict[str, Any]:
    started = time.time()
    out = artifact_dir(repo_root)
    out.mkdir(parents=True, exist_ok=True)
    work = out / "interactive_guest_session"
    work.mkdir(parents=True, exist_ok=True)

    share = stage_ninep_share(repo_root)
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = PERSONA
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(share)
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "1"

    boot = boot_interactive_guest(
        repo_root,
        work,
        dual=False,
        boot_timeout_s=boot_timeout_s,
        memory_mb=memory_mb,
    )
    session = boot.get("_session")
    result: dict[str, Any] = {
        "schema": "gunnchos.creation_enablement.guest_e2e_host.v1",
        "packet": PACKET,
        "base_sha_expected": "e290cdf2bf39453442022e471bbbd4fafd97abf2",
        "persona": PERSONA,
        "sealed_cow": True,
        "ninep_share": str(share),
        "boot": {k: v for k, v in boot.items() if k != "_session"},
        "started_at_utc": _utc(),
        "SILICON_EXACT_EMULATION": False,
        "host_side_counting": False,
        "tokens": {
            "CREATOR_GUEST_BUILD_PASS": False,
            "CREATOR_GUEST_INSTALL_PASS": False,
            "CREATOR_GUEST_RUN_PASS": False,
            "CREATOR_GUEST_UPDATE_PASS": False,
            "CREATOR_GUEST_ROLLBACK_PASS": False,
            "CREATOR_END_TO_END_DIGITAL_PASS": False,
        },
        "ok_guest_chain": False,
        "guest_result": None,
        "error": None,
    }

    if not boot.get("ok") or session is None:
        result["error"] = boot.get("error") or "boot_failed"
        result["duration_ms"] = int((time.time() - started) * 1000)
        _write_host_evidence(out, result)
        return result

    try:
        if not _wait_agent(session, tries=60, sleep_s=2.0):
            result["error"] = "guest_agent_not_ready"
            return result

        ping = _agent_call(session, "ping", timeout_sec=10.0)
        result["agent_ping"] = ping
        transport = str(ping.get("transport") or "")
        if "stub" in transport.lower():
            result["error"] = "host_stub_rejected"
            return result

        mount = _guest_bash(
            session,
            "set -e; mkdir -p /mnt/gdlgames; "
            "modprobe 9p 9pnet 9pnet_virtio 2>/dev/null || true; "
            "mountpoint -q /mnt/gdlgames || "
            "mount -t 9p -o trans=virtio,version=9p2000.L,ro gdlgames /mnt/gdlgames; "
            "test -f /mnt/gdlgames/CREATOR_PAYLOAD_MANIFEST.json; "
            "ls /mnt/gdlgames | head; "
            "hostname; uname -a",
            timeout_sec=60.0,
        )
        result["ninep_mount"] = mount
        if mount.get("returncode") not in (0, None) and not mount.get("ok"):
            # process_run returns ok + returncode fields depending on agent version
            rc = mount.get("returncode")
            if rc not in (0, None) and rc != 0:
                result["error"] = "ninep_mount_failed"
                return result

        dogfood = _guest_bash(
            session,
            "set -e; "
            "export PYTHONPATH=/mnt/gdlgames/python_root; "
            "python3 /mnt/gdlgames/python_root/gunnchos_device_os/creation_enablement/guest_dogfood.py; "
            "test -f /var/lib/gunnchos/creator_e2e/RESULT.json; "
            "cp /var/lib/gunnchos/creator_e2e/RESULT.json /tmp/creator_e2e_RESULT.json; "
            "cp /var/lib/gunnchos/creator_e2e/TOKENS.json /tmp/creator_e2e_TOKENS.json",
            timeout_sec=300.0,
        )
        result["dogfood_process"] = {
            "ok": dogfood.get("ok"),
            "returncode": dogfood.get("returncode"),
            "stdout": (dogfood.get("stdout") or "")[:2000],
            "stderr": (dogfood.get("stderr") or "")[:1000],
        }

        raw = _pull_guest_file(session, "/tmp/creator_e2e_RESULT.json")
        if not raw:
            result["error"] = "guest_result_missing"
            return result
        guest_result = json.loads(raw.decode("utf-8"))
        result["guest_result"] = guest_result
        tokens = dict(guest_result.get("tokens") or {})
        # Only accept tokens when guest marked executed_in_guest and five keys present.
        required = (
            "CREATOR_GUEST_BUILD_PASS",
            "CREATOR_GUEST_INSTALL_PASS",
            "CREATOR_GUEST_RUN_PASS",
            "CREATOR_GUEST_UPDATE_PASS",
            "CREATOR_GUEST_ROLLBACK_PASS",
        )
        if not guest_result.get("executed_in_guest"):
            result["error"] = "guest_result_not_marked_in_guest"
            tokens = {k: False for k in (*required, "CREATOR_END_TO_END_DIGITAL_PASS")}
        else:
            for k in required:
                tokens[k] = bool(tokens.get(k))
            tokens["CREATOR_END_TO_END_DIGITAL_PASS"] = all(tokens[k] for k in required)
        result["tokens"] = tokens
        result["ok_guest_chain"] = bool(tokens.get("CREATOR_END_TO_END_DIGITAL_PASS"))
        if not result["ok_guest_chain"] and not result.get("error"):
            result["error"] = guest_result.get("error") or "guest_chain_incomplete"
    finally:
        if session is not None and not keep_guest:
            try:
                session.stop()
            except Exception as exc:  # noqa: BLE001
                result["stop_error"] = str(exc)

    result["duration_ms"] = int((time.time() - started) * 1000)
    result["completed_at_utc"] = _utc()
    _write_host_evidence(out, result)
    return result


def _write_host_evidence(out: Path, result: dict[str, Any]) -> Path:
    path = out / "CREATOR_GUEST_E2E_RESULT.json"
    # Strip non-serializable leftovers
    clean = {k: v for k, v in result.items() if k != "_session"}
    path.write_text(json.dumps(clean, indent=2, default=str) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    res = run_guest_creator_e2e(root)
    print(
        json.dumps(
            {
                "ok_guest_chain": res.get("ok_guest_chain"),
                "tokens": res.get("tokens"),
                "error": res.get("error"),
                "evidence": str(artifact_dir(root) / "CREATOR_GUEST_E2E_RESULT.json"),
            },
            indent=2,
        )
    )
