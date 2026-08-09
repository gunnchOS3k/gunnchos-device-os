"""Adopter API client with version negotiation (digital / DEV)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import urllib.error
import urllib.request

# Local policy mirror — keep in sync with gunnchos_device_os.cont_viii.api_abi_policy
CURRENT = {
    "app_manifest": "1.2.0",
    "permissions": "1.1.0",
    "device_role": "1.0.0",
    "ring_input": "1.3.0",
    "ai": "1.0.0",
    "connectivity": "1.1.0",
    "telemetry": "1.0.0",
    "fleet": "1.0.0",
    "save_cloud": "1.0.0",
}


@dataclass
class AdopterClient:
    """HTTP-capable client; negotiation works offline against embedded policy."""

    base_url: str = "http://127.0.0.1:8080"
    api_version: str = "1.0.0"
    timeout_s: float = 2.0
    last_error: str | None = field(default=None, init=False)

    def negotiate(self, surface: str, requested: str) -> dict[str, Any]:
        if surface not in CURRENT:
            return {"ok": False, "reason": "unknown_surface", "surface": surface}
        current = CURRENT[surface]
        req_major = int(requested.split(".")[0])
        cur_major = int(current.split(".")[0])
        if req_major != cur_major:
            return {
                "ok": False,
                "surface": surface,
                "requested": requested,
                "current": current,
                "reason": "major_mismatch",
            }
        return {
            "ok": True,
            "surface": surface,
            "requested": requested,
            "negotiated": requested if requested <= current else current,
            "current": current,
            "compatibility": "compatible",
        }

    def get_json(self, path: str) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.last_error = str(exc)
            return {"ok": False, "error": str(exc), "offline_fallback": True}

    def sample_device_role(self, role: str = "student") -> dict[str, Any]:
        nego = self.negotiate("device_role", "1.0.0")
        return {"ok": nego.get("ok"), "role": role, "negotiation": nego}

    def sample_ring_input(self, gesture: str = "tap") -> dict[str, Any]:
        nego = self.negotiate("ring_input", "1.3.0")
        return {
            "ok": nego.get("ok"),
            "gesture": gesture,
            "destructive_requires_confirm": True,
            "negotiation": nego,
        }

    def sample_ai(self, prompt: str) -> dict[str, Any]:
        nego = self.negotiate("ai", "1.0.0")
        return {
            "ok": nego.get("ok"),
            "mode": "local_first",
            "prompt": prompt,
            "cloud_export": False,
            "negotiation": nego,
        }

    def sample_connectivity(self) -> dict[str, Any]:
        nego = self.negotiate("connectivity", "1.1.0")
        return {
            "ok": nego.get("ok"),
            "bearers": ["ethernet", "wifi", "terrestrial", "ntn_simulated"],
            "negotiation": nego,
        }

    def sample_telemetry(self, event: str = "app_launch") -> dict[str, Any]:
        nego = self.negotiate("telemetry", "1.0.0")
        return {
            "ok": nego.get("ok"),
            "event": event,
            "pii": False,
            "negotiation": nego,
        }
