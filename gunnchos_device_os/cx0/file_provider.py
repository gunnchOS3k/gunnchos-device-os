"""FileProvider interface (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Protocol


class FileProvider(Protocol):
    provider_id: str

    def list(self, uri: str) -> List[str]: ...
    def read_bytes(self, uri: str) -> bytes: ...
    def write_bytes(self, uri: str, data: bytes) -> None: ...


@dataclass
class LocalPathFileProvider:
    """Local filesystem provider for tests — not a cloud Files UX."""

    root: Path
    provider_id: str = "gunnchos.cx0.file_provider.local.v1"
    uri_schemes: List[str] = field(default_factory=lambda: ["file"])
    capabilities: List[str] = field(
        default_factory=lambda: ["list", "read", "write"]
    )

    def _resolve(self, uri: str) -> Path:
        if uri.startswith("file://"):
            uri = uri[len("file://") :]
        path = Path(uri)
        if not path.is_absolute():
            path = self.root / path
        resolved = path.resolve()
        root = self.root.resolve()
        if root not in resolved.parents and resolved != root:
            raise PermissionError(f"uri_escapes_provider_root:{uri}")
        return resolved

    def list(self, uri: str) -> List[str]:
        path = self._resolve(uri)
        if not path.exists():
            return []
        if path.is_file():
            return [path.name]
        return sorted(p.name for p in path.iterdir())

    def read_bytes(self, uri: str) -> bytes:
        return self._resolve(uri).read_bytes()

    def write_bytes(self, uri: str, data: bytes) -> None:
        path = self._resolve(uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "uri_schemes": self.uri_schemes,
            "capabilities": self.capabilities,
            "offline_cache": True,
            "claim_boundary": "local_scaffold_only",
        }
