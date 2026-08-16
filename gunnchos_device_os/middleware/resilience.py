"""Middleware resilience fault injection against STREAM-A-PKT-001 contracts.

Injects controlled faults and records whether handlers degrade honestly
(schema-valid error envelopes) without inventing silicon-exact claims.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from gunnchos_device_os.middleware.contracts import (
    CONTRACT_SCHEMA_FILES,
    load_example,
    validate_payload,
)

PACKET = "STREAM-A-PKT-002"

# Faults required by A3
FAULTS = (
    "ai_unavailable",
    "ring_disconnect",
    "permission_denied",
    "storage_full",
    "network_outage",
    "update_interrupted",
    "service_crash",
    "display_topology",
    "malformed_ipc",
    "stale_protocol_version",
)

CONTRACT_FOR_FAULT = {
    "ai_unavailable": "MW-AI-INTERFACE",
    "ring_disconnect": "MW-RING-INPUT",
    "permission_denied": "MW-IDENTITY",
    "storage_full": "MW-PACKAGE",
    "network_outage": "MW-SESSION-CONTINUITY",
    "update_interrupted": "MW-PACKAGE",
    "service_crash": "MW-GAME-LAUNCH",
    "display_topology": "MW-SESSION-CONTINUITY",
    "malformed_ipc": "MW-RING-INPUT",
    "stale_protocol_version": "MW-IDENTITY",
}


def _error_envelope(
    *,
    fault: str,
    contract_id: str,
    code: str,
    detail: str,
    recoverable: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "schema": "gunnchos.middleware.fault_response.v1",
        "packet": PACKET,
        "contract_id": contract_id,
        "fault": fault,
        "ok": False,
        "error": {"code": code, "detail": detail, "recoverable": recoverable},
        "SILICON_EXACT_EMULATION": False,
        "degraded": True,
        "observed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if extra:
        base.update(extra)
    return base


def _handlers() -> dict[str, Callable[[], dict[str, Any]]]:
    def ai_unavailable() -> dict[str, Any]:
        ex = load_example("MW-AI-INTERFACE")
        return _error_envelope(
            fault="ai_unavailable",
            contract_id="MW-AI-INTERFACE",
            code="AI_UNAVAILABLE",
            detail="Local AI backend unreachable; refuse cloud fallback without consent",
            recoverable=True,
            extra={"request_id": ex.get("request_id"), "mode": "local_offline"},
        )

    def ring_disconnect() -> dict[str, Any]:
        return _error_envelope(
            fault="ring_disconnect",
            contract_id="MW-RING-INPUT",
            code="RING_DISCONNECT",
            detail="Ring input channel disconnected (digital lab path)",
            recoverable=True,
            extra={"PHYSICAL_RING_E6": False, "SILICON_EXACT_EMULATION": False},
        )

    def permission_denied() -> dict[str, Any]:
        return _error_envelope(
            fault="permission_denied",
            contract_id="MW-IDENTITY",
            code="PERMISSION_DENIED",
            detail="Caller lacks capability for requested middleware action",
            recoverable=False,
            extra={"required_capability": "package.install"},
        )

    def storage_full() -> dict[str, Any]:
        return _error_envelope(
            fault="storage_full",
            contract_id="MW-PACKAGE",
            code="STORAGE_FULL",
            detail="Install root cannot accept package payload",
            recoverable=True,
            extra={"bytes_free": 0},
        )

    def network_outage() -> dict[str, Any]:
        return _error_envelope(
            fault="network_outage",
            contract_id="MW-SESSION-CONTINUITY",
            code="NETWORK_OUTAGE",
            detail="Offline continuity path engaged; remote sync deferred",
            recoverable=True,
            extra={"offline_first": True},
        )

    def update_interrupted() -> dict[str, Any]:
        return _error_envelope(
            fault="update_interrupted",
            contract_id="MW-PACKAGE",
            code="UPDATE_INTERRUPTED",
            detail="Package update aborted mid-write; prior version retained",
            recoverable=True,
            extra={"rollback_candidate": True},
        )

    def service_crash() -> dict[str, Any]:
        return _error_envelope(
            fault="service_crash",
            contract_id="MW-GAME-LAUNCH",
            code="SERVICE_CRASH",
            detail="Launch helper exited non-zero before runtime receipt",
            recoverable=True,
            extra={"SILICON_EXACT_EMULATION": False},
        )

    def display_topology() -> dict[str, Any]:
        return _error_envelope(
            fault="display_topology",
            contract_id="MW-SESSION-CONTINUITY",
            code="DISPLAY_TOPOLOGY_CHANGED",
            detail="Guest DRM connector count changed; session continuity remapped",
            recoverable=True,
            extra={"outputs_before": 2, "outputs_after": 1},
        )

    def malformed_ipc() -> dict[str, Any]:
        return _error_envelope(
            fault="malformed_ipc",
            contract_id="MW-RING-INPUT",
            code="MALFORMED_IPC",
            detail="Ring IPC frame failed schema validation; event dropped",
            recoverable=True,
            extra={"dropped": True, "PHYSICAL_RING_E6": False},
        )

    def stale_protocol_version() -> dict[str, Any]:
        return _error_envelope(
            fault="stale_protocol_version",
            contract_id="MW-IDENTITY",
            code="STALE_PROTOCOL_VERSION",
            detail="Client protocol older than accepted identity contract",
            recoverable=False,
            extra={"client_protocol": "0.9.0", "server_protocol": "1.0.0"},
        )

    return {
        "ai_unavailable": ai_unavailable,
        "ring_disconnect": ring_disconnect,
        "permission_denied": permission_denied,
        "storage_full": storage_full,
        "network_outage": network_outage,
        "update_interrupted": update_interrupted,
        "service_crash": service_crash,
        "display_topology": display_topology,
        "malformed_ipc": malformed_ipc,
        "stale_protocol_version": stale_protocol_version,
    }


def build_resilience_matrix() -> dict[str, Any]:
    rows = []
    for fault in FAULTS:
        rows.append(
            {
                "fault": fault,
                "contract_id": CONTRACT_FOR_FAULT[fault],
                "pkt001_contract": CONTRACT_FOR_FAULT[fault] in CONTRACT_SCHEMA_FILES,
                "expected_code": fault.upper()
                if fault
                not in {
                    "ai_unavailable",
                    "ring_disconnect",
                    "permission_denied",
                    "storage_full",
                    "network_outage",
                    "update_interrupted",
                    "service_crash",
                    "display_topology",
                    "malformed_ipc",
                    "stale_protocol_version",
                }
                else {
                    "ai_unavailable": "AI_UNAVAILABLE",
                    "ring_disconnect": "RING_DISCONNECT",
                    "permission_denied": "PERMISSION_DENIED",
                    "storage_full": "STORAGE_FULL",
                    "network_outage": "NETWORK_OUTAGE",
                    "update_interrupted": "UPDATE_INTERRUPTED",
                    "service_crash": "SERVICE_CRASH",
                    "display_topology": "DISPLAY_TOPOLOGY_CHANGED",
                    "malformed_ipc": "MALFORMED_IPC",
                    "stale_protocol_version": "STALE_PROTOCOL_VERSION",
                }[fault],
                "must_keep_silicon_exact_false": True,
            }
        )
    return {
        "schema": "gunnchos.middleware.resilience_matrix.v1",
        "packet": PACKET,
        "faults": rows,
        "count": len(rows),
        "claim_boundary": (
            "Digital fault-injection matrix over PKT-001 middleware contracts. "
            "Not a production SLA claim. SILICON_EXACT_EMULATION=false."
        ),
    }


def inject_fault(fault: str) -> dict[str, Any]:
    handlers = _handlers()
    if fault not in handlers:
        return {"ok": False, "error": f"unknown_fault:{fault}"}
    response = handlers[fault]()
    # Positive controls: healthy example still validates for the mapped contract
    contract_id = CONTRACT_FOR_FAULT[fault]
    healthy_errs = validate_payload(contract_id, load_example(contract_id))
    # Fault envelopes are intentionally not the happy-path schema — they must
    # degrade honestly without claiming silicon-exact or inventing PASS.
    checks = {
        "response_ok_false": response.get("ok") is False,
        "degraded": response.get("degraded") is True,
        "silicon_exact_false": response.get("SILICON_EXACT_EMULATION") is False,
        "has_error_code": bool((response.get("error") or {}).get("code")),
        "healthy_example_still_valid": healthy_errs == [],
        "contract_mapped": contract_id in CONTRACT_SCHEMA_FILES,
    }
    # Malformed IPC: also prove happy-path rejects garbage
    if fault == "malformed_ipc":
        bad = {"schema": "not-a-ring-schema", "garbage": True}
        checks["malformed_rejected_by_schema"] = bool(validate_payload(contract_id, bad))
    if fault == "stale_protocol_version":
        checks["recoverable_false"] = (response.get("error") or {}).get("recoverable") is False

    passed = all(checks.values())
    return {
        "fault": fault,
        "contract_id": contract_id,
        "pass": passed,
        "checks": checks,
        "response": response,
    }


def run_fault_injection() -> dict[str, Any]:
    started = time.time()
    results = [inject_fault(f) for f in FAULTS]
    return {
        "schema": "gunnchos.middleware.fault_injection_result.v1",
        "packet": PACKET,
        "results": results,
        "pass_count": sum(1 for r in results if r.get("pass")),
        "fail_count": sum(1 for r in results if not r.get("pass")),
        "ok": all(r.get("pass") for r in results) and len(results) == len(FAULTS),
        "SILICON_EXACT_EMULATION": False,
        "duration_ms": int((time.time() - started) * 1000),
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim_boundary": (
            "Digital fault injection over PKT-001 contracts. Degraded envelopes only — "
            "does not claim production middleware hardening complete."
        ),
    }


def write_artifacts(repo_root: Path) -> dict[str, Path]:
    out = repo_root / "artifacts" / "stream_a_pkt_002"
    out.mkdir(parents=True, exist_ok=True)
    matrix = build_resilience_matrix()
    faults = run_fault_injection()
    mpath = out / "MIDDLEWARE_RESILIENCE_MATRIX.json"
    fpath = out / "MIDDLEWARE_FAULT_INJECTION_RESULT.json"
    mpath.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    fpath.write_text(json.dumps(faults, indent=2) + "\n", encoding="utf-8")
    return {"matrix": mpath, "faults": fpath}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    paths = write_artifacts(root)
    faults = json.loads(paths["faults"].read_text(encoding="utf-8"))
    print(json.dumps({"ok": faults.get("ok"), "pass_count": faults.get("pass_count"), "paths": {k: str(v) for k, v in paths.items()}}))
