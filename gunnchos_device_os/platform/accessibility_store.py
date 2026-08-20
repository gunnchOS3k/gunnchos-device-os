"""Persisted accessibility settings per profile."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.accessibility_manager import apply_settings, get_defaults, validate_coverage

SCHEMA_VERSION = 1
CLAIM_BOUNDARY = (
    "Persisted accessibility preferences per profile. "
    "HUMAN_ACCESSIBILITY_VALIDATED=false, WCAG_VALIDATED=false."
)


@dataclass
class AccessibilityStore:
    root: Path
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    corrupt: bool = False

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._load()

    def _store_path(self) -> Path:
        return self.root / "accessibility_profiles.json"

    def _load(self) -> None:
        path = self._store_path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.profiles = {}
            self.corrupt = True
            return
        self.profiles = data.get("profiles", {})
        self.corrupt = False

    def _persist(self) -> None:
        payload = {"schema_version": SCHEMA_VERSION, "profiles": self.profiles}
        self._store_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        self.corrupt = False

    def load(self, profile_id: str) -> dict[str, Any]:
        if self.corrupt:
            return {
                "ok": False,
                "profile_id": profile_id,
                "error": "store_corrupt",
                "wcag_validated": False,
                "human_accessibility_review": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        if profile_id in self.profiles:
            settings = dict(self.profiles[profile_id])
        else:
            settings = get_defaults(profile_id if profile_id != "default" else "default")
        missing = validate_coverage(settings)
        return {
            "ok": len(missing) == 0,
            "profile_id": profile_id,
            "settings": settings,
            "missing_features": missing,
            "wcag_validated": False,
            "human_accessibility_review": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def update(self, profile_id: str, overrides: dict[str, Any]) -> dict[str, Any]:
        base = self.load(profile_id)["settings"]
        merged = apply_settings({**base, **overrides})
        self.profiles[profile_id] = merged
        self._persist()
        return self.load(profile_id)

    def reset(self, profile_id: str) -> dict[str, Any]:
        defaults = get_defaults("default")
        self.profiles[profile_id] = defaults
        self._persist()
        return self.load(profile_id)

    def shell_contract(self, profile_id: str) -> dict[str, Any]:
        loaded = self.load(profile_id)
        return {
            "schema": "gunnchos.platform.accessibility.shell_contract.v1",
            "profile_id": profile_id,
            "settings": loaded["settings"],
            "wcag_validated": False,
            "human_accessibility_validated": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    @classmethod
    def from_storage(cls, root: Path) -> "AccessibilityStore":
        return cls(root=root)
