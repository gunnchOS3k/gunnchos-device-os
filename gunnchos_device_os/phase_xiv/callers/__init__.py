"""Cross-product callers — WAIKE, Creator, Device Manager, Archive, connectivity.

All call the OS AI System API (never model paths). Optionally forward to gunnchAI
Stage 2 `/v1/capability/*` per OS_CALLER_CONTRACT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.phase_xiv.ai_system import AiRequest, OsAiSystemApi


PRODUCTS = ("waike", "creator", "device_manager", "archive", "connectivity_diagnostics")


@dataclass
class CallerResult:
    product: str
    capability: str
    ok: bool
    text: str
    via: str
    model_path_exposed: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "capability": self.capability,
            "ok": self.ok,
            "text": self.text,
            "via": self.via,
            "model_path_exposed": self.model_path_exposed,
            "details": self.details,
        }


class CrossProductCallers:
    def __init__(self, api: OsAiSystemApi):
        self.api = api

    def waike_tutor(self, topic: str, user_id: str = "student") -> CallerResult:
        r = self.api.invoke(AiRequest("tutor", topic, user_id=user_id, grant=["memory"]))
        return CallerResult("waike", "tutor", r.ok, r.text, r.source, r.model_path_exposed, r.route)

    def creator_summarize(self, draft: str, user_id: str = "creator") -> CallerResult:
        r = self.api.invoke(AiRequest("summarize", draft, user_id=user_id))
        return CallerResult("creator", "summarize", r.ok, r.text, r.source, r.model_path_exposed, r.route)

    def device_manager_diagnose(self, symptom: str, user_id: str = "admin") -> CallerResult:
        r = self.api.invoke(
            AiRequest("diagnose", symptom, user_id=user_id, grant=["device"])
        )
        return CallerResult(
            "device_manager", "diagnose", r.ok, r.text, r.source, r.model_path_exposed, r.route
        )

    def archive_classify(self, label_hint: str, user_id: str = "archivist") -> CallerResult:
        r = self.api.invoke(AiRequest("classify", label_hint, user_id=user_id))
        return CallerResult("archive", "classify", r.ok, r.text, r.source, r.model_path_exposed, r.route)

    def connectivity_diagnose(self, report: str, user_id: str = "netops") -> CallerResult:
        r = self.api.invoke(
            AiRequest("diagnose", f"connectivity: {report}", user_id=user_id, grant=["network", "device"])
        )
        return CallerResult(
            "connectivity_diagnostics",
            "diagnose",
            r.ok,
            r.text,
            r.source,
            r.model_path_exposed,
            r.route,
        )

    def run_all_smoke(self) -> dict[str, Any]:
        results = [
            self.waike_tutor("OFDM basics"),
            self.creator_summarize("Draft blog about dual-screen study mode"),
            self.device_manager_diagnose("Wi-Fi drops after dock undock"),
            self.archive_classify("field notes from campus walk"),
            self.connectivity_diagnose("5G NSA attach failed; fallback LTE ok"),
        ]
        ok = all(r.ok for r in results) and all(not r.model_path_exposed for r in results)
        return {
            "ok": ok,
            "products": PRODUCTS,
            "results": [r.to_dict() for r in results],
            "contract": "OS_CALLER_CONTRACT /v1/capability/*",
        }
