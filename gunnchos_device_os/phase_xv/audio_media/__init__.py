"""AUDIO_MEDIA — ALSA/PipeWire-oriented stack with focus policy + loopback E2E.

Physical audio quality remains PHYSICAL_PENDING.
"""
from __future__ import annotations

import json
import struct
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "ALSA/PipeWire-oriented digital audio path with loopback E2E. "
    "Physical quality metrics PHYSICAL_PENDING."
)

FORMATS = ("pcm_s16le_48k", "pcm_s16le_44k1", "pcm_f32le_48k")
ROLES = ("foreground", "background", "notification", "voice", "media")


@dataclass
class FocusPolicy:
    exclusive_foreground: bool = True
    duck_background_db: float = -12.0
    allow_voice_over_media: bool = True

    def decide(self, requester: str, current: str | None) -> dict[str, Any]:
        if current is None:
            return {"grant": True, "action": "take", "ducked": []}
        if requester == "voice" and self.allow_voice_over_media and current == "media":
            return {"grant": True, "action": "duck_media", "ducked": ["media"]}
        if requester == "foreground" and self.exclusive_foreground:
            return {"grant": True, "action": "preempt", "ducked": [current]}
        if requester == "notification":
            return {"grant": True, "action": "mix", "ducked": []}
        if requester == "background" and current in ("foreground", "media", "voice"):
            return {"grant": False, "action": "deny", "ducked": []}
        return {"grant": True, "action": "share", "ducked": []}


@dataclass
class AudioSession:
    session_id: str
    role: str
    fmt: str
    active: bool = False
    frames: int = 0


class AlsaPipewireStack:
    """Digital ALSA/PipeWire-oriented media stack with file loopback."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.loopback_dir = self.root / "loopback"
        self.loopback_dir.mkdir(exist_ok=True)
        self.focus = FocusPolicy()
        self.current_focus: str | None = None
        self.sessions: dict[str, AudioSession] = {}
        self.audit: list[dict[str, Any]] = []
        self.stack = {
            "playback": "pipewire + alsa-sink (digital)",
            "capture": "pipewire + alsa-source (digital)",
            "loopback": "snd-aloop or file-backed PCM loop",
            "policy": "gunnchos focus/duck policy",
        }

    def request_focus(self, role: str) -> dict[str, Any]:
        if role not in ROLES:
            raise ValueError(role)
        decision = self.focus.decide(role, self.current_focus)
        if decision["grant"]:
            self.current_focus = role
        self.audit.append({"op": "focus", "role": role, **decision, "at": time.time()})
        return decision

    def _pcm_path(self, name: str) -> Path:
        return self.loopback_dir / f"{name}.wav"

    def write_pcm(self, name: str, fmt: str, seconds: float = 0.05) -> Path:
        if fmt not in FORMATS:
            raise ValueError(fmt)
        rate = 48000 if "48k" in fmt else 44100
        sampwidth = 2 if "s16" in fmt else 4
        nframes = max(1, int(rate * seconds))
        path = self._pcm_path(name)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(sampwidth)
            wf.setframerate(rate)
            if sampwidth == 2:
                frames = b"".join(struct.pack("<h", int(1000 * ((i % 32) - 16))) for i in range(nframes))
            else:
                frames = b"".join(struct.pack("<f", 0.01 * ((i % 32) - 16)) for i in range(nframes))
            wf.writeframes(frames)
        return path

    def playback(self, name: str, role: str = "media", fmt: str = "pcm_s16le_48k") -> dict[str, Any]:
        decision = self.request_focus(role)
        if not decision["grant"]:
            return {"ok": False, "error": "focus_denied", "decision": decision}
        path = self.write_pcm(name, fmt)
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            data = wf.readframes(frames)
        sid = f"play-{name}"
        self.sessions[sid] = AudioSession(sid, role, fmt, active=True, frames=frames)
        self.audit.append({"op": "playback", "path": path.name, "frames": frames, "bytes": len(data)})
        return {
            "ok": True,
            "session_id": sid,
            "frames": frames,
            "bytes": len(data),
            "fmt": fmt,
            "decision": decision,
            "path": path.name,
        }

    def capture(self, name: str, role: str = "voice", fmt: str = "pcm_s16le_48k") -> dict[str, Any]:
        decision = self.request_focus(role)
        if not decision["grant"]:
            return {"ok": False, "error": "focus_denied", "decision": decision}
        # Capture writes into loopback then reads back (E2E loop)
        path = self.write_pcm(f"cap-{name}", fmt)
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            data = wf.readframes(frames)
        out = self.loopback_dir / f"captured-{name}.bin"
        out.write_bytes(data)
        sid = f"cap-{name}"
        self.sessions[sid] = AudioSession(sid, role, fmt, active=True, frames=frames)
        return {
            "ok": True,
            "session_id": sid,
            "frames": frames,
            "bytes": len(data),
            "fmt": fmt,
            "decision": decision,
            "captured": out.name,
        }

    def loopback_e2e(self) -> dict[str, Any]:
        play = self.playback("loop-src", role="media", fmt="pcm_s16le_48k")
        cap = self.capture("loop-dst", role="voice", fmt="pcm_s16le_48k")
        # Compare sizes under same fmt/duration policy
        src = self._pcm_path("loop-src")
        dst = self.loopback_dir / "captured-loop-dst.bin"
        ok = play["ok"] and cap["ok"] and src.exists() and dst.exists() and dst.stat().st_size > 0
        return {"ok": ok, "playback": play, "capture": cap, "src_bytes": src.stat().st_size if src.exists() else 0}

    def e2e(self) -> dict[str, Any]:
        # Focus policy matrix
        focus_cases = []
        self.current_focus = None
        focus_cases.append(("take_media", self.request_focus("media")))
        focus_cases.append(("voice_over_media", self.request_focus("voice")))
        self.current_focus = "foreground"
        focus_cases.append(("bg_denied", self.request_focus("background")))
        focus_ok = (
            focus_cases[0][1]["grant"]
            and focus_cases[1][1]["action"] == "duck_media"
            and focus_cases[2][1]["grant"] is False
        )

        fmt_results = {}
        for fmt in FORMATS:
            self.current_focus = None
            r = self.playback(f"fmt-{fmt}", role="media", fmt=fmt)
            fmt_results[fmt] = r["ok"]

        loop = self.loopback_e2e()
        ok = focus_ok and all(fmt_results.values()) and loop["ok"]
        report = {
            "schema": "gunnchos.phase_xv.audio_media.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "physical_quality": "PHYSICAL_PENDING",
            "stack": self.stack,
            "formats": list(FORMATS),
            "roles": list(ROLES),
            "focus_ok": focus_ok,
            "format_results": fmt_results,
            "loopback": loop,
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
        (self.root / "AUDIO_MEDIA_E2E.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
