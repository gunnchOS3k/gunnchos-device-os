"""3k MLV world-workspace launcher bridge.

MLV consumes gunnchOS identity. This module is the experience-layer
contract, not a security boundary for file bytes.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote_to_bytes
from uuid import UUID

MLV_APP_ID = "mlv_world_workspace"
MLV_APP_NAME = "My Little Vicinity"
DEEP_LINK_SCHEME = "gunnchos"
DEEP_LINK_HOST = "mlv"
ALLOWED_KINDS = frozenset({"home", "node", "public", "share"})
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,256}$")

# Journey posture — do not weaken youth / library / guardian rules.
RECOMMENDED_PRESETS = frozenset({"studio", "arcade", "workshop"})
AVAILABLE_PRESETS = frozenset({"car", "laboratory", "spaceship", "offline"})
POLICY_CONTROLLED_PRESETS = frozenset({"classroom", "guardian"})
PUBLIC_EPHEMERAL_PRESETS = frozenset({"library"})
SIMPLIFIED_PRESETS = frozenset({"scooter", "bicycle"})


def _reject(uri: str | None, reason: str) -> dict[str, Any]:
    return {
        "uri": uri,
        "valid": False,
        "reason": reason,
        "kind": None,
        "node_id": None,
        "token_present": False,
        "app_id": MLV_APP_ID,
    }


def _has_ambiguous_encoding(raw: str) -> bool:
    if "%" not in raw:
        return False
    i = 0
    while i < len(raw):
        if raw[i] != "%":
            i += 1
            continue
        if i + 2 >= len(raw):
            return True
        hexpart = raw[i + 1 : i + 3]
        if not re.fullmatch(r"[0-9A-Fa-f]{2}", hexpart):
            return True
        if hexpart.lower() == "25":
            return True
        i += 3
    return False


def _decode_once(segment: str) -> str | None:
    if _has_ambiguous_encoding(segment):
        return None
    try:
        raw_bytes = unquote_to_bytes(segment)
    except Exception:
        return None
    if b"\x00" in raw_bytes:
        return None
    try:
        decoded = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if any(ord(ch) < 32 for ch in decoded):
        return None
    return decoded


def parse_mlv_deep_link(uri: str | None) -> dict[str, Any]:
    """Parse gunnchos://mlv/... without logging share tokens."""
    if not uri:
        return _reject(uri, "empty")
    trimmed = uri.strip()
    if "\x00" in trimmed or "\\" in trimmed:
        return _reject(trimmed, "unsafe_chars")
    lower = trimmed.lower()
    prefix = f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}"
    if not lower.startswith(prefix):
        return _reject(trimmed, "scheme_or_host_rejected")
    rest = trimmed[len(prefix) :]
    if rest.startswith("/"):
        rest = rest[1:]
    parts = [p for p in rest.split("/") if p]
    if not parts:
        return _reject(trimmed, "kind_rejected")
    kind_decoded = _decode_once(parts[0])
    if kind_decoded is None:
        return _reject(trimmed, "encoding_rejected")
    kind = kind_decoded.lower()
    if kind not in ALLOWED_KINDS:
        return _reject(trimmed, "kind_rejected")
    if kind == "home":
        return {
            "uri": trimmed,
            "valid": True,
            "reason": None,
            "kind": kind,
            "node_id": None,
            "token_present": False,
            "app_id": MLV_APP_ID,
            "canonical": f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}/home",
        }
    if len(parts) < 2:
        return _reject(trimmed, "missing_value")
    value = _decode_once(parts[1])
    if value is None:
        return _reject(trimmed, "encoding_rejected")
    if kind in {"node", "public"}:
        if not UUID_RE.match(value):
            return _reject(trimmed, "uuid_rejected")
        UUID(value)
        return {
            "uri": trimmed,
            "valid": True,
            "reason": None,
            "kind": kind,
            "node_id": value,
            "token_present": False,
            "app_id": MLV_APP_ID,
            "canonical": f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}/{kind}/{value}",
        }
    if not TOKEN_RE.match(value):
        return _reject(trimmed, "token_rejected")
    return {
        "uri": trimmed,
        "valid": True,
        "reason": None,
        "kind": "share",
        "node_id": None,
        "token_present": True,
        "app_id": MLV_APP_ID,
        "canonical": f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}/share",
    }


