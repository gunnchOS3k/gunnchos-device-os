"""Filesystem layout contract for Stage 2 image-based host."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

# Absolute path names as they appear on device; tests use a writable sysroot.
CONTRACT_DIRS = (
    "system-a",
    "system-b",
    "apps",
    "games",
    "models",
    "home",
    "data",
    "recovery",
    "dev-environments",
)

IMMUTABLE_SLOTS = frozenset({"system-a", "system-b", "recovery"})
MUTABLE_LAYERS = frozenset(
    {"apps", "games", "models", "home", "data", "dev-environments"}
)


@dataclass
class SysrootLayout:
    root: Path
    created: list[str]

    def path(self, name: str) -> Path:
        return self.root / name

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "created": list(self.created),
            "contract_dirs": list(CONTRACT_DIRS),
            "immutable_slots": sorted(IMMUTABLE_SLOTS),
            "mutable_layers": sorted(MUTABLE_LAYERS),
        }


def ensure_sysroot(root: Path | str) -> SysrootLayout:
    """Materialize the Stage 2 filesystem contract under *root* (writable)."""
    root_path = Path(root).resolve()
    # Guard: never write host-local absolute user homes into artifacts.
    if "/Users/" in str(root_path) and "artifacts" not in str(root_path):
        raise ValueError(
            "sysroot must live under a workspace artifacts tree, not a host home path"
        )
    created: list[str] = []
    root_path.mkdir(parents=True, exist_ok=True)
    for name in CONTRACT_DIRS:
        p = root_path / name
        p.mkdir(parents=True, exist_ok=True)
        marker = p / ".gunnchos_layout"
        if not marker.exists():
            marker.write_text(f"layout={name}\n", encoding="utf-8")
        created.append(name)
    # Slot metadata skeleton
    for slot in ("system-a", "system-b"):
        meta = root_path / slot / "slot.json"
        if not meta.exists():
            meta.write_text(
                '{"slot":"%s","version":null,"state":"empty"}\n' % slot[-1].upper(),
                encoding="utf-8",
            )
    return SysrootLayout(root=root_path, created=created)


def verify_contract(root: Path | str) -> dict[str, Any]:
    root_path = Path(root)
    missing = [n for n in CONTRACT_DIRS if not (root_path / n).is_dir()]
    return {
        "ok": not missing,
        "missing": missing,
        "root": str(root_path),
        "contract": asdict(SysrootLayout(root=root_path, created=list(CONTRACT_DIRS)))
        if not missing
        else None,
    }
