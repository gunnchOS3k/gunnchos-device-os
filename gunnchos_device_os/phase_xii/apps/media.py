"""Real media playback via ffmpeg/ffplay/mpv."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.phase_xii.apps.detect import which_first


def ensure_fixture_wav(path: Path, seconds: float = 1.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    ffmpeg = which_first(["ffmpeg"])
    if ffmpeg:
        subprocess.run(
            [ffmpeg["path"], "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-ac", "1", str(path)],
            capture_output=True,
            timeout=30,
        )
        if path.exists():
            return path
    # PCM WAV header + silence
    import struct, wave
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        frames = int(16000 * seconds)
        w.writeframes(b"\\x00\\x00" * frames)
    return path


def play_audio(path: Path, evidence: Path) -> dict[str, Any]:
    evidence.mkdir(parents=True, exist_ok=True)
    ensure_fixture_wav(path)
    started = time.time()
    player = which_first(["ffplay", "mpv", "vlc", "ffmpeg"])
    if not player:
        return {"ok": False, "error": "no_media_player", "defect": "XR-DEFECT-MEDIA", "execution_depth": "L0_GENERIC_OK"}
    if player["name"] == "ffmpeg":
        # decode-only proof
        r = subprocess.run([player["path"], "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, timeout=30)
        ok = r.returncode == 0
    elif player["name"] == "ffplay":
        r = subprocess.run([player["path"], "-autoexit", "-nodisp", "-t", "1", str(path)], capture_output=True, text=True, timeout=30)
        ok = r.returncode == 0
    else:
        r = subprocess.run([player["path"], "--length=1", "--vo=null", "--ao=null", str(path)], capture_output=True, text=True, timeout=30)
        ok = r.returncode == 0
    (evidence / "media.log").write_text((r.stdout or "") + "\\n" + (r.stderr or ""), encoding="utf-8")
    return {
        "ok": ok,
        "player": player,
        "path": str(path),
        "execution_depth": "L4_REAL_APPLICATION_PROCESS",
        "duration_ms": int((time.time() - started) * 1000),
    }