def journey_preset_access(preset: str) -> dict[str, Any]:
    preset_id = (preset or "").strip().lower()
    if preset_id in RECOMMENDED_PRESETS:
        return {"preset": preset_id, "allowed": True, "posture": "recommended"}
    if preset_id in AVAILABLE_PRESETS:
        note = "cached owner subset only" if preset_id == "offline" else "available"
        return {"preset": preset_id, "allowed": True, "posture": note}
    if preset_id in PUBLIC_EPHEMERAL_PRESETS:
        return {
            "preset": preset_id,
            "allowed": True,
            "posture": "public_ephemeral_guest",
            "private_nodes": False,
        }
    if preset_id in POLICY_CONTROLLED_PRESETS:
        return {"preset": preset_id, "allowed": False, "posture": "policy_controlled"}
    if preset_id in SIMPLIFIED_PRESETS:
        return {"preset": preset_id, "allowed": False, "posture": "simplified_path_omitted"}
    return {"preset": preset_id, "allowed": False, "posture": "unknown"}


def open_home() -> dict[str, Any]:
    return {
        "ok": True,
        "app_id": MLV_APP_ID,
        "app_name": MLV_APP_NAME,
        "route": "gunnchos://mlv/home",
        "action": "open_home",
    }


def open_node(node_id: str) -> dict[str, Any]:
    parsed = parse_mlv_deep_link(f"gunnchos://mlv/node/{node_id}")
    if not parsed["valid"]:
        return {"ok": False, "reason": parsed["reason"], "app_id": MLV_APP_ID}
    return {"ok": True, "app_id": MLV_APP_ID, "route": parsed["canonical"], "action": "open_node", "node_id": node_id}


def open_public_node(node_id: str) -> dict[str, Any]:
    parsed = parse_mlv_deep_link(f"gunnchos://mlv/public/{node_id}")
    if not parsed["valid"]:
        return {"ok": False, "reason": parsed["reason"], "app_id": MLV_APP_ID}
    return {
        "ok": True,
        "app_id": MLV_APP_ID,
        "route": parsed["canonical"],
        "action": "open_public_node",
        "node_id": node_id,
    }


def open_share(token: str) -> dict[str, Any]:
    parsed = parse_mlv_deep_link(f"gunnchos://mlv/share/{token}")
    if not parsed["valid"]:
        return {"ok": False, "reason": parsed["reason"], "app_id": MLV_APP_ID, "token_present": False}
    return {
        "ok": True,
        "app_id": MLV_APP_ID,
        "route": "gunnchos://mlv/share",
        "action": "open_share",
        "token_present": True,
    }


def launch_app_for_node(node: dict[str, Any]) -> dict[str, Any]:
    mime = str(node.get("mime_type") or "")
    visibility = str(node.get("visibility") or "private")
    if visibility != "public" and not node.get("owner_authorized"):
        return {"ok": False, "reason": "not_authorized", "app_id": MLV_APP_ID}
    app = "mlv_safe_viewer"
    if mime.startswith("text/") or "json" in mime:
        app = "notes"
    elif mime == "application/pdf":
        app = "files"
    return {
        "ok": True,
        "app_id": MLV_APP_ID,
        "launch_app": app,
        "visibility": visibility,
        "default_visibility_honored": True,
    }


def get_recent_nodes() -> list[dict[str, Any]]:
    """Prototype: no cloud recents until the owner session is wired."""
    return []


def ingest_artifact_intent(intent: dict[str, Any]) -> dict[str, Any]:
    if intent.get("default_visibility") != "private":
        return {"ok": False, "reason": "public_default_forbidden"}
    required = ("artifact_id", "owner_id", "title", "mime_type", "app_id")
    missing = [k for k in required if not intent.get(k)]
    if missing:
        return {"ok": False, "reason": "missing_fields", "fields": missing}
    return {
        "ok": True,
        "visibility": "private",
        "placement_room": "home.desk",
        "node_kind": "file",
        "app_id": MLV_APP_ID,
    }
