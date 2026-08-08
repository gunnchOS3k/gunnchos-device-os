"""Abuse-case suite against the runnable DEV plane (in-process).

Exercises token abuse, mode bypass attempts, oversized payloads, and path tricks.
Not a penetration test — DEV regression harness only.
"""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.cloud_dev_plane.client import DevPlaneClient
from gunnchos_device_os.cloud_dev_plane.server import DevPlaneApp, DevPlaneServer
from gunnchos_device_os.cloud_edge.services import ServiceMode


def run_abuse_suite() -> dict[str, Any]:
    server = DevPlaneServer(DevPlaneApp(role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.CLOUD)
    results: list[dict[str, Any]] = []

    def case(name: str, ok: bool, detail: Any = None) -> None:
        results.append({"case": name, "passed": ok, "detail": detail})

    # Non-DEV enrollment token rejected
    bad = client.enrollment_submit("d-abuse", "org", enrollment_token="PROD_SECRET_TOKEN")
    case("reject_prod_enrollment_token", bad.get("status") == "rejected" or bad.get("http_status") == 403, bad)

    # Mode bypass: claim cloud while client mode disconnected should still block sync via client gate
    client.set_mode(ServiceMode.DISCONNECTED)
    try:
        client.sync_enqueue("notes", "x", {"a": 1})
        case("client_blocks_sync_when_disconnected", False, "expected PermissionError")
    except PermissionError:
        case("client_blocks_sync_when_disconnected", True)

    # Oversize-ish attribute bag (still accepted but redacted if sensitive)
    client.set_mode(ServiceMode.LOCAL)
    big = client.identity_register(
        "abuse-user",
        {"email": "kid@school.test", "token": "DEV_SHOULD_REDACT", "bio": "x" * 5000},
    )
    attrs = big.get("attributes") or {}
    case(
        "redacts_sensitive_identity_attrs",
        attrs.get("email") == "[REDACTED]" and attrs.get("token") == "[REDACTED]",
        attrs,
    )

    # Path traversal style lobby id — stored as opaque string, no filesystem touch
    mm = client.matchmaking_publish("../etc/passwd", {"game": "x"})
    case("opaque_lobby_id_no_crash", mm.get("lobby_id") == "../etc/passwd", mm)

    # Fleet heartbeat in disconnected
    client.set_mode(ServiceMode.DISCONNECTED)
    try:
        client.fleet_heartbeat("fleet-abuse")
        case("fleet_blocked_disconnected", False)
    except PermissionError:
        case("fleet_blocked_disconnected", True)

    server.stop()
    passed = sum(1 for r in results if r["passed"])
    return {
        "suite": "cloud_dev_plane_abuse",
        "passed": passed,
        "total": len(results),
        "ok": passed == len(results),
        "results": results,
        "mock": False,
        "realm": "DEV",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_abuse_suite(), indent=2))
