"""Persist per-profile network preferences via Wave004 encrypted storage."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gunnchos_device_os.network_decision.models import UserPreferenceProfile
from gunnchos_device_os.platform.encrypted_storage import SoftwareKeystore


@dataclass
class UserPreferenceStore:
    root: Path
    profile_id: str = "default"
    namespace: str = "network_decision_prefs"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.keystore = SoftwareKeystore(self.root / "keystore")

    def set_preference(self, preference: UserPreferenceProfile | str) -> dict[str, Any]:
        if isinstance(preference, str):
            preference = UserPreferenceProfile(preference)
        payload = {
            "profile_id": self.profile_id,
            "preference": preference.value,
            "schema": "gunnchos.network_decision.user_preference.v1",
        }
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return self.keystore.put(self.profile_id, raw, namespace=self.namespace)

    def get_preference(self) -> UserPreferenceProfile | None:
        got = self.keystore.get(self.profile_id, namespace=self.namespace)
        if not got.get("ok"):
            return None
        data = json.loads(got["plaintext"].decode("utf-8"))
        return UserPreferenceProfile(data["preference"])

    def prove_persistence_across_restart(self) -> dict[str, Any]:
        self.set_preference(UserPreferenceProfile.PREFER_BATTERY)
        reloaded = UserPreferenceStore(self.root, profile_id=self.profile_id, namespace=self.namespace)
        got = reloaded.get_preference()
        return {
            "ok": got == UserPreferenceProfile.PREFER_BATTERY,
            "stored": UserPreferenceProfile.PREFER_BATTERY.value,
            "loaded": None if got is None else got.value,
            "software_keystore": True,
            "TPM_KEYSTORE": False,
        }
