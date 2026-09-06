"""IPC protocol schema for Device OS ↔ Learning OS companion transport."""
from __future__ import annotations

from typing import Any, Final

PROTOCOL_ID: Final = "gunnchos.learning_os.ipc.v1"
PROTOCOL_MAJOR: Final = 1

MESSAGE_LAUNCH_CONTEXT = "launch_context"
MESSAGE_ACK = "ack"
MESSAGE_NACK = "nack"

ALLOWED_CONTEXT_KEYS = frozenset(
    {
        "profile",
        "mode",
        "device_role",
        "platform_role",
        "shell_form_factor",
        "registry_id",
        "bundle_id",
        "sdk_app_id",
        "runtime_id",
        "course_id",
        "section_id",
        "activity_id",
        "sync_cursor",
        "revision",
    }
)

SECRET_CONTEXT_KEYS = frozenset(
    {
        "password",
        "passwords",
        "private_key",
        "private_keys",
        "session_token",
        "session_tokens",
        "db_key",
        "db_keys",
        "lti_private_key",
        "api_key",
        "secret",
        "bearer",
        "authorization",
        "auth",
        "jwt",
        "token",
        "answer_key",
        "WAIKE_DEV_DB_KEY",
    }
)


def validate_request(payload: dict[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(payload, dict):
        return False, "not_object"
    if payload.get("protocol") != PROTOCOL_ID:
        return False, "wrong_protocol_version"
    if payload.get("message_type") != MESSAGE_LAUNCH_CONTEXT:
        return False, "bad_message_type"
    if not payload.get("request_id"):
        return False, "missing_request_id"
    deep_link = payload.get("deep_link")
    if deep_link is not None and not isinstance(deep_link, dict):
        return False, "bad_deep_link"
    context = payload.get("context") or {}
    if not isinstance(context, dict):
        return False, "bad_context"
    for key in context:
        key_l = str(key).lower()
        if key not in ALLOWED_CONTEXT_KEYS:
            return False, f"unknown_context_field:{key}"
        if key_l in {s.lower() for s in SECRET_CONTEXT_KEYS}:
            return False, f"secret_context_field:{key}"
    return True, None


def build_launch_request(
    *,
    request_id: str,
    deep_link: dict[str, Any] | None,
    context: dict[str, Any],
    bundle_id: str,
) -> dict[str, Any]:
    clean_context = {k: v for k, v in context.items() if k in ALLOWED_CONTEXT_KEYS}
    return {
        "protocol": PROTOCOL_ID,
        "message_type": MESSAGE_LAUNCH_CONTEXT,
        "request_id": request_id,
        "bundle_id": bundle_id,
        "deep_link": deep_link,
        "context": clean_context,
    }


def build_ack(
    *,
    request_id: str,
    status: str = "ok",
    app_version: str | None = None,
    bundle_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "protocol": PROTOCOL_ID,
        "message_type": MESSAGE_ACK,
        "request_id": request_id,
        "status": status,
        "app_version": app_version,
    }
    if bundle_id:
        payload["bundle_id"] = bundle_id
    return payload


def validate_ack(
    ack: dict[str, Any],
    *,
    request_id: str,
    expected_bundle_id: str | None = None,
    expected_app_version: str | None = None,
) -> tuple[bool, str | None]:
    """Validate Learning OS ACK fields for production launch success."""
    if not isinstance(ack, dict):
        return False, "bad_ack_payload"
    if ack.get("protocol") != PROTOCOL_ID:
        return False, "wrong_protocol_version"
    if ack.get("message_type") != MESSAGE_ACK:
        return False, "nack_or_bad_message"
    if ack.get("request_id") != request_id:
        return False, "ack_request_id_mismatch"
    status = ack.get("status")
    if status not in ("ok", "ok_replay"):
        return False, f"ack_bad_status:{status}"
    if expected_bundle_id:
        got = ack.get("bundle_id")
        if got != expected_bundle_id:
            return False, "ack_bundle_mismatch"
    if expected_app_version:
        got_ver = ack.get("app_version")
        if got_ver is not None and got_ver != expected_app_version:
            return False, "ack_version_mismatch"
    return True, None


def build_nack(*, request_id: str, reason: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "message_type": MESSAGE_NACK,
        "request_id": request_id,
        "reason": reason,
    }
