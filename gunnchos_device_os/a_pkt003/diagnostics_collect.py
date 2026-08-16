"""A5 — gunnch diagnostics collect path."""
from __future__ import annotations

import json
import platform
import time
import uuid
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET
from gunnchos_device_os.a_pkt003.evidence_scrub import write_scrubbed_json
from gunnchos_device_os.diagnostics_log import DiagnosticsLog, redact
from gunnchos_device_os.release_engineering.serviceability import export_diagnostic_bundle, redact_text


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def collect_diagnostics(
    repo_root: Path,
    *,
    device_profile: str = "student_14_5",
    install_root: Path | None = None,
) -> dict[str, Any]:
    out = repo_root / ARTIFACT_REL / "diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    request_id = str(uuid.uuid4())
    trace_id = uuid.uuid4().hex

    log = DiagnosticsLog(out / "structured.jsonl")
    log.log(
        "diagnostics_collect_start",
        {
            "request_id": request_id,
            "email": "learner.probe@example.edu",
            "token": "REDACT_PROBE_TOKEN",
            "api_key": "REDACT_PROBE_KEY",
        },
        level="info",
        trace_id=trace_id,
    )
    log.log(
        "sample_crash",
        {
            "request_id": request_id,
            "crash_reason": "simulated_service_fault",
            "recovery_action": "restart_fallback",
            "student_name": "RedactProbeName",
        },
        level="error",
        trace_id=trace_id,
    )

    device_root = out / "device_root"
    device_root.mkdir(parents=True, exist_ok=True)
    (device_root / "identity.json").write_text(
        json.dumps({"device_id": "lab-virtual", "profile": device_profile}) + "\n",
        encoding="utf-8",
    )
    logs_dir = device_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "runtime.log").write_text(
        "user=learner.probe@example.edu token=REDACT_PROBE_TOKEN crash=oom\n",
        encoding="utf-8",
    )
    bundle_path = out / "diagnostic_bundle.tar.gz"
    bundle = export_diagnostic_bundle(device_root, bundle_path)

    install_root = install_root or (repo_root / "os_build" / "sdk_runtime" / "installed")
    versions: dict[str, Any] = {}
    reg = install_root / "registry.json"
    if reg.exists():
        versions = json.loads(reg.read_text(encoding="utf-8"))

    profile_path = (
        repo_root / "gunnchos_device_os" / "device_lab" / "profiles" / f"{device_profile}.json"
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8")) if profile_path.exists() else {}

    service_health = {
        "guest_agent": "unknown",
        "package_runtime": "ok",
        "ai_local": "degraded_or_offline",
        "waike": "digital_only",
        "ring": "virtual_only",
    }
    error_taxonomy = {
        "STORAGE_PRESSURE": "resource",
        "UPDATE_INTERRUPTED": "lifecycle",
        "SERVICE_CRASH": "runtime",
        "NETWORK_OUTAGE": "connectivity",
        "PERMISSION_DENIED": "security",
        "AI_UNAVAILABLE": "ai",
    }

    structured_records = []
    jsonl = out / "structured.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                structured_records.append(redact(json.loads(line)))

    export_blob = {"structured_logs": structured_records, "bundle_summary": bundle}
    export_text = json.dumps(export_blob)
    leaks = []
    for needle in ("REDACT_PROBE_TOKEN", "learner.probe@example.edu", "RedactProbeName", "REDACT_PROBE_KEY"):
        if needle in export_text:
            leaks.append(needle)

    doc = {
        "schema": "gunnchos.a_pkt003.diagnostics_collect.v1",
        "packet": PACKET,
        "base_sha": BASE_SHA,
        "command": "gunnch diagnostics collect",
        "generated_at_utc": _utc(),
        "request_id": request_id,
        "trace_id": trace_id,
        "structured_logs": structured_records,
        "service_health": service_health,
        "package_app_versions": versions,
        "device_profile": {
            "profile_id": device_profile,
            "product": profile.get("product"),
            "SILICON_EXACT_EMULATION": False,
        },
        "error_taxonomy": error_taxonomy,
        "redaction": {"applied": True, "leaks_found": leaks},
        "crash_reason": "simulated_service_fault",
        "recovery_action": "restart_fallback",
        "provenance": {
            "bundle_sha256": bundle.get("sha256"),
            "bundle_path": "artifacts/a_pkt003/diagnostics/diagnostic_bundle.tar.gz",
            "host": "<lab-host>",
            "platform": platform.system(),
        },
        "ok": bundle.get("ok") is True and not leaks,
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": (
            "Diagnostic collect for support/creators/research/CI. "
            "No learner-private data or secrets in export."
        ),
    }
    path = repo_root / ARTIFACT_REL / "DIAGNOSTICS_COLLECT_RESULT.json"
    cleaned = write_scrubbed_json(path, doc, repo_root)
    cleaned["path"] = "artifacts/a_pkt003/DIAGNOSTICS_COLLECT_RESULT.json"
    cleaned["token_OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS"] = bool(cleaned["ok"])
    return cleaned
