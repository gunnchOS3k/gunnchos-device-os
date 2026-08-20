"""Userspace recovery environment — honest software path only."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CLAIM_BOUNDARY = (
    "Userspace recovery orchestration only. Not physical recovery partition, "
    "not verified boot chain, not factory RMA hardware path."
)


@dataclass
class UserspaceRecoveryEnv:
    root: Path
    slots: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_slot: str = "A"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        state_path = self.root / "recovery_state.json"
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.slots = data.get("slots", {})
            self.active_slot = data.get("active_slot", "A")
        else:
            self.slots = {
                "A": {"version": "1.0.0", "verified": True, "corrupt": False},
                "B": {"version": None, "verified": False, "corrupt": False},
            }
            self._persist()

    def _persist(self) -> None:
        (self.root / "recovery_state.json").write_text(
            json.dumps(
                {"active_slot": self.active_slot, "slots": self.slots, "claim_boundary": CLAIM_BOUNDARY},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def inspect(self) -> dict[str, Any]:
        return {
            "ok": True,
            "active_slot": self.active_slot,
            "slots": self.slots,
            "userspace_only": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def select_boot_slot(self, *, require_verified: bool = True, corrupt_active: bool = False) -> dict[str, Any]:
        if corrupt_active:
            self.slots[self.active_slot]["corrupt"] = True
            self.slots[self.active_slot]["verified"] = False
        candidates = [
            slot
            for slot, meta in self.slots.items()
            if meta.get("verified") and not meta.get("corrupt")
        ]
        if require_verified and not candidates:
            self._persist()
            return {"ok": False, "error": "no_verified_slot", "selected_verified": False}
        chosen = candidates[0] if candidates else self.active_slot
        self.active_slot = chosen
        self._persist()
        return {
            "ok": True,
            "selected": chosen,
            "selected_verified": self.slots[chosen].get("verified", False),
        }
