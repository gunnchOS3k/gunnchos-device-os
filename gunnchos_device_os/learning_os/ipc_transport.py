"""IPC transport interface + file and deterministic test implementations."""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .ipc_protocol import (
    MESSAGE_ACK,
    PROTOCOL_ID,
    build_ack,
    build_nack,
    validate_request,
)


class IpcTransport(ABC):
    """Send launch context and wait for acknowledgement."""

    @abstractmethod
    def send_and_await_ack(
        self,
        request: dict[str, Any],
        *,
        timeout_s: float = 5.0,
    ) -> dict[str, Any]:
        raise NotImplementedError


class FileIpcTransport(IpcTransport):
    """Production/native file-drop transport.

    Layout under ipc_dir:
      request-<id>.json  — Device OS writes
      ack-<id>.json      — Learning OS writes
    """

    def __init__(self, ipc_dir: Path, *, receiver_present: bool = True):
        self.ipc_dir = Path(ipc_dir)
        self.ipc_dir.mkdir(parents=True, exist_ok=True)
        self.receiver_present = receiver_present
        self._seen_request_ids: set[str] = set()

    def send_and_await_ack(
        self,
        request: dict[str, Any],
        *,
        timeout_s: float = 5.0,
    ) -> dict[str, Any]:
        ok, reason = validate_request(request)
        if not ok:
            return {"ok": False, "reason": reason or "bad_payload", "ack": None}

        request_id = str(request["request_id"])
        if request_id in self._seen_request_ids:
            # Idempotent safe replay: return prior-style ack without re-delivery side effects.
            return {
                "ok": True,
                "reason": "idempotent_replay",
                "ack": build_ack(request_id=request_id, status="ok_replay"),
                "replay": True,
            }
        self._seen_request_ids.add(request_id)

        if not self.receiver_present:
            return {"ok": False, "reason": "missing_receiver", "ack": None}

        req_path = self.ipc_dir / f"request-{request_id}.json"
        ack_path = self.ipc_dir / f"ack-{request_id}.json"
        req_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if ack_path.is_file():
                try:
                    ack = json.loads(ack_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    return {"ok": False, "reason": "bad_ack_payload", "ack": None}
                if ack.get("protocol") != PROTOCOL_ID:
                    return {"ok": False, "reason": "wrong_protocol_version", "ack": ack}
                if ack.get("message_type") != MESSAGE_ACK:
                    return {"ok": False, "reason": "nack_or_bad_message", "ack": ack}
                if ack.get("request_id") != request_id:
                    return {"ok": False, "reason": "ack_request_id_mismatch", "ack": ack}
                return {"ok": True, "reason": None, "ack": ack, "replay": False}
            time.sleep(0.02)
        return {"ok": False, "reason": "timeout", "ack": None}


class DeterministicTestTransport(IpcTransport):
    """In-memory transport for unit tests — optional auto-ack / fault injection."""

    def __init__(
        self,
        *,
        auto_ack: bool = True,
        fail_reason: str | None = None,
        app_version: str = "0.1.0-fixture",
        latency_s: float = 0.0,
    ):
        self.auto_ack = auto_ack
        self.fail_reason = fail_reason
        self.app_version = app_version
        self.latency_s = latency_s
        self.sent: list[dict[str, Any]] = []
        self._seen: set[str] = set()

    def send_and_await_ack(
        self,
        request: dict[str, Any],
        *,
        timeout_s: float = 5.0,
    ) -> dict[str, Any]:
        ok, reason = validate_request(request)
        if not ok:
            return {"ok": False, "reason": reason or "bad_payload", "ack": None}

        request_id = str(request["request_id"])
        self.sent.append(request)
        if request_id in self._seen:
            return {
                "ok": True,
                "reason": "idempotent_replay",
                "ack": build_ack(request_id=request_id, status="ok_replay"),
                "replay": True,
            }
        self._seen.add(request_id)

        if self.fail_reason:
            if self.fail_reason == "timeout":
                # Simulate timeout without sleeping the full timeout in tests.
                return {"ok": False, "reason": "timeout", "ack": None}
            if self.fail_reason == "missing_receiver":
                return {"ok": False, "reason": "missing_receiver", "ack": None}
            return {
                "ok": False,
                "reason": self.fail_reason,
                "ack": build_nack(request_id=request_id, reason=self.fail_reason),
            }

        if self.latency_s > timeout_s:
            return {"ok": False, "reason": "timeout", "ack": None}
        if self.latency_s:
            time.sleep(self.latency_s)

        if not self.auto_ack:
            return {"ok": False, "reason": "timeout", "ack": None}

        return {
            "ok": True,
            "reason": None,
            "ack": build_ack(request_id=request_id, status="ok", app_version=self.app_version),
            "replay": False,
        }
