"""gunnchPlay — library, QoS, saves, checkpoint/resume, social DEV, LAN remote-play.

Registers four first-party games as reference titles.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FIRST_PARTY_GAMES = (
    {
        "game_id": "anime-aggressors",
        "title": "Anime Aggressors",
        "path": "games/anime-aggressors-web",
        "kind": "web",
    },
    {
        "game_id": "beatlink-party",
        "title": "BeatLink Party",
        "path": "games/beatlink-party-web",
        "kind": "web",
    },
    {
        "game_id": "earth-species",
        "title": "Earth Species",
        "path": "games/earth-species-web",
        "kind": "web",
    },
    {
        "game_id": "foot-racing",
        "title": "Foot Racing",
        "path": "games/foot-racing-web",
        "kind": "web",
    },
)


@dataclass
class GameRegistration:
    game_id: str
    title: str
    path: str
    kind: str
    registered_at: float = field(default_factory=time.time)


@dataclass
class SaveSlot:
    game_id: str
    slot: int
    payload: dict[str, Any]
    checkpoint: bool = False
    at: float = field(default_factory=time.time)


@dataclass
class QosProfile:
    name: str
    target_fps: int
    max_bitrate_kbps: int
    latency_budget_ms: int


class GunnchPlay:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.library: dict[str, GameRegistration] = {}
        self.saves: list[SaveSlot] = []
        self.sessions: dict[str, dict[str, Any]] = {}
        self.social_dev: list[dict[str, Any]] = []
        self.remote_play: dict[str, Any] | None = None
        self.qos = QosProfile("balanced", target_fps=60, max_bitrate_kbps=15000, latency_budget_ms=40)

    def register_first_party(self, repo_root: Path) -> list[GameRegistration]:
        out = []
        for g in FIRST_PARTY_GAMES:
            path = repo_root / g["path"]
            exists = path.exists()
            reg = GameRegistration(
                game_id=g["game_id"],
                title=g["title"],
                path=g["path"],
                kind=g["kind"],
            )
            self.library[reg.game_id] = reg
            meta = {
                "game_id": reg.game_id,
                "title": reg.title,
                "path": reg.path,
                "kind": reg.kind,
                "tree_present": exists,
                "registered_at": reg.registered_at,
            }
            (self.root / f"{reg.game_id}.json").write_text(json.dumps(meta, indent=2) + "\n")
            out.append(reg)
        (self.root / "LIBRARY.json").write_text(
            json.dumps({"games": list(self.library)}, indent=2, default=lambda o: o.__dict__) + "\n"
        )
        return out

    def set_qos(self, name: str, **kwargs: Any) -> QosProfile:
        for k, v in kwargs.items():
            if hasattr(self.qos, k):
                setattr(self.qos, k, v)
        self.qos.name = name
        return self.qos

    def save(self, game_id: str, slot: int, payload: dict[str, Any], *, checkpoint: bool = False) -> SaveSlot:
        if game_id not in self.library:
            raise KeyError(game_id)
        s = SaveSlot(game_id=game_id, slot=slot, payload=payload, checkpoint=checkpoint)
        self.saves = [x for x in self.saves if not (x.game_id == game_id and x.slot == slot)]
        self.saves.append(s)
        path = self.root / "saves" / game_id
        path.mkdir(parents=True, exist_ok=True)
        (path / f"slot{slot}.json").write_text(json.dumps(s.__dict__, indent=2) + "\n")
        return s

    def resume(self, game_id: str, slot: int) -> dict[str, Any]:
        for s in self.saves:
            if s.game_id == game_id and s.slot == slot:
                session_id = hashlib.sha256(f"{game_id}:{slot}:{s.at}".encode()).hexdigest()[:12]
                self.sessions[session_id] = {
                    "game_id": game_id,
                    "slot": slot,
                    "checkpoint": s.checkpoint,
                    "payload": s.payload,
                    "resumed_at": time.time(),
                }
                return {"ok": True, "session_id": session_id, "payload": s.payload}
        return {"ok": False, "error": "save_not_found"}

    def social_dev_announce(self, game_id: str, message: str) -> dict[str, Any]:
        """DEV-only social service (not production online)."""
        entry = {
            "game_id": game_id,
            "message": message,
            "channel": "dev_lan",
            "at": time.time(),
            "production_online": False,
        }
        self.social_dev.append(entry)
        return entry

    def start_lan_remote_play(self, host_game: str, client_device: str) -> dict[str, Any]:
        if host_game not in self.library:
            raise KeyError(host_game)
        self.remote_play = {
            "schema": "gunnchos.phase_xiv.remote_play_lan.v1",
            "host_game": host_game,
            "client_device": client_device,
            "qos": self.qos.__dict__,
            "transport": "lan_udp_foundation",
            "production_wan": False,
            "started_at": time.time(),
        }
        (self.root / "REMOTE_PLAY.json").write_text(json.dumps(self.remote_play, indent=2) + "\n")
        return dict(self.remote_play)

    def e2e(self, repo_root: Path) -> dict[str, Any]:
        regs = self.register_first_party(repo_root)
        self.set_qos("performance", target_fps=90, max_bitrate_kbps=25000, latency_budget_ms=25)
        save = self.save("anime-aggressors", 1, {"level": 3, "score": 1200}, checkpoint=True)
        resumed = self.resume("anime-aggressors", 1)
        social = self.social_dev_announce("beatlink-party", "looking for LAN co-op")
        remote = self.start_lan_remote_play("foot-racing", "handheld-01")
        ok = (
            len(regs) == 4
            and resumed.get("ok")
            and save.checkpoint
            and social["production_online"] is False
            and remote["production_wan"] is False
        )
        return {
            "ok": ok,
            "library_count": len(regs),
            "resume": resumed,
            "social_dev": social,
            "remote_play": remote,
            "qos": self.qos.__dict__,
        }
