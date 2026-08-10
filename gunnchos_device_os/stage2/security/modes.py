"""CONSUMER / DEVELOPER / SECURE_DEVELOPER modes with audited escalation."""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any


class SecurityMode(str, Enum):
    CONSUMER = "CONSUMER"
    DEVELOPER = "DEVELOPER"
    SECURE_DEVELOPER = "SECURE_DEVELOPER"


MODE_CAPS = {
    SecurityMode.CONSUMER: {
        "terminal": False,
        "containers": False,
        "custom_runtimes": False,
        "hw_debug": False,
        "strong_sandbox": True,
    },
    SecurityMode.DEVELOPER: {
        "terminal": True,
        "containers": True,
        "custom_runtimes": True,
        "hw_debug": True,
        "strong_sandbox": False,
    },
    SecurityMode.SECURE_DEVELOPER: {
        "terminal": True,
        "containers": True,
        "custom_runtimes": True,
        "hw_debug": True,
        "strong_sandbox": True,
        "isolated_builds": True,
        "explicit_elevation": True,
    },
}


class ModeManager:
    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "mode.json"
        self.audit = self.state_dir / "mode_audit.jsonl"
        if not self.state_path.exists():
            self._save({"mode": SecurityMode.CONSUMER.value, "previous": None})

    def _save(self, doc: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(doc, indent=2) + "\n")

    def _load(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text())

    def current(self) -> SecurityMode:
        return SecurityMode(self._load()["mode"])

    def escalate(self, target: SecurityMode, *, reason: str) -> dict[str, Any]:
        cur = self.current()
        doc = {"mode": target.value, "previous": cur.value, "reason": reason}
        self._save(doc)
        with self.audit.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "event": "escalate",
                        "from": cur.value,
                        "to": target.value,
                        "reason": reason,
                    }
                )
                + "\n"
            )
        return {
            "ok": True,
            "mode": target.value,
            "previous": cur.value,
            "caps": MODE_CAPS[target],
            "logged": True,
        }

    def revert(self) -> dict[str, Any]:
        doc = self._load()
        prev = doc.get("previous")
        if not prev:
            return {"ok": False, "reason": "no_previous"}
        cur = doc["mode"]
        new_doc = {"mode": prev, "previous": None, "reverted_from": cur}
        self._save(new_doc)
        with self.audit.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps({"event": "revert", "from": cur, "to": prev}) + "\n"
            )
        return {
            "ok": True,
            "mode": prev,
            "reverted_from": cur,
            "logged": True,
            "reversible": True,
        }

    def audit_log(self) -> list[dict[str, Any]]:
        if not self.audit.exists():
            return []
        return [json.loads(line) for line in self.audit.read_text().splitlines() if line.strip()]
