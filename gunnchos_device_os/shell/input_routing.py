"""Normalized input routing with remapping persistence (Wave 002 / OS-PLATFORM-005)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.input_router import InputRouter


INPUT_SOURCES = ("touch", "controller", "keyboard_mouse", "ring")


DEFAULT_REMAPS: dict[str, dict[str, str]] = {
    "handheld": {
        "controller.a": "confirm",
        "controller.b": "back",
        "touch.tap": "select",
    },
    "docked": {
        "keyboard_mouse.enter": "confirm",
        "controller.a": "confirm",
    },
    "ds_xl": {
        "ring.click": "pointer_button",
        "keyboard_mouse.enter": "confirm",
    },
}


@dataclass
class InputRoutingService:
    router: InputRouter = field(default_factory=InputRouter)
    remaps: dict[str, dict[str, str]] = field(default_factory=lambda: dict(DEFAULT_REMAPS))
    store_path: Path | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.store_path and self.store_path.exists():
            self.load()

    def normalize(self, source: str, raw_event: dict[str, Any], *, form_factor: str = "handheld") -> dict[str, Any]:
        if source not in INPUT_SOURCES:
            raise ValueError(f"unsupported input source: {source}")
        key = raw_event.get("binding") or raw_event.get("kind") or "unknown"
        remap_key = f"{source}.{key}"
        profile = self.remaps.get(form_factor, {})
        mapped = profile.get(remap_key, key)
        normalized = {
            "source": source,
            "raw_kind": key,
            "mapped_action": mapped,
            "form_factor": form_factor,
            "payload": dict(raw_event),
        }
        self.events.append(normalized)
        return normalized

    def deliver(self, source: str, raw_event: dict[str, Any], *, form_factor: str = "handheld") -> dict[str, Any]:
        norm = self.normalize(source, raw_event, form_factor=form_factor)
        payload = {
            **norm["payload"],
            "kind": norm["mapped_action"],
            "source": source,
            "confidence": float(raw_event.get("confidence", 0.95)),
            "target": raw_event.get("target", self.router.surfaces.focus),
        }
        result = self.router.deliver(payload)
        return {"normalized": norm, "delivery": result}

    def set_remap(self, form_factor: str, binding: str, action: str) -> None:
        self.remaps.setdefault(form_factor, {})[binding] = action
        self.persist()

    def persist(self) -> None:
        if self.store_path is None:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps({"schema": "gunnchos.shell.input_remaps.v1", "remaps": self.remaps}, indent=2) + "\n",
            encoding="utf-8",
        )

    def load(self) -> None:
        if self.store_path is None or not self.store_path.exists():
            return
        data = json.loads(self.store_path.read_text(encoding="utf-8"))
        self.remaps = dict(data.get("remaps") or DEFAULT_REMAPS)

    def status(self) -> dict[str, Any]:
        return {
            "sources": list(INPUT_SOURCES),
            "form_factors": sorted(self.remaps.keys()),
            "events": len(self.events),
            "router_summary": self.router.summary(),
            "persisted": self.store_path is not None and bool(self.store_path.exists()),
        }
