"""Storage backend — sparse image + removable media lifecycle."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StorageBackend:
    root: Path
    images: dict[str, Path] = field(default_factory=dict)
    removable_present: bool = True

    def start(self, profile: dict[str, Any], work: Path) -> dict[str, Any]:
        self.root = work / "storage"
        self.root.mkdir(parents=True, exist_ok=True)
        img = self.root / "system.img"
        # sparse-ish: write small header + size claim
        payload = b"GUNNCHDEVICE_LAB_STORAGE_V01\n" + (profile.get("profile_id") or "").encode()
        img.write_bytes(payload)
        self.images["system"] = img
        rem = self.root / "removable.img"
        rem.write_bytes(b"REMOVABLE\n")
        self.images["removable"] = rem
        self.removable_present = True
        return {
            "ok": True,
            "images": {k: str(v) for k, v in self.images.items()},
            "sha256_system": hashlib.sha256(img.read_bytes()).hexdigest(),
            "backend": "file_sparse_image",
        }

    def remove_removable(self) -> dict[str, Any]:
        self.removable_present = False
        p = self.images.get("removable")
        if p and p.exists():
            p.unlink()
        return {"ok": True, "removable_present": False}

    def reset(self) -> dict[str, Any]:
        for p in self.images.values():
            if p.exists():
                p.unlink()
        self.images.clear()
        return {"ok": True, "reset": True}
