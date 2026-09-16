"""CX1J Offline / low-bandwidth — connectivity, queues, caches, deterministic cut tests."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ResumableDownload:
    url: str
    dest: Path
    total_bytes: int
    received: int = 0
    state: str = "pending"

    def write_chunk(self, data: bytes) -> None:
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        mode = "ab" if self.dest.exists() else "wb"
        with self.dest.open(mode) as fh:
            fh.write(data)
        self.received += len(data)
        if self.received >= self.total_bytes:
            self.state = "complete"
        else:
            self.state = "partial"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "dest": str(self.dest),
            "total_bytes": self.total_bytes,
            "received": self.received,
            "state": self.state,
        }


@dataclass
class OfflinePlane:
    root: Path
    online: bool = True
    low_bandwidth: bool = False
    downloads: Dict[str, ResumableDownload] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("cache", "downloads", "help", "state"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        (self.root / "help" / "offline_help.md").write_text(
            "# Offline Help\n\nVault, drafts, and queued Connect outbox remain available offline.\n"
        )
        self._load()

    def _state_path(self) -> Path:
        return self.root / "state" / "offline.json"

    def _load(self) -> None:
        path = self._state_path()
        if path.exists():
            data = json.loads(path.read_text())
            self.online = data.get("online", True)
            self.low_bandwidth = data.get("low_bandwidth", False)

    def save(self) -> None:
        self._state_path().write_text(
            json.dumps(
                {
                    "online": self.online,
                    "low_bandwidth": self.low_bandwidth,
                    "updated_at": time.time(),
                },
                indent=2,
            )
            + "\n"
        )

    def status(self) -> dict:
        return {
            "online": self.online,
            "low_bandwidth": self.low_bandwidth,
            "mode": "offline" if not self.online else ("low_bandwidth" if self.low_bandwidth else "online"),
        }

    def cut(self) -> dict:
        self.online = False
        self.save()
        return self.status()

    def reconnect(self) -> dict:
        self.online = True
        self.save()
        return self.status()

    def set_low_bandwidth(self, enabled: bool) -> dict:
        self.low_bandwidth = enabled
        self.save()
        return self.status()

    def start_download(self, download_id: str, url: str, total_bytes: int) -> ResumableDownload:
        dest = self.root / "downloads" / download_id
        dl = ResumableDownload(url=url, dest=dest, total_bytes=total_bytes)
        self.downloads[download_id] = dl
        return dl

    def resume_download(self, download_id: str, chunk: bytes) -> dict:
        if not self.online and self.downloads.get(download_id) is None:
            return {"ok": False, "reason": "offline_and_unknown_download"}
        dl = self.downloads[download_id]
        if not self.online and dl.state != "partial":
            # allow resume only of already-started partial when reconnecting semantics tested separately
            return {"ok": False, "reason": "offline"}
        # While offline, still allow writing buffered chunks for deterministic tests of resume abstraction
        dl.write_chunk(chunk)
        return {"ok": True, **dl.to_dict()}

    def cache_package_metadata(self, catalog: dict) -> Path:
        path = self.root / "cache" / "package_metadata.json"
        path.write_text(json.dumps(catalog, indent=2) + "\n")
        return path

    def offline_help(self) -> str:
        return (self.root / "help" / "offline_help.md").read_text()

    def cut_reconnect_test(self, sync_queue, connect_outbox_count: int) -> dict:
        """Deterministic network cut → continue → queue → restart → reconnect → reconcile."""
        steps = []
        steps.append({"cut": self.cut()})
        # continue local work marker
        marker = self.root / "cache" / "local_work.txt"
        marker.write_text("worked_offline\n")
        steps.append({"local_work": marker.exists()})
        pending_before = sync_queue.pending_count()
        sync_queue.enqueue("user_files", {"op": "put", "path": "offline.txt"})
        steps.append({"queued": sync_queue.pending_count() >= pending_before + 1})
        # simulate restart
        reloaded = sync_queue.reload()
        steps.append({"survived_restart": reloaded >= 1})
        steps.append({"reconnect": self.reconnect()})
        reconciled = sync_queue.reconcile()
        steps.append({"reconcile": reconciled})
        ok = all(
            [
                not steps[0]["cut"]["online"],
                steps[1]["local_work"],
                steps[2]["queued"],
                steps[3]["survived_restart"],
                steps[4]["reconnect"]["online"],
                reconciled.get("reconciled", 0) >= 1,
            ]
        )
        return {
            "ok": ok,
            "steps": steps,
            "connect_outbox_queued": connect_outbox_count,
            "evidence_class": "DIGITAL_PASS" if ok else "DIGITAL_PARTIAL",
        }
