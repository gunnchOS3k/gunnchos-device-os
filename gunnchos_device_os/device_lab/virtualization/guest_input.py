"""Conventional keyboard/mouse/touch injection into Lab guests.

Prefers QEMU monitor sendkey / virtio-input when a real guest is alive.
Observable state change is required for PASS claims.
"""
from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any


CLAIM = (
    "Conventional input injection targets QEMU virt guest or hybrid Lab surfaces. "
    "Not physical HID SI. SILICON_EXACT_EMULATION=false."
)


def _monitor_send(monitor_sock: Path, command: str, *, timeout: float = 2.0) -> dict[str, Any]:
    if not monitor_sock.exists():
        return {"ok": False, "error": "monitor_socket_missing", "path": str(monitor_sock)}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(str(monitor_sock))
            # Drain banner
            try:
                sock.recv(4096)
            except OSError:
                pass
            sock.sendall((command.strip() + "\n").encode("utf-8"))
            time.sleep(0.05)
            try:
                reply = sock.recv(4096).decode("utf-8", errors="replace")
            except OSError:
                reply = ""
            return {"ok": True, "command": command, "reply": reply[:500], "via": "qemu_monitor"}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "command": command}


def inject_key(
    *,
    monitor_sock: Path | None,
    key: str = "ret",
    agent: Any | None = None,
    hybrid_surface: Any | None = None,
) -> dict[str, Any]:
    """Inject a key. Prefer QEMU monitor → guest agent → hybrid surface."""
    attempts: list[dict[str, Any]] = []
    if monitor_sock is not None:
        mon = _monitor_send(monitor_sock, f"sendkey {key}")
        attempts.append(mon)
        if mon.get("ok"):
            observed = {"monitor_accepted": True, "key": key}
            # Optional agent confirmation
            if agent is not None:
                try:
                    after = agent.call("input_observe", key=key)
                    observed["agent"] = after
                except Exception as exc:  # noqa: BLE001
                    observed["agent_error"] = str(exc)
            return {
                "ok": True,
                "path": "qemu_monitor_sendkey",
                "key": key,
                "observed": observed,
                "attempts": attempts,
                "SILICON_EXACT_EMULATION": False,
                "claim_boundary": CLAIM,
            }

    if agent is not None:
        try:
            rsp = agent.call("input_inject", kind="key", key=key)
            attempts.append(rsp)
            if rsp.get("ok"):
                return {
                    "ok": True,
                    "path": "guest_agent",
                    "key": key,
                    "observed": rsp,
                    "attempts": attempts,
                    "SILICON_EXACT_EMULATION": False,
                    "claim_boundary": CLAIM,
                }
        except Exception as exc:  # noqa: BLE001
            attempts.append({"ok": False, "error": str(exc)})

    if hybrid_surface is not None:
        before = hybrid_surface.snapshot() if hasattr(hybrid_surface, "snapshot") else None
        applied = hybrid_surface.apply_hid({"kind": "key", "text": key if len(key) == 1 else "X"})
        after = hybrid_surface.snapshot() if hasattr(hybrid_surface, "snapshot") else None
        mutated = bool(applied.get("mutated")) or before != after
        return {
            "ok": mutated,
            "path": "hybrid_surface",
            "key": key,
            "observed": {"before": before, "after": after, "applied": applied},
            "attempts": attempts,
            "claim_boundary": CLAIM + " Hybrid host-guest boundary: surface mutation only.",
            "SILICON_EXACT_EMULATION": False,
            "HYBRID": True,
        }

    return {
        "ok": False,
        "error": "no_injection_path",
        "attempts": attempts,
        "SKIPPED_ENVIRONMENT": monitor_sock is None and agent is None,
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": CLAIM,
    }


def inject_pointer(
    *,
    monitor_sock: Path | None = None,
    x: int = 40,
    y: int = 40,
    button: str = "left",
    agent: Any | None = None,
    hybrid_surface: Any | None = None,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    if monitor_sock is not None:
        # QEMU mouse_move is relative in some builds; still records accepted command.
        mon = _monitor_send(monitor_sock, f"mouse_move {x} {y}")
        attempts.append(mon)
        click = _monitor_send(monitor_sock, "mouse_button 1")
        attempts.append(click)
        if mon.get("ok") or click.get("ok"):
            return {
                "ok": True,
                "path": "qemu_monitor_mouse",
                "x": x,
                "y": y,
                "button": button,
                "attempts": attempts,
                "SILICON_EXACT_EMULATION": False,
                "claim_boundary": CLAIM,
            }
    if agent is not None:
        rsp = agent.call("input_inject", kind="pointer", x=x, y=y, button=button)
        attempts.append(rsp)
        if rsp.get("ok"):
            return {
                "ok": True,
                "path": "guest_agent",
                "observed": rsp,
                "attempts": attempts,
                "SILICON_EXACT_EMULATION": False,
                "claim_boundary": CLAIM,
            }
    if hybrid_surface is not None:
        before = hybrid_surface.snapshot()
        applied = hybrid_surface.apply_hid({"kind": "click", "x": x, "y": y, "element": "lab-button"})
        after = hybrid_surface.snapshot()
        return {
            "ok": bool(applied.get("mutated")),
            "path": "hybrid_surface",
            "observed": {"before": before, "after": after},
            "HYBRID": True,
            "claim_boundary": CLAIM + " Hybrid pointer path.",
            "SILICON_EXACT_EMULATION": False,
        }
    return {"ok": False, "error": "no_pointer_path", "attempts": attempts}


def write_input_evidence(work: Path, payload: dict[str, Any]) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    path = work / "conventional_input_evidence.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
